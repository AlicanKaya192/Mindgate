"""Tests for ad_metrics.py: number parsing, rejections, warnings, totals and the output footer.

Run: python -I -B ad_metrics_test.py
No network. Temporary files go to the system temp folder and are removed by tempfile.
"""
import io
import json
import re
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "test_data"
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))
import ad_metrics  # noqa: E402

CORE = ["--spend", "Spend", "--conversions", "Conversions", "--currency", "EUR", "--decimal", ","]
NO_CURRENCY_COLUMN = ["--no-currency-column"]
NO_ATTRIBUTION_COLUMN = ["--no-attribution-column"]
BASE = CORE + NO_CURRENCY_COLUMN + NO_ATTRIBUTION_COLUMN
WITH_REVENUE = BASE + ["--revenue", "Revenue"]
CURRENCY_COLUMN = CORE + ["--revenue", "Revenue", "--currency-column", "Currency"] + NO_ATTRIBUTION_COLUMN
ATTRIBUTION_COLUMN = CORE + NO_CURRENCY_COLUMN + ["--attribution-column", "Attribution"]
PANEL_NOTE = "Not checked against the ad platform: compare these totals with the totals in your ad platform."
SAMPLE_NOTE = "Sample size was not assessed; this tool does not declare a winner."
UNLABELED_TOTALS_NOTE = ("Unlabeled total rows and higher-level rows (campaign, ad set) are not removed; "
                         "if the file has any, the totals are counted twice.")


def run(path, *flags):
    """Runs the tool in-process; returns (exit code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = ad_metrics.main([str(path), *flags])
    return code, out.getvalue(), err.getvalue()


def run_json(path, *flags):
    code, out, err = run(path, *flags, "--json")
    if code != 0:
        raise AssertionError(f"exit {code}: {err}")
    return json.loads(out)


class TempCsv:
    """Writes CSV text (or bytes) to a temporary file for one test."""

    def __init__(self, content, encoding="utf-8"):
        self.content = content if isinstance(content, bytes) else content.encode(encoding)

    def __enter__(self):
        self.folder = tempfile.TemporaryDirectory()
        path = Path(self.folder.name) / "report.csv"
        path.write_bytes(self.content)
        return path

    def __exit__(self, *exc):
        self.folder.cleanup()


class NumberParsingTest(unittest.TestCase):
    def test_comma_decimal_reads_dot_as_thousands(self):
        self.assertEqual(ad_metrics.parse_amount("2.000,50", ","), Decimal("2000.50"))

    def test_dot_decimal_reads_comma_as_thousands(self):
        self.assertEqual(ad_metrics.parse_amount("2,000.50", "."), Decimal("2000.50"))

    def test_plain_numbers_without_thousands(self):
        self.assertEqual(ad_metrics.parse_amount("1000,5", ","), Decimal("1000.5"))
        self.assertEqual(ad_metrics.parse_amount("0", ","), Decimal("0"))

    def test_other_format_is_rejected(self):
        with self.assertRaises(ValueError):
            ad_metrics.parse_amount("2,000.50", ",")

    def test_thousands_group_must_have_three_digits(self):
        for text in ("2.00,50", "20.00", "1.0000", ".500"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                ad_metrics.parse_amount(text, ",")

    def test_two_decimal_separators_are_rejected(self):
        with self.assertRaises(ValueError):
            ad_metrics.parse_amount("1,2,3", ",")

    def test_currency_symbols_and_spaces_are_not_stripped(self):
        for text in ("₺100", "100 TL", " 100", "100 ", "1 000", "$5"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                ad_metrics.parse_amount(text, ",")

    def test_empty_and_dashes_are_not_numbers(self):
        for text in ("", "—", "-", "–"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                ad_metrics.parse_amount(text, ",")

    def test_negative_is_rejected_by_name(self):
        with self.assertRaisesRegex(ValueError, "negative"):
            ad_metrics.parse_amount("-5,00", ",")

    def test_conversion_must_be_a_whole_number(self):
        self.assertEqual(ad_metrics.parse_count("1.000", ","), 1000)
        for text in ("2,5", "3,0"):
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, "whole number"):
                ad_metrics.parse_count(text, ",")


class TotalLabelTest(unittest.TestCase):
    def test_labels_match_without_case_or_turkish_i(self):
        for text in ("Toplam", "TOPLAM", "genel toplam", "GENEL TOPLAM", "Total", "Grand Total", "TOTALS", " Toplam "):
            with self.subTest(text=text):
                self.assertTrue(ad_metrics.is_total_label(text))

    def test_other_labels_do_not_match(self):
        for text in ("Total A", "Subtotal", "Ara toplam", "Sample A", ""):
            with self.subTest(text=text):
                self.assertFalse(ad_metrics.is_total_label(text))


class RatioTest(unittest.TestCase):
    def test_zero_conversions_cpa_cannot_be_computed(self):
        code, out, _ = run(DATA / "zeros.csv", *WITH_REVENUE)
        self.assertEqual(code, 0)
        result = run_json(DATA / "zeros.csv", *WITH_REVENUE)
        self.assertEqual(result["rows"][1]["cpa"], "not computable")
        self.assertIn("not computable", out)

    def test_zero_spend_roas_cannot_be_computed(self):
        result = run_json(DATA / "zeros.csv", *WITH_REVENUE)
        self.assertEqual(result["rows"][0]["roas"], "not computable")
        self.assertEqual(result["rows"][0]["cpa"], "0")

    def test_all_zero_totals_cannot_be_computed(self):
        with TempCsv("Campaign;Spend;Conversions;Revenue\nSample A;0;0;0\n") as path:
            result = run_json(path, *WITH_REVENUE)
        self.assertEqual(result["total"]["cpa"], "not computable")
        self.assertEqual(result["total"]["roas"], "not computable")

    def test_without_revenue_cpa_is_computed_and_roas_says_no_revenue(self):
        code, out, _ = run(DATA / "ratios.csv", *BASE)
        self.assertEqual(code, 0)
        result = run_json(DATA / "ratios.csv", *BASE)
        self.assertEqual(Decimal(result["total"]["cpa"]), Decimal("100"))
        self.assertEqual(result["total"]["roas"], "no revenue column")
        self.assertIn("no revenue column", out.split("Warnings", 1)[1])
        self.assertNotIn("ROAS", out)

    def test_total_roas_is_ratio_of_totals_not_mean_of_rows(self):
        result = run_json(DATA / "ratios.csv", *WITH_REVENUE)
        row_roas = [Decimal(r["roas"]) for r in result["rows"]]
        self.assertEqual(row_roas, [Decimal("2.5"), Decimal("2")])
        self.assertEqual(Decimal(result["total"]["roas"]), Decimal("850") / Decimal("400"))
        self.assertNotEqual(Decimal(result["total"]["roas"]), sum(row_roas) / 2)

    def test_total_cpa_is_ratio_of_totals_not_mean_of_rows(self):
        with TempCsv("Campaign;Spend;Conversions\nSample A;100;1\nSample B;300;6\n") as path:
            result = run_json(path, *BASE)
        self.assertEqual(result["total"]["cpa"], str(Decimal("400") / Decimal("7")))
        self.assertNotEqual(Decimal(result["total"]["cpa"]), Decimal("75"))

    def test_display_rounds_half_up_to_two_places(self):
        with TempCsv("Campaign;Spend;Conversions\nSample A;1;8\n") as path:
            code, out, _ = run(path, *BASE)
            result = run_json(path, *BASE)
        self.assertEqual(code, 0)
        self.assertEqual(result["rows"][0]["cpa"], "0.125")
        self.assertIn("0,13", out)


class NumberFormatCliTest(unittest.TestCase):
    def test_dot_thousands_under_comma_decimal(self):
        with TempCsv("Campaign;Spend;Conversions\nSample A;2.000,50;1\n") as path:
            result = run_json(path, *BASE)
        self.assertEqual(Decimal(result["rows"][0]["spend"]), Decimal("2000.50"))

    def test_comma_thousands_under_comma_decimal_is_rejected(self):
        with TempCsv("Campaign;Spend;Conversions\nSample A;2,000.50;1\n") as path:
            code, out, err = run(path, *BASE)
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("line 2", err)

    def test_dot_decimal_flag_with_comma_delimiter(self):
        text = 'Campaign,Spend,Conversions\nSample A,"2,000.50",1\n'
        flags = list(BASE)
        flags[flags.index(",")] = "."
        with TempCsv(text) as path:
            result = run_json(path, *flags)
        self.assertEqual(Decimal(result["rows"][0]["spend"]), Decimal("2000.50"))


class RejectionTest(unittest.TestCase):
    def assertRejected(self, code, out, err, *expected):
        self.assertEqual(code, 2)
        self.assertEqual(out, "", "a rejection prints no table")
        for text in expected:
            self.assertIn(text, err)

    def test_two_currencies_in_currency_column(self):
        self.assertRejected(*run(DATA / "two_currencies.csv", *CURRENCY_COLUMN), "USD", "line 3")

    def test_mixed_currency_file_without_any_currency_flag(self):
        self.assertRejected(*run(DATA / "two_currencies.csv", *CORE, "--revenue", "Revenue"),
                            "--currency-column", "--no-currency-column")

    def test_currency_declaration_missing(self):
        self.assertRejected(*run(DATA / "ratios.csv", *CORE, *NO_ATTRIBUTION_COLUMN),
                            "--currency-column", "--no-currency-column")

    def test_currency_declaration_both_ways(self):
        self.assertRejected(*run(DATA / "two_currencies.csv", *CURRENCY_COLUMN, *NO_CURRENCY_COLUMN),
                            "--currency-column", "--no-currency-column")

    def test_currency_column_differs_from_flag(self):
        flags = list(CURRENCY_COLUMN)
        flags[flags.index("EUR")] = "USD"
        with TempCsv("Campaign;Currency;Spend;Conversions;Revenue\nSample A;EUR;1;1;1\n") as path:
            self.assertRejected(*run(path, *flags), "USD", "EUR")

    def test_attribution_declaration_missing(self):
        self.assertRejected(*run(DATA / "ratios.csv", *CORE, *NO_CURRENCY_COLUMN),
                            "--attribution-column", "--no-attribution-column")

    def test_attribution_declaration_both_ways(self):
        self.assertRejected(*run(DATA / "two_currencies.csv", *ATTRIBUTION_COLUMN, *NO_ATTRIBUTION_COLUMN),
                            "--attribution-column", "--no-attribution-column")

    def test_two_attribution_values(self):
        with TempCsv("Campaign;Attribution;Spend;Conversions\nSample A;1-day;1;1\nSample B;7-day;1;1\n") as path:
            self.assertRejected(*run(path, *ATTRIBUTION_COLUMN), "line 3", "7-day")

    def test_single_attribution_value_is_accepted(self):
        code, _, err = run(DATA / "two_currencies.csv", *ATTRIBUTION_COLUMN, "--revenue", "Revenue")
        self.assertEqual(code, 0, err)

    def test_empty_spend_cell_names_line_and_column(self):
        self.assertRejected(*run(DATA / "empty_cell.csv", *WITH_REVENUE), "line 3", "Spend")

    def test_dash_cells_are_rejected(self):
        for cell in ("-", "—"):
            with self.subTest(cell=cell), TempCsv(f"Campaign;Spend;Conversions\nSample A;{cell};1\n") as path:
                self.assertRejected(*run(path, *BASE), "line 2", "Spend")

    def test_negative_revenue_is_rejected(self):
        with TempCsv("Campaign;Spend;Conversions;Revenue\nSample A;1;1;-1\n") as path:
            self.assertRejected(*run(path, *WITH_REVENUE), "line 2", "Revenue", "negative")

    def test_fractional_conversion_is_rejected(self):
        with TempCsv("Campaign;Spend;Conversions\nSample A;1;2,5\n") as path:
            self.assertRejected(*run(path, *BASE), "line 2", "Conversions")

    def test_identical_rows_without_flag(self):
        self.assertRejected(*run(DATA / "duplicates.csv", *WITH_REVENUE), "2 identical lines", "--count-duplicates")

    def test_duplicate_id(self):
        self.assertRejected(*run(DATA / "duplicates.csv", *WITH_REVENUE, "--id", "ID"), "k1", "line 2", "line 3")

    def test_missing_required_flag(self):
        self.assertRejected(*run(DATA / "ratios.csv", "--spend", "Spend", "--decimal", ","),
                            "--conversions", "--currency")

    def test_unknown_decimal_choice(self):
        flags = list(BASE)
        flags[flags.index(",")] = ";"
        code, out, err = run(DATA / "ratios.csv", *flags)
        self.assertRejected(code, out, err, "error")

    def test_column_not_in_header(self):
        flags = list(BASE)
        flags[flags.index("Spend")] = "Cost"
        self.assertRejected(*run(DATA / "ratios.csv", *flags), "Cost")

    def test_optional_column_not_in_header(self):
        self.assertRejected(*run(DATA / "ratios.csv", *BASE, "--id", "Missing"), "Missing")

    def test_ambiguous_delimiter_asks_for_flag(self):
        with TempCsv("Campaign;Spend,Conversions\nSample A;1,1\n") as path:
            self.assertRejected(*run(path, *BASE), "--delimiter")

    def test_header_without_delimiter_asks_for_flag(self):
        with TempCsv("Spend\n1\n") as path:
            self.assertRejected(*run(path, *BASE), "--delimiter")

    def test_row_with_missing_cell(self):
        with TempCsv("Campaign;Spend;Conversions\nSample A;1\n") as path:
            self.assertRejected(*run(path, *BASE), "line 2")

    def test_missing_file(self):
        self.assertRejected(*run(DATA / "no-such-file.csv", *BASE), "no-such-file.csv")

    def test_no_data_rows(self):
        with TempCsv("Campaign;Spend;Conversions\nTotal;1;1\n") as path:
            self.assertRejected(*run(path, *BASE), "no data lines")


class WarningTest(unittest.TestCase):
    def test_total_label_row_is_skipped_with_warning(self):
        result = run_json(DATA / "total_row.csv", *WITH_REVENUE)
        self.assertEqual(Decimal(result["total"]["spend"]), Decimal("400"))
        self.assertEqual(len(result["rows"]), 2)
        code, out, _ = run(DATA / "total_row.csv", *WITH_REVENUE)
        self.assertEqual(code, 0)
        warnings = out.split("Warnings", 1)[1]
        self.assertIn("line 4", warnings)
        self.assertIn("limited", warnings)

    def test_short_total_row_is_skipped_with_warning(self):
        with TempCsv("Campaign;Spend;Conversions;Revenue\nSample A;100;1;250\nTotal;100\n") as path:
            code, out, err = run(path, *WITH_REVENUE)
        self.assertEqual(code, 0, err)
        self.assertIn("line 3", out.split("Warnings", 1)[1])

    def test_total_label_is_read_from_name_column(self):
        text = "ID;Campaign;Spend;Conversions\nk1;Sample A;1;1\nk9;TOTAL;1;1\n"
        with TempCsv(text) as path:
            result = run_json(path, *BASE, "--name", "Campaign")
        self.assertEqual(len(result["rows"]), 1)

    def test_identical_rows_are_counted_with_flag(self):
        code, out, err = run(DATA / "duplicates.csv", *WITH_REVENUE, "--count-duplicates")
        self.assertEqual(code, 0, err)
        self.assertIn("2 identical lines", out.split("Warnings", 1)[1])
        result = run_json(DATA / "duplicates.csv", *WITH_REVENUE, "--count-duplicates")
        self.assertEqual(Decimal(result["total"]["spend"]), Decimal("500"))


class EncodingAndDelimiterTest(unittest.TestCase):
    """A Turkish export: non-ASCII headers and names, read as UTF-8 or as Windows Turkish (cp1254)."""
    TEXT = "Kampanya;Harcama;Dönüşüm;Gelir\nİlkbahar ölçümü;100,00;1;250,00\n"
    FLAGS = ["--spend", "Harcama", "--conversions", "Dönüşüm", "--revenue", "Gelir", "--currency", "TRY",
             "--decimal", ",", *NO_CURRENCY_COLUMN, *NO_ATTRIBUTION_COLUMN]

    def test_reads_windows_turkish_encoding(self):
        with TempCsv(self.TEXT, encoding="cp1254") as path:
            code, out, err = run(path, *self.FLAGS)
        self.assertEqual(code, 0, err)
        self.assertIn("İlkbahar ölçümü", out)

    def test_reads_utf8_with_bom(self):
        with TempCsv(self.TEXT, encoding="utf-8-sig") as path:
            code, _, err = run(path, *self.FLAGS)
        self.assertEqual(code, 0, err)

    def test_tab_delimiter_flag(self):
        with TempCsv(self.TEXT.replace(";", "\t")) as path:
            code, _, err = run(path, *self.FLAGS, "--delimiter", "tab")
        self.assertEqual(code, 0, err)

    def test_explicit_delimiter_resolves_ambiguous_header(self):
        with TempCsv("Campaign;Spend;Conversions\nSample, A;1;1\n") as path:
            code, _, err = run(path, *BASE, "--delimiter", ";")
        self.assertEqual(code, 0, err)


class FooterTest(unittest.TestCase):
    VARIANTS = {
        "text": ["ratios.csv", *WITH_REVENUE],
        "no_revenue": ["ratios.csv", *BASE],
        "with_warning": ["total_row.csv", *WITH_REVENUE],
        "not_computable": ["zeros.csv", *WITH_REVENUE],
        "with_period": ["ratios.csv", *WITH_REVENUE, "--period", "October 2026"],
    }

    def test_text_output_always_ends_with_the_three_lines(self):
        for name, (file, *flags) in self.VARIANTS.items():
            with self.subTest(variant=name):
                code, out, _ = run(DATA / file, *flags)
                self.assertEqual(code, 0)
                last = out.rstrip("\n").splitlines()[-3:]
                self.assertIn("EUR", last[0])
                self.assertEqual(last[1:], [PANEL_NOTE, SAMPLE_NOTE])

    def test_json_output_always_carries_the_notes(self):
        for name, (file, *flags) in self.VARIANTS.items():
            with self.subTest(variant=name):
                notes = run_json(DATA / file, *flags)["notes"]
                self.assertEqual(notes[1:], [PANEL_NOTE, SAMPLE_NOTE])

    def test_unlabeled_totals_warning_is_always_printed(self):
        for name, (file, *flags) in self.VARIANTS.items():
            with self.subTest(variant=name):
                _, out, _ = run(DATA / file, *flags)
                self.assertIn(f"- {UNLABELED_TOTALS_NOTE}", out.split("Warnings", 1)[1].splitlines())
                self.assertIn(UNLABELED_TOTALS_NOTE, run_json(DATA / file, *flags)["warnings"])

    def test_period_text_or_default(self):
        code, out, _ = run(DATA / "ratios.csv", *BASE)
        self.assertIn("period not given", out.splitlines()[-3])
        code, out, _ = run(DATA / "ratios.csv", *BASE, "--period", "October 2026")
        self.assertIn("October 2026", out.splitlines()[-3])


class SafetyTest(unittest.TestCase):
    BANNED = re.compile(r"\b(urllib|socket|http|requests|subprocess|os\.system|os\.remove|unlink|rmtree|"
                        r"eval\(|exec\(|write_text|write_bytes|open\([^)]*['\"][wa])")
    NO_VERDICT = ("winner:", "recommendation:", "significant", "threshold")

    def test_tool_has_no_network_process_or_write_calls(self):
        source = (HERE / "ad_metrics.py").read_text(encoding="utf-8")
        self.assertIsNone(self.BANNED.search(source))

    def test_documented_command_writes_no_bytecode(self):
        with tempfile.TemporaryDirectory() as folder:
            copy = Path(folder) / "scripts"
            copy.mkdir()
            (copy / "ad_metrics.py").write_bytes((HERE / "ad_metrics.py").read_bytes())
            out = subprocess.run([sys.executable, "-I", "scripts/ad_metrics.py", str(DATA / "ratios.csv"),
                                  *WITH_REVENUE], capture_output=True, encoding="utf-8", cwd=folder,
                                 stdin=subprocess.DEVNULL)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertIn(PANEL_NOTE, out.stdout)
            self.assertEqual(sorted(p.name for p in copy.iterdir()), ["ad_metrics.py"])

    def test_documented_command_rejects_with_exit_code_two(self):
        out = subprocess.run([sys.executable, "-I", "-B", str(HERE / "ad_metrics.py"), str(DATA / "empty_cell.csv"),
                              *WITH_REVENUE], capture_output=True, encoding="utf-8", cwd=tempfile.gettempdir(),
                             stdin=subprocess.DEVNULL)
        self.assertEqual(out.returncode, 2)
        self.assertEqual(out.stdout, "")
        self.assertIn("line 3", out.stderr)

    def test_output_has_no_verdict_words(self):
        code, out, _ = run(DATA / "ratios.csv", *WITH_REVENUE)
        body = out.replace(SAMPLE_NOTE, "").lower()
        for word in self.NO_VERDICT:
            with self.subTest(word=word):
                self.assertNotIn(word, body)


if __name__ == "__main__":
    unittest.main()
