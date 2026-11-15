"""Computes spend, conversions, attributed revenue, CPA and ROAS from an ad report CSV.

    py -3 -I ad_metrics.py report.csv --spend "Spend" --conversions "Conversions" --currency EUR --decimal "," \
        --currency-column "Currency" --no-attribution-column
    py -3 -I ad_metrics.py report.csv ... --revenue "Revenue" --name "Campaign" --period "October 2026" --json

A currency column and an attribution column are each either named or explicitly declared absent
(--no-currency-column, --no-attribution-column), so a mixed file is never summed by omission.

Column names and the number format come only from flags; nothing is guessed. Input that cannot be read
exactly ends the run with exit code 2, a line-numbered message on stderr and no table. Line numbers are
lines of the file (the header is line 1). The tool reads the given CSV and prints; it writes nothing.
It produces no threshold, significance, winner or recommendation.
"""
import argparse
import csv
import io
import json
import re
import sys
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

sys.dont_write_bytecode = True

EXIT_REJECTED = 2
ENCODINGS = ("utf-8-sig", "cp1254")
DELIMITERS = {";": ";", ",": ",", "tab": "\t"}
DECIMAL_SEPARATORS = (",", ".")
TOTAL_LABELS = ("toplam", "genel toplam", "total", "grand total", "totals")
NOT_COMPUTABLE = "not computable"
NO_REVENUE = "no revenue column"
NO_PERIOD = "period not given"
PANEL_NOTE = "Not checked against the ad platform: compare these totals with the totals in your ad platform."
SAMPLE_NOTE = "Sample size was not assessed; this tool does not declare a winner."
UNLABELED_TOTALS_NOTE = ("Unlabeled total rows and higher-level rows (campaign, ad set) are not removed; "
                         "if the file has any, the totals are counted twice.")
DISPLAY_STEP = Decimal("0.01")
SWAP_SEPARATORS = str.maketrans(",.", ".,")
REQUIRED_FLAGS = (("spend", "--spend"), ("conversions", "--conversions"),
                  ("currency", "--currency"), ("decimal", "--decimal"))
# A column check the user must either ask for or explicitly waive: (column attribute, flag, waiver attribute, flag).
DECLARED_COLUMNS = (("currency_column", "--currency-column", "no_currency_column", "--no-currency-column"),
                    ("attribution_column", "--attribution-column", "no_attribution_column", "--no-attribution-column"))


class Rejected(Exception):
    """Input the tool will not compute from; each message becomes one stderr line."""

    def __init__(self, *messages):
        super().__init__(*messages)
        self.messages = list(messages)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Rejected(f"error: flag error: {message}")


@dataclass(frozen=True)
class Columns:
    spend: int
    conversions: int
    revenue: int | None
    name: int
    ident: int | None
    currency: int | None
    attribution: int | None


@dataclass(frozen=True)
class Line:
    number: int
    name: str
    ident: str | None
    spend: Decimal
    conversions: int
    revenue: Decimal | None


@dataclass(frozen=True)
class Report:
    lines: list
    warnings: list
    headers: dict
    currency: str
    period: str
    decimal_sep: str
    has_revenue: bool


# --- numbers --------------------------------------------------------------------------------------

def thousands_for(decimal_sep):
    return "." if decimal_sep == "," else ","


def number_pattern(decimal_sep):
    group = re.escape(thousands_for(decimal_sep))
    integer = rf"(?:[0-9]{{1,3}}(?:{group}[0-9]{{3}})+|[0-9]+)"
    return re.compile(rf"{integer}(?:{re.escape(decimal_sep)}[0-9]+)?")


NUMBER_PATTERNS = {sep: number_pattern(sep) for sep in DECIMAL_SEPARATORS}


def parse_amount(text, decimal_sep):
    """A non-negative number in the declared format: '2.000,50' with ',' is 2000.50. Nothing is stripped."""
    pattern = NUMBER_PATTERNS[decimal_sep]
    thousands = thousands_for(decimal_sep)
    if text == "":
        raise ValueError("empty cell")
    if text.startswith("-") and pattern.fullmatch(text[1:]):
        raise ValueError(f"negative value \"{printable(text)}\"")
    if not pattern.fullmatch(text):
        raise ValueError(f"\"{printable(text)}\" is not a number in the declared format "
                         f"(decimal separator \"{decimal_sep}\", thousands separator \"{thousands}\")")
    return Decimal(text.replace(thousands, "").replace(decimal_sep, "."))


def parse_count(text, decimal_sep):
    value = parse_amount(text, decimal_sep)
    if decimal_sep in text:
        raise ValueError(f"\"{printable(text)}\" must be a whole number")
    return int(value)


def ratio(numerator, denominator):
    return NOT_COMPUTABLE if denominator == 0 else numerator / denominator


# --- labels and text ------------------------------------------------------------------------------

def fold(text):
    """Lowercase that ignores case and the Turkish dotted/dotless i (I, İ, ı, i are one letter)."""
    return text.strip().replace("İ", "i").replace("I", "i").replace("ı", "i").lower()


TOTAL_KEYS = frozenset(fold(label) for label in TOTAL_LABELS)


def is_total_label(text):
    return fold(text) in TOTAL_KEYS


def printable(text):
    """Keeps control characters from the file out of the terminal."""
    return "".join(ch if ch.isprintable() else "?" for ch in text)


def line_list(numbers):
    return ", ".join(f"line {n}" for n in numbers)


# --- reading --------------------------------------------------------------------------------------

def read_text(path):
    """UTF-8 (with or without BOM), else Windows Turkish (cp1254)."""
    try:
        raw = Path(path).read_bytes()
    except OSError as error:
        raise Rejected(f"error: cannot read {path}: {error.strerror or error}") from error
    for encoding in ENCODINGS:
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise Rejected(f"error: {path} is not UTF-8 or Windows-1254 (cp1254) text")


def choose_delimiter(text, flag):
    if flag:
        return DELIMITERS[flag]
    header = text.splitlines()[0]
    found = [name for name, char in DELIMITERS.items() if char in header]
    if len(found) != 1:
        seen = ", ".join(f"\"{name}\"" for name in found) or "none"
        raise Rejected(f"error: line 1: the delimiter in the header is ambiguous (found: {seen}); "
                       "give --delimiter \";\", \",\" or \"tab\"")
    return DELIMITERS[found[0]]


def read_table(text, delimiter):
    """Returns the header and (line number, cells) pairs; blank lines are skipped."""
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter, strict=True)
    try:
        header = next(reader)
        rows = [(reader.line_num, cells) for cells in reader if cells]
    except csv.Error as error:
        raise Rejected(f"error: line {reader.line_num}: cannot read the CSV structure ({error})") from error
    return header, rows


def column_index(header, flag, name, errors):
    count = header.count(name)
    if count == 1:
        return header.index(name)
    problem = "is not in the header" if count == 0 else f"appears {count} times in the header"
    errors.append(f"error: line 1: {flag} column \"{printable(name)}\" {problem}")
    return None


def resolve_columns(header, args):
    errors = []

    def optional(flag, name):
        return None if name is None else column_index(header, flag, name, errors)

    columns = Columns(
        spend=column_index(header, "--spend", args.spend, errors),
        conversions=column_index(header, "--conversions", args.conversions, errors),
        revenue=optional("--revenue", args.revenue),
        name=0 if args.name is None else column_index(header, "--name", args.name, errors),
        ident=optional("--id", args.id),
        currency=optional("--currency-column", args.currency_column),
        attribution=optional("--attribution-column", args.attribution_column),
    )
    if errors:
        raise Rejected(*errors)
    return columns


# --- checks ---------------------------------------------------------------------------------------

def check_widths(header, rows):
    errors = [f"error: line {number}: has {len(cells)} cells, the header has {len(header)} columns"
              for number, cells in rows if len(cells) != len(header)]
    if errors:
        raise Rejected(*errors)


def first_line_per_value(rows, index):
    seen = {}
    for number, cells in rows:
        seen.setdefault(cells[index], number)
    return seen


def describe_values(seen):
    return ", ".join(f"\"{printable(value)}\" (line {number})" for value, number in seen.items())


def check_currency(rows, index, flag_name, currency):
    seen = first_line_per_value(rows, index)
    if len(seen) > 1:
        return [f"error: --currency-column \"{flag_name}\" holds more than one value: {describe_values(seen)}"]
    if currency not in seen:
        return [f"error: --currency-column \"{flag_name}\" holds {describe_values(seen)}, "
                f"which is not --currency \"{printable(currency)}\""]
    return []


def check_attribution(rows, index, flag_name):
    seen = first_line_per_value(rows, index)
    if len(seen) > 1:
        return [f"error: --attribution-column \"{flag_name}\" holds more than one value: {describe_values(seen)}"]
    return []


def repeated_groups(rows, key):
    groups = {}
    for number, cells in rows:
        groups.setdefault(key(cells), []).append(number)
    return {value: numbers for value, numbers in groups.items() if len(numbers) > 1}


def check_ids(rows, index):
    return [f"error: --id \"{printable(value)}\" is on more than one line: {line_list(numbers)}"
            for value, numbers in repeated_groups(rows, lambda cells: cells[index]).items()]


def identical_lines(rows):
    groups = repeated_groups(rows, tuple)
    return sorted(number for numbers in groups.values() for number in numbers)


def parse_line(number, cells, columns, header, decimal_sep, errors):
    def cell(index, parser):
        try:
            return parser(cells[index], decimal_sep)
        except ValueError as error:
            errors.append(f"error: line {number}, column \"{printable(header[index])}\": {error}")
            return None

    return Line(
        number=number,
        name=cells[columns.name],
        ident=None if columns.ident is None else cells[columns.ident],
        spend=cell(columns.spend, parse_amount),
        conversions=cell(columns.conversions, parse_count),
        revenue=None if columns.revenue is None else cell(columns.revenue, parse_amount),
    )


# --- building the report --------------------------------------------------------------------------

def split_total_rows(rows, name_index):
    """Runs before the width check, so a short 'Total' row is skipped instead of failing the file."""
    data, totals = [], []
    for number, cells in rows:
        is_total = len(cells) > name_index and is_total_label(cells[name_index])
        (totals if is_total else data).append((number, cells))
    return data, totals


def total_row_warning(totals, name_index):
    found = ", ".join(f"line {number} (\"{printable(cells[name_index].strip())}\")" for number, cells in totals)
    return (f"Total row left out of the calculation: {found}. The list of total labels is limited "
            f"({', '.join(TOTAL_LABELS)}); total rows labeled any other way are not removed.")


def consistency_errors(data, columns, header, args):
    errors = []
    if columns.currency is not None:
        errors += check_currency(data, columns.currency, printable(header[columns.currency]), args.currency)
    if columns.attribution is not None:
        errors += check_attribution(data, columns.attribution, printable(header[columns.attribution]))
    if columns.ident is not None:
        errors += check_ids(data, columns.ident)
    return errors


def duplicate_warning(data, columns, count_duplicates):
    """Without an id column, identical rows are refused unless the user says to count them."""
    if columns.ident is not None:
        return None
    lines = identical_lines(data)
    if not lines:
        return None
    if not count_duplicates:
        raise Rejected(f"error: {len(lines)} identical lines ({line_list(lines)}); "
                       "give --count-duplicates if they are to be counted as separate lines")
    return f"{len(lines)} identical lines counted (--count-duplicates): {line_list(lines)}."


def build_report(args):
    text = read_text(args.report)
    if not text.strip():
        raise Rejected(f"error: {args.report} is empty")
    header, rows = read_table(text, choose_delimiter(text, args.delimiter))
    columns = resolve_columns(header, args)
    data, totals = split_total_rows(rows, columns.name)
    check_widths(header, data)
    if not data:
        raise Rejected(f"error: {args.report} has no data lines")
    errors = consistency_errors(data, columns, header, args)
    if errors:
        raise Rejected(*errors)
    warnings = [UNLABELED_TOTALS_NOTE]
    warnings += [total_row_warning(totals, columns.name)] if totals else []
    duplicates = duplicate_warning(data, columns, args.count_duplicates)
    warnings += [duplicates] if duplicates else []
    lines = [parse_line(number, cells, columns, header, args.decimal, errors) for number, cells in data]
    if errors:
        raise Rejected(*errors)
    if columns.revenue is None:
        warnings.append(f"{NO_REVENUE}: --revenue was not given, so no revenue-based ratio was computed.")
    headers = {"name": header[columns.name], "ident": None if columns.ident is None else header[columns.ident]}
    return Report(lines=lines, warnings=warnings, headers=headers, currency=args.currency,
                  period=args.period or "", decimal_sep=args.decimal, has_revenue=columns.revenue is not None)


# --- output ---------------------------------------------------------------------------------------

def figures(spend, conversions, revenue, has_revenue):
    return {
        "spend": spend,
        "conversions": conversions,
        "revenue": revenue,
        "cpa": ratio(spend, conversions),
        "roas": ratio(revenue, spend) if has_revenue else NO_REVENUE,
    }


def row_figures(line, has_revenue):
    return figures(line.spend, line.conversions, line.revenue, has_revenue)


def total_figures(report):
    revenue = sum(line.revenue for line in report.lines) if report.has_revenue else None
    return figures(sum(line.spend for line in report.lines), sum(line.conversions for line in report.lines),
                   revenue, report.has_revenue)


def footer(report):
    period = f"Period: {printable(report.period)}" if report.period else NO_PERIOD
    return [f"Currency: {printable(report.currency)} · {period}", PANEL_NOTE, SAMPLE_NOTE]


def exact(value):
    return value if value is None or isinstance(value, str) else str(value)


def render_json(report):
    def entry(values):
        return {key: exact(value) for key, value in values.items()}

    rows = [{"line": line.number, "name": line.name, "id": line.ident, **entry(row_figures(line, report.has_revenue))}
            for line in report.lines]
    result = {"currency": report.currency, "period": report.period or None, "rows": rows,
              "total": entry(total_figures(report)), "warnings": report.warnings, "notes": footer(report)}
    return json.dumps(result, ensure_ascii=False, indent=1)


def shown(value, decimal_sep):
    """Display only: two places, half up, in the file's own decimal format."""
    if isinstance(value, str):
        return value
    if isinstance(value, int):
        text = f"{value:,}"
    else:
        text = f"{value.quantize(DISPLAY_STEP, rounding=ROUND_HALF_UP):,.2f}"
    return text if decimal_sep == "." else text.translate(SWAP_SEPARATORS)


def table_layout(report):
    currency = printable(report.currency)
    labels = [("Line", None), (printable(report.headers["name"]), None)]
    if report.headers["ident"] is not None:
        labels.append((printable(report.headers["ident"]), None))
    labels += [(f"Spend ({currency})", "spend"), ("Conversions", "conversions")]
    if report.has_revenue:
        labels.append((f"Revenue ({currency})", "revenue"))
    labels.append((f"CPA ({currency})", "cpa"))
    if report.has_revenue:
        labels.append(("ROAS", "roas"))
    return labels


def table_rows(report, labels):
    numeric = [key for _, key in labels if key]
    label_count = len(labels) - len(numeric)
    rows = []
    for line in report.lines:
        values = row_figures(line, report.has_revenue)
        text = [str(line.number), printable(line.name)] + ([printable(line.ident)] if line.ident is not None else [])
        rows.append(text + [shown(values[key], report.decimal_sep) for key in numeric])
    totals = total_figures(report)
    rows.append(["Total"] + [""] * (label_count - 1) + [shown(totals[key], report.decimal_sep) for key in numeric])
    return rows, label_count


def render_table(labels, rows, label_count):
    heads = [label for label, _ in labels]
    widths = [max(len(row[i]) for row in [heads, *rows]) for i in range(len(heads))]

    def fit(cells):
        return "  ".join(cell.ljust(w) if i < label_count else cell.rjust(w)
                         for i, (cell, w) in enumerate(zip(cells, widths))).rstrip()

    return [fit(heads), *(fit(row) for row in rows)]


def render_text(report):
    labels = table_layout(report)
    rows, label_count = table_rows(report, labels)
    out = render_table(labels, rows, label_count)
    if report.warnings:
        out += ["", "Warnings"] + [f"- {printable(w)}" for w in report.warnings]
    return "\n".join(out + [""] + footer(report))


# --- command line ---------------------------------------------------------------------------------

def parse_args(argv):
    parser = Parser(description="Spend, conversions, revenue, CPA and ROAS table from an ad report CSV.")
    parser.add_argument("report", help="CSV file")
    parser.add_argument("--spend", help="name of the spend column (required)")
    parser.add_argument("--conversions", help="name of the conversions column (required)")
    parser.add_argument("--currency", help="currency of the report, e.g. EUR (required)")
    parser.add_argument("--decimal", choices=DECIMAL_SEPARATORS, help="decimal separator (required)")
    parser.add_argument("--revenue", help="name of the attributed revenue column")
    parser.add_argument("--name", help="column that names each line (default: the first column)")
    parser.add_argument("--id", help="id column that must be unique on every line")
    parser.add_argument("--currency-column", help="currency column that must hold a single value")
    parser.add_argument("--no-currency-column", action="store_true", help="the file has no currency column")
    parser.add_argument("--attribution-column", help="attribution window column that must hold a single value")
    parser.add_argument("--no-attribution-column", action="store_true",
                        help="the file has no attribution window column")
    parser.add_argument("--period", help="period of the report (free text)")
    parser.add_argument("--delimiter", choices=tuple(DELIMITERS), help="CSV delimiter")
    parser.add_argument("--count-duplicates", action="store_true", help="count identical lines separately")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    missing = [flag for attribute, flag in REQUIRED_FLAGS if getattr(args, attribute) is None]
    errors = [f"error: required flag missing: {', '.join(missing)}"] if missing else []
    errors += declaration_errors(args)
    if errors:
        raise Rejected(*errors)
    return args


def declaration_errors(args):
    errors = []
    for column, column_flag, waiver, waiver_flag in DECLARED_COLUMNS:
        given, waived = getattr(args, column) is not None, getattr(args, waiver)
        if given and waived:
            errors.append(f"error: {column_flag} and {waiver_flag} cannot be given together; give only one")
        elif not given and not waived:
            errors.append(f"error: give {column_flag} \"<column>\", or if the file has no such column, "
                          f"say so with {waiver_flag}")
    return errors


def main(argv=None):
    try:
        args = parse_args(argv)
        report = build_report(args)
    except Rejected as rejection:
        for message in rejection.messages:
            print(message, file=sys.stderr)
        return EXIT_REJECTED
    print(render_json(report) if args.json else render_text(report))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
