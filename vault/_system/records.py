"""Locked and atomic writes to shared vault files: pending items, log, handoff cards.

Why: parallel chats can write at the same time (rule #36). A pending number is taken under the lock, with the
file read again. A pending item closes only with evidence (#24). Handoff cards keep "where were we" when a session
is reset. Other sessions' cards and old cards are not deleted: whatever goes beyond what the file keeps is moved word
for word to a monthly archive (#22). A session updates only its own card (like editing a note; the old version stays
in git history).

Usage (from the vault root):
  records.py pending add --type approval --text "..." --source note-name --chat "Chat title" [--project name]
  records.py pending close P-012 --note "user: yes; done" --evidence "commit abc1234"
  records.py pending hold P-006 --note "user: look at it later"
  records.py log --operation progress --title "..." [--body-file path] [--evidence "..."] [--learned "..."]
  records.py handoff write --session <session_id> --label "short name" --file card.md
  records.py handoff read [--count 2] [--limit 2500]
  records.py index --section "Knowledge — ML / Data Science" --line "- [[note-name]] — one-line summary"
"""
import argparse
import re
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the -I flag does not add the script folder to the path
from common import LANGUAGE, VAULT, LockUnavailable, atomic_write, locked, name, vault_path  # noqa: E402

PENDING = vault_path("inbox", "pending.md")
LOG = vault_path("log.md")
HANDOFF = vault_path("inbox", "handoff.md")
INDEX = vault_path("index.md")
LINK_TARGET = re.compile(r"\[\[([^\]|#]+)")
HANDOFF_ARCHIVE = vault_path("archive", "handoff")
LOG_ARCHIVE = vault_path("archive", "log")              # log entries of past months, word for word
PENDING_ARCHIVE = vault_path("archive", "pending")      # closed pending items of past months
# A work entry links to the related note and stays short: the details live in the note; Obsidian's backlinks show
# "which entry this note is in"
UNLINKED_OPERATIONS = {"pending", "done", "lint", "query", "profile"}
LEARNED_OPERATIONS = {"progress", "setup", "research", "problem", "decision", "learning"}   # '- Learned:' line required
BODY_LINE_LIMIT = 3
LOG_ENTRY = re.compile(r"^## \[(\d{4}-\d{2}-\d{2})\] ", re.M)
# Rotation within a month: the limit is below health.py's large-file limit (1,500 lines / 150 KB), so no warning shows
LOG_LIMIT_LINES, LOG_LIMIT_BYTES = 1200, 120_000
LOG_TARGET_LINES, LOG_TARGET_BYTES = 1000, 100_000
CLOSE_DATE = re.compile(r"\| ✔ (\d{4}-\d{2})-\d{2}")
TYPES = {"question", "approval", "decision", "task", "notice", "on-hold"}
OPERATIONS = {"setup", "idea", "project", "progress", "problem", "decision", "experiment", "ingest", "research", "query",
              "lint", "rule", "profile", "release", "pending", "done", "learning", "violation"}
PENDING_PREFIX = "B" if LANGUAGE == "tr" else "P"   # new ids; both prefixes are read
CLOSED_HEADINGS = ("Closed", "Kapananlar")          # the heading of the closed section, in both languages
CLOSED_HEADING = "## " + CLOSED_HEADINGS[0]
CLOSED_LINE = re.compile(rf"^## (?:{'|'.join(CLOSED_HEADINGS)})[ \t]*$", re.M)
NOTE_NAME = re.compile(r"^[\w.\- ]+$")   # wiki link target: no [, ], |, line break (no line injection)
PENDING_LINE = re.compile(r"^- \[( |x|X)\] ([PB]-(\d+)) \|([^|]*)\|")
CLOSED_PENDING = re.compile(r"^- \[x\] [PB]-")
HANDOFF_CARD_LIMIT = 3000
HANDOFF_KEPT = 6          # number of newest cards kept in the file; older ones move to the archive
HANDOFF_HEADING = re.compile(r"^## (\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}) · (.+?) · ([0-9a-f-]{8})\s*$", re.M)


class RecordError(ValueError):
    pass


def one_line(text: str) -> str:
    """Removes characters that break the table/line format."""
    return " ".join(str(text).replace("|", "/").split())


def short_summary(text: str, limit: int) -> str:
    """One-line log summary; if the cut falls inside a [[link]], it extends to the end of the link so the link stays whole."""
    flat = one_line(text)
    if len(flat) <= limit:
        return flat
    opening = flat.rfind("[[", 0, limit)
    if opening > flat.rfind("]]", 0, limit):
        closing = flat.find("]]", opening)
        limit = closing + 2 if closing != -1 else opening   # unclosed link: cut before the link
    return flat[:limit].rstrip() + "…"


def today() -> str:
    return date.today().isoformat()


# ---------- log ----------
def append_to_archive(directory: Path, kind: str, month: str, text: str) -> None:
    """Appends the records of a past month to `directory/<kind>-<month>.md`; opens the file with a header if missing.
    The archive is not changed or deleted."""
    path = directory / f"{kind}-{month}.md"   # kind prefix: the log and pending archives must not share names
    current = path.read_text(encoding="utf-8") if path.is_file() else (
        f"---\ntype: entry\ntags: [{name('archive')}, {kind}]\ncreated: {today()}\nupdated: {today()}\n---\n\n"
        f"# {kind.capitalize()} archive — {month}\n\n> The old records of this month or of a past month were moved here "
        "word for word. Not changed, not deleted.\n")
    atomic_write(path, current.rstrip("\n") + "\n" + text.strip("\n") + "\n")


def log_entries(text: str) -> tuple[str, list[tuple[str, str]]]:
    """(leading frontmatter and description, [(day, the entry's text word for word)])."""
    positions = [(m.start(), m.group(1)) for m in LOG_ENTRY.finditer(text)]
    if not positions:
        return text, []
    ends = [pos for pos, _ in positions[1:]] + [len(text)]
    return text[:positions[0][0]], [(day, text[pos:end]) for (pos, day), end in zip(positions, ends)]


def cutoff_date(text: str, this_day: str) -> str:
    """Entries older than this date go to the archive. Normally the start of the month; if the log passed the limit,
    the newest days stay as long as they fit the target. A day is not split, today's entries are never moved."""
    month_start = this_day[:7] + "-01"
    if text.count("\n") <= LOG_LIMIT_LINES and len(text.encode("utf-8")) <= LOG_LIMIT_BYTES:
        return month_start
    head, entries = log_entries(text)
    days: dict[str, str] = {}
    for day, entry in entries:
        days[day] = days.get(day, "") + entry
    kept = head + "".join(entry for day, entry in days.items() if day >= this_day)
    cutoff = this_day
    for day in sorted((d for d in days if d < this_day), reverse=True):
        candidate = kept + days[day]
        if candidate.count("\n") > LOG_TARGET_LINES or len(candidate.encode("utf-8")) > LOG_TARGET_BYTES:
            break
        kept, cutoff = candidate, day
    return max(month_start, cutoff)


def rotate_log(text: str, cutoff: str) -> tuple[str, dict[str, str]]:
    """Splits entries older than the cutoff month by month: (remaining log, {month: entries}). The leading
    frontmatter and description stay."""
    head, entries = log_entries(text)
    remaining, months = [head], {}
    for day, entry in entries:
        if day < cutoff:
            months[day[:7]] = months.get(day[:7], "") + entry
        else:
            remaining.append(entry)
    return "".join(remaining), months


def add_log(operation: str, title: str, body: str = "", evidence: str = "", learned: str = "") -> None:
    if operation not in OPERATIONS:
        raise RecordError(f"unknown operation '{operation}' (vault CLAUDE.md §10: {', '.join(sorted(OPERATIONS))})")
    lines = [s.rstrip() for s in body.strip().splitlines() if s.strip()]
    if operation not in UNLINKED_OPERATIONS and "[[" not in title + body:
        raise RecordError("a work entry must give a [[link]] to the related note: the details live in the note, "
                          "the log is only an index")
    if operation in LEARNED_OPERATIONS and not learned.strip():
        raise RecordError(f"a '{operation}' entry needs a '- Learned:' line; if there is no lesson write --learned \"none\"")
    if len(lines) > BODY_LINE_LIMIT:
        raise RecordError(f"the log body is at most {BODY_LINE_LIMIT} lines (now {len(lines)}): write the details in the "
                          "related note, put a summary and a link in the log")
    parts = [f"\n## [{today()}] {operation} | {one_line(title)}\n"]
    if lines:
        parts.append("\n".join(lines) + "\n")
    if evidence:
        parts.append(f"- Evidence: {one_line(evidence)}\n")
    if learned:
        parts.append(f"- Learned: {one_line(learned)}\n")
    with locked("log"):
        text = LOG.read_text(encoding="utf-8")
        remaining, months = rotate_log(text, cutoff_date(text, today()))
        for month, entries in sorted(months.items()):   # archive first: if interrupted, an entry is in two places, not lost
            append_to_archive(LOG_ARCHIVE, "log", month, entries)
        atomic_write(LOG, remaining.rstrip("\n") + "\n" + "".join(parts))


# ---------- pending ----------
def next_number(text: str) -> int:
    """Numbers in the archive count too: a number is not reused after rotation."""
    archive = [p.read_text(encoding="utf-8") for p in sorted(PENDING_ARCHIVE.glob("*.md"))] if PENDING_ARCHIVE.is_dir() else []
    numbers = [int(m.group(3)) for m in map(PENDING_LINE.match, "\n".join([text, *archive]).splitlines()) if m]
    return max(numbers, default=0) + 1


def rotate_closed(content: str, this_month: str) -> tuple[str, dict[str, str]]:
    """Splits the '- [x]' lines closed before this month, month by month (word for word); the rest stays as it is."""
    remaining, months = [], {}
    for line in content.splitlines(keepends=True):
        m = CLOSE_DATE.search(line) if CLOSED_PENDING.match(line) else None
        if m and m.group(1) < this_month:
            months[m.group(1)] = months.get(m.group(1), "") + line
        else:
            remaining.append(line)
    return "".join(remaining), months


def touch_updated(text: str) -> str:
    return re.sub(r"^updated: .*$", f"updated: {today()}", text, count=1, flags=re.M)


def validate_note_name(field: str, value: str) -> str:
    if value and not NOTE_NAME.match(value):
        raise RecordError(f"{field} '{value[:40]}' is invalid: only a note name (letters, digits, '-', '_', '.', space)")
    return value


def closed_heading(content: str) -> re.Match:
    m = CLOSED_LINE.search(content)
    if not m:
        raise RecordError(f"heading '{CLOSED_HEADING}' not found in {PENDING.name}; the file was not changed")
    return m


def add_pending(kind: str, text: str, source: str, chat: str, project: str = "") -> str:
    if kind not in TYPES:
        raise RecordError(f"type '{kind}' is invalid ({', '.join(sorted(TYPES))})")
    if not chat.strip():
        raise RecordError("a chat title is required (§7.10)")
    validate_note_name("source", source)
    validate_note_name("project", project)
    with locked("pending"):
        content = PENDING.read_text(encoding="utf-8")
        heading = closed_heading(content)
        no = f"{PENDING_PREFIX}-{next_number(content):03d}"
        line = f"- [ ] {no} | {kind} | {today()} | {one_line(text)} | [[{source}]] | chat: {one_line(chat)}"
        if project:
            line += f" | project: [[{project}]]"
        content = content[:heading.start()].rstrip("\n") + "\n" + line + "\n\n" + content[heading.start():]
        atomic_write(PENDING, touch_updated(content))
    add_log("pending", f"{no} — {short_summary(text, 90)}")
    return no


def _find_line(content: str, no: str) -> str:
    m = re.search(rf"^- \[ \] {re.escape(no)} \|[^\n]*\n", content, re.M)
    if not m:
        raise RecordError(f"open {no} not found (it may already be closed)")
    return m.group(0)


def close_pending(no: str, note: str, evidence: str) -> None:
    if not evidence.strip():
        raise RecordError("evidence is required (#24): write a commit id, a note link or command output")
    with locked("pending"):
        content = PENDING.read_text(encoding="utf-8")
        line = _find_line(content, no)
        closed = (line.rstrip("\n").replace(f"- [ ] {no}", f"- [x] {no}", 1)
                  + f" | ✔ {today()} ({one_line(note)} · evidence: {one_line(evidence)})\n")
        content = content.replace(line, "", 1)
        heading = closed_heading(content)   # if not found, nothing is written; the item is not lost
        rest = content[heading.end():]
        content = content[:heading.end()] + "\n" + closed + (rest[1:] if rest.startswith("\n") else rest)
        content, months = rotate_closed(content, today()[:7])
        for month, lines in sorted(months.items()):
            append_to_archive(PENDING_ARCHIVE, name("pending"), month, lines)
        atomic_write(PENDING, touch_updated(content))
    add_log("done", f"{no} — {short_summary(note, 90)}")   # the evidence is in the pending line; one log line is enough


def hold_pending(no: str, note: str) -> None:
    """Moves the item to the 'on-hold' type: it stays open and is listed as "look at later"."""
    with locked("pending"):
        content = PENDING.read_text(encoding="utf-8")
        line = _find_line(content, no)
        parts = line.split("|")
        parts[1] = " on-hold "
        new = "|".join(parts).rstrip("\n") + f" | ⏸ {today()}: {one_line(note)}\n"
        atomic_write(PENDING, touch_updated(content.replace(line, new, 1)))
    add_log("pending", f"{no} put on hold — {short_summary(note, 80)}")


# ---------- index ----------
AUTO_BLOCK = re.compile(r"<!-- central:start -->.*?<!-- central:end -->", re.S)


def add_index(section: str, line: str) -> None:
    """Adds a line under the `## <section>` heading of index.md, at the end of the section. Never writes into the
    automatic "Most central notes" block: that block is regenerated and a line added by hand would be lost (#36)."""
    indent = " " * min(len(line) - len(line.lstrip(" ")), 4)   # project sub-notes are indented in the index (two levels at most)
    line = indent + one_line(line)
    target = LINK_TARGET.search(line)
    if not line.lstrip(" ").startswith("- [[") or not target:
        raise RecordError("the line must look like '- [[note-name]] — summary' (leading spaces for a sub-item)")
    with locked("index"):
        text = INDEX.read_text(encoding="utf-8")
        auto = AUTO_BLOCK.search(text)
        free = text[:auto.start()] + "\0" * (auto.end() - auto.start()) + text[auto.end():] if auto else text
        if re.search(rf"^[ \t]*- \[\[{re.escape(target.group(1))}\]\]", free, re.M):
            raise RecordError(f"[[{target.group(1)}]] is already in the index")
        m = re.search(rf"^## {re.escape(section)}[ \t]*$", free, re.M)
        if not m:
            raise RecordError(f"{INDEX.name} has no '## {section}' section (the automatic block does not count)")
        following = re.search(r"^## ", free[m.end():], re.M)
        end = m.end() + following.start() if following else len(text)
        body = text[m.end():end].rstrip("\n")
        atomic_write(INDEX, text[:m.end()] + body + "\n" + line + "\n\n" + text[end:].lstrip("\n"))


# ---------- handoff cards ----------
HANDOFF_EMPTY = """---
type: entry
status: active
tags: [entry, {handoff}]
aliases: [handoff cards, recent sessions, where were we]
created: {date}
updated: {date}
---

# Handoff cards — recent sessions

> Every meaningful session writes its own card before it ends (`records.py handoff write`). At session start the
> newest cards come into the context (`session_log.py remind`). Card: what was done, why, what is still open, next
> step, sources. The newest {kept} cards stay here; older ones are moved word for word under `{archive}/`, not deleted.
> See the vault `CLAUDE.md` §7.8 and the context management skill.
"""


def handoff_cards(text: str) -> list[tuple[str, str]]:
    """[(session8, card text)] — in file order (newest on top)."""
    headings = list(HANDOFF_HEADING.finditer(text))
    cards = []
    for i, m in enumerate(headings):
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        cards.append((m.group(4), text[m.start():end].rstrip("\n") + "\n"))
    return cards


def write_handoff(session: str, label: str, body: str) -> None:
    session8 = re.sub(r"[^0-9a-f-]", "", session.lower())[:8]
    if len(session8) < 8:
        raise RecordError("the session id must have at least 8 hexadecimal characters")
    if len(body) > HANDOFF_CARD_LIMIT:
        raise RecordError(f"card is {len(body)} characters; at most {HANDOFF_CARD_LIMIT}. Shorten it, link the details to a note")
    heading = f"## {datetime.now():%Y-%m-%d %H:%M} · {one_line(label)} · {session8}"
    card = heading + "\n" + body.strip() + "\n"
    with locked("handoff"):
        text = HANDOFF.read_text(encoding="utf-8") if HANDOFF.is_file() else HANDOFF_EMPTY.format(
            date=today(), kept=HANDOFF_KEPT, handoff=HANDOFF.stem,
            archive=HANDOFF_ARCHIVE.relative_to(VAULT).as_posix() if HANDOFF_ARCHIVE.is_relative_to(VAULT) else HANDOFF_ARCHIVE.name)
        first = HANDOFF_HEADING.search(text)
        before = text[:first.start()] if first else text.rstrip("\n") + "\n\n"
        cards = [c for s, c in handoff_cards(text) if s != session8]   # a session renews only its own card
        cards.insert(0, card)
        to_move = cards[HANDOFF_KEPT:]
        if to_move:
            _move_to_archive(to_move)
        atomic_write(HANDOFF, touch_updated(before + "\n".join(cards[:HANDOFF_KEPT])))


def _move_to_archive(cards: list[str]) -> None:
    target = HANDOFF_ARCHIVE / f"{HANDOFF.stem}-{date.today():%Y-%m}.md"
    if not target.is_file():
        head = (f"---\ntype: entry\nstatus: archived\ntags: [{HANDOFF.stem}, {name('archive')}]\ncreated: {today()}\n"
                f"updated: {today()}\n---\n\n# Handoff cards archive — {date.today():%Y-%m}\n\n"
                f"> Old cards moved from [[{HANDOFF.stem}]], word for word.\n\n")
    else:
        head = target.read_text(encoding="utf-8").rstrip("\n") + "\n\n"
    atomic_write(target, touch_updated(head + "\n".join(cards)))


def handoff_summary(count: int = 2, limit: int = 2500) -> str:
    if not HANDOFF.is_file():
        return ""
    from security_scan import HIDDEN   # invisible/direction-changing characters must not reach the session-start context
    text = HIDDEN.sub("", "\n".join(c for _, c in handoff_cards(HANDOFF.read_text(encoding="utf-8"))[:count]))
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n…(truncated; full text in {name('inbox')}/{name('handoff.md')})"


# ---------- command line ----------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="area", required=True)
    pending = sub.add_parser("pending").add_subparsers(dest="action", required=True)
    a = pending.add_parser("add")
    for flag in ("--type", "--text", "--source", "--chat"):
        a.add_argument(flag, required=True)
    a.add_argument("--project", default="")
    c = pending.add_parser("close")
    c.add_argument("no")
    c.add_argument("--note", required=True)
    c.add_argument("--evidence", required=True)
    h = pending.add_parser("hold")
    h.add_argument("no")
    h.add_argument("--note", required=True)
    lg = sub.add_parser("log")
    lg.add_argument("--operation", required=True)
    lg.add_argument("--title", required=True)
    lg.add_argument("--body-file", default="")
    lg.add_argument("--evidence", default="")
    lg.add_argument("--learned", default="")
    ix = sub.add_parser("index")
    ix.add_argument("--section", required=True, help='e.g. "Knowledge — ML / Data Science"')
    ix.add_argument("--line", required=True, help='"- [[note-name]] — one-line summary"')
    ho = sub.add_parser("handoff").add_subparsers(dest="action", required=True)
    hw = ho.add_parser("write")
    hw.add_argument("--session", required=True)
    hw.add_argument("--label", required=True)
    hw.add_argument("--file", required=True)
    hr = ho.add_parser("read")
    hr.add_argument("--count", type=int, default=2)
    hr.add_argument("--limit", type=int, default=2500)
    return p


def run(args) -> str:
    if args.area == "pending" and args.action == "add":
        return add_pending(args.type, args.text, args.source, args.chat, args.project)
    if args.area == "pending" and args.action == "close":
        close_pending(args.no, args.note, args.evidence)
        return f"{args.no} closed"
    if args.area == "pending":
        hold_pending(args.no, args.note)
        return f"{args.no} on hold"
    if args.area == "index":
        add_index(args.section, args.line)
        return "index line added"
    if args.area == "log":
        body = Path(args.body_file).read_text(encoding="utf-8") if args.body_file else ""
        add_log(args.operation, args.title, body, args.evidence, args.learned)
        return "log written"
    if args.action == "write":
        write_handoff(args.session, args.label, Path(args.file).read_text(encoding="utf-8"))
        return "handoff card written"
    return handoff_summary(args.count, args.limit)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        print(run(build_parser().parse_args()))
    except (RecordError, LockUnavailable, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
