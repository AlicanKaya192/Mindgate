"""Builds the data sets of the dashboard (a claude.ai Data artifact) from the vault.

Only Claude can publish them, with its own Artifact tools (the /dashboard skill); this script only writes JSON files
under `_system/output/dashboard/` (outside git) and a manifest of their SHA-256 values, so the skill uploads only the
data sets that changed. The data sets, their ids and fields follow the dashboard data contract (20 sets plus `meta`).

Privacy filter (rules #17, #18): `me/`, the root `CLAUDE.md`, raw session records (only their number), notes with
`privacy: private` and paths with a sensitive name never reach a data set; neither do links that touch them. Every text
field passes the secret scan; a text with a finding is replaced by HIDDEN_TEXT. A data set is never an empty list (the
dashboard counts an empty file as an error): it gets one placeholder row instead.

Chat trace: from the Claude Code transcripts on this computer (~/.claude/projects/*/*.jsonl) it finds which chat opened
and last changed a note and which chat first wrote a log entry, a progress item, a task or a pending line. Only the chat
title, the note name and short hashes of lines are taken, never the content, and only chats that wrote to the vault keep
their title and folder. The trace lasts in `_system/chat_trace.json`
(in git, so it outlives the transcripts); how far each transcript was read is kept in
`_system/output/chat_trace_position.json`. Unrecorded chats (rule #43, session_mode.py) are not traced and not shown.

Run (from the vault root):  python -I _system/dashboard_data.py [--dry]
  --dry   writes nothing into the vault (no chat trace); only the output files are built
"""
import argparse
import ast
import hashlib
import json
import re
import sys
from contextlib import nullcontext
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I does not put the script folder on the path
import common  # noqa: E402
import session_mode as sm  # noqa: E402
from common import ascii_lower, atomic_write, frontmatter, locked, name, sensitive_path, vault_path  # noqa: E402

DATASETS = ("meta", "notes", "log", "versions", "links", "tasks", "counts", "progress", "weekly", "pending", "agents",
            "agent_runs", "expertise", "skills", "discoveries", "rules", "health", "handoff", "system", "cost", "councils")
PLACEHOLDER = "_placeholder"
PLACEHOLDER_KEY = "_placeholder"
HIDDEN_TEXT = "[hidden]"          # the page shows its own word for it
TOP_FOLDERS = ("inbox", "projects", "ideas", "councils", "problems", "knowledge", "research", "me", "rules", "drafts",
               "archive", "sources", "_templates", "_system")
NOT_NOTE_FOLDERS = ("_templates", "_system", "rules")   # link targets, not notes; rules have their own data set
OUT_OF_VAULT = {".obsidian", ".git", ".trash", ".claude"}   # .claude: agent worktrees hold copies of notes
PRIVATE_FOLDERS = ("me",)
PRIVATE_PAGES = {"CLAUDE"}
ROOT_PAGES = {"index", "log"}                       # pages that are not expected to get links
WORK_TYPES = {"project", "progress", "idea", "draft"}   # checklists in other notes are not tasks
HIDDEN_OPERATIONS = {"profile", "rule"}             # their log titles and bodies stay out
STALE_DAYS = 60
SUMMARY_CHARS, DETAIL_CHARS, LOG_CHARS, PROGRESS_CHARS, HANDOFF_CHARS = 220, 260, 420, 420, 1500
WEEKLY_CHARS, LIST_CHARS, COUNCIL_SUMMARY_CHARS, RULE_TITLE_CHARS = 400, 900, 300, 80
ATTACHMENTS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".pdf"}
OUTPUT_FOLDER = ("_system", "output", "dashboard")
SOURCES_NOT_WAITING = {".gitkeep"}
SOURCE_ASSETS = "assets"

LINK = re.compile(r"\[\[([^\]|#]+)")
LINK_TEXT = re.compile(r"\[\[([^\]|]+)\|?([^\]]*)\]\]")
EMBED_OR_LINK = re.compile(r"!?" + LINK_TEXT.pattern)
MD_LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
CODE_BLOCK = re.compile(r"```.*?```", re.S)
CODE_SPAN = re.compile(r"`[^`\n]*`")
TASK = re.compile(r"^\s*- \[( |x|X)\] (.+)$", re.M)
LOG_ENTRY = re.compile(r"^## \[(\d{4}-\d{2}-\d{2})\] (\S+) \| (.+)$", re.M)
PROGRESS_HEADING = re.compile(r"^### (\d{4}-\d{2}-\d{2})(?: \((\d+)\))?[ \t]*(?:[—–-][ \t]*(.*))?$", re.M)
LABELLED_ITEM = re.compile(r"^- \*\*([^*]+?):?\*\*:?\s*(.*)$")
LIST_ITEM = re.compile(r"^(?:[-*]|\d+\.)\s+")
PENDING_LINE = re.compile(r"^\s*- \[( |x|X)\]\s*([PB]-\d+)\s*\|\s*([^|]+?)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*(.+?)\s*(?:\|\s*(.*?))?\s*$")
PENDING_FIELD = re.compile(r"^(chat|sohbet|project|proje)\s*:\s*(.*)$", re.I)
CHAT_FIELDS = {"chat", "sohbet"}
HELD_KINDS = {"on-hold", "beklemede"}
CLOSE_DATE = re.compile(r"✔\s*(\d{4}-\d{2}-\d{2})")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
TABLE_DATE_ROW = re.compile(r"^\|\s*(\d{4}-\d{2}-\d{2})\s*\|(.*)\|\s*$")
RULE_ROW = re.compile(r"^\|\s*(\d+)\s*\|(.*)\|\s*$")
BOLD_START = re.compile(r"^\*\*(.+?)\*\*")
FIRST_SENTENCE = re.compile(r"(?<=[.!?])\s")
AGENT_PAGE = re.compile(r"^(?:agent|ajan)-(.+)$")
AGENT_LEVEL = re.compile(r"(?:Level|Mode|Seviye|Mod)\s*(\d)")
EXPERT_PACK = re.compile(r"^(?:expert|uzman)-")
SKILL_CELL = re.compile(r"`/?([\w-]+)`")
PRELOADED = re.compile(r"^skills:[ \t]*\n((?:[ \t]+-[ \t]*\S.*\n?)+)", re.M)
URL = re.compile(r"https?://([^\s)>`]+)")
IDEA_SOURCES_LINE = re.compile(r"(?:Idea sources?|Fikir kaynakları?):(.*)")
PARENTHESES = re.compile(r"\([^)]*\)")
COUNCIL_TITLE = re.compile(r"^(?:Council|Kurul): ")
QUIZ_SCORE = re.compile(r"(?:Memory quiz|Hafıza sınavı)[^\n\d]*?([\d.,]+\s*/\s*\d+)", re.I)

# Section headings in both install languages: (summary section, second line section) for each note type
SUMMARY_SECTIONS = {
    "problem": (r"(?:Symptom|Belirti)", r"(?:Solution|Çözüm)"),
    "decision": (r"(?:Decision|Karar)", r"(?:Context|Bağlam)"),
    "concept": (r"(?:In one sentence|Tek cümlede)", r"(?:In practice|Pratikte)"),
    "research": (r"(?:Question|Soru)", r"(?:Conclusion|Sonuç)"),
    "idea": (r"(?:Raw idea|Ham fikir)", r"(?:First step|İlk adım)"),
    "project": (r"(?:Goal|Hedef)", r"(?:Status|Durum)"),
}
PROGRESS_SECTION = r"(?:Log|Günlük)"
VERSION_SECTION = r"(?:Version history|Sürüm geçmişi)"
LESSONS_SECTION = r"(?:Lessons|Dersler)"
LESSON_CANDIDATES_SECTION = r"(?:Pending candidates|Bekleyen adaylar)"
COUNCIL_SUMMARY_SECTION = r"(?:Summary|Özet)"
IDEA_SOURCES_SECTION = r"(?:Idea sources?|Fikir kaynakları?)"
METHOD_SKILLS_HEADING = re.compile(r"^### (?:Method skills|Yöntem becerileri)", re.M)
REGISTRY_WHAT = ("What it does", "Field", "What", "Ne yapar", "Alan", "Ne")
REGISTRY_USES = ("Usage", "Kullanım")
REGISTRY_LAST = ("Last used", "Son kullanım")
EMPTY_CELLS = {"—", "-", ""}
WEEKLY_PATTERNS = ("*-weekly-summary.md", "*-haftalik-ozet.md")
PROJECT_RULE_PATTERNS = ("*/*-rules.md", "*/*-kurallar.md")
WEEKLY_TASKS = ("weekly", "haftalik")      # the id the weekly task reports under, in an English and a Turkish install


# ---------- text helpers ----------
def placeholder() -> dict:
    return {"key": PLACEHOLDER_KEY, PLACEHOLDER: True}


def safe(text: str) -> str:
    """The text, or HIDDEN_TEXT when the secret scan finds something in it."""
    from secret_scan import scan_line
    return HIDDEN_TEXT if any(scan_line(line) for line in text.splitlines()) else text


def safe_lines(text: str) -> str:
    """Line by line: only a line with a finding is hidden (handoff cards keep their other lines)."""
    from secret_scan import scan_line
    return "\n".join(HIDDEN_TEXT if scan_line(line) else line for line in text.splitlines())


def shorten(text: str, limit: int) -> str:
    """The text cut to `limit` characters. The secret scan sees the whole text first: a cut key is no longer found."""
    if len(text) <= limit:
        return text
    text = safe(text)
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


def note_key(target: str) -> str:
    """The name Obsidian resolves a link or note to: 'Ideas/My-Note.md#part' -> 'my-note'. Private names are kept this way."""
    stem = target.split("#")[0].strip().replace("\\", "/").rsplit("/", 1)[-1]
    return re.sub(r"\.md$", "", stem, flags=re.I).lower()


def hide_private_links(text: str, private: set) -> str:
    """[[x]], [[x|y]] and ![[x]] links to a private note, in any spelling Obsidian resolves, become HIDDEN_TEXT,
    so plain() does not turn them into the note's name."""
    def hidden(m):
        return HIDDEN_TEXT if note_key(m.group(1)) in private else m.group(0)
    return EMBED_OR_LINK.sub(hidden, text)


def plain(text: str) -> str:
    """[[a|b]] -> b, [[a]] -> a, **x** -> x."""
    text = LINK_TEXT.sub(lambda m: (m.group(2) or m.group(1)).strip(), text)
    return re.sub(r"\*\*|__", "", text).strip()


def bare(text: str) -> str:
    """Plain text without code marks: the dashboard shows table cells as plain text."""
    return plain(text).replace("`", "")


def keep_code_text(text: str) -> str:
    """A code block becomes its first line; inline code loses its backticks (the content stays)."""
    def block(m):
        lines = [s for s in m.group(1).splitlines()[1:] if s.strip()]
        return lines[0].strip() if lines else ""
    return CODE_SPAN.sub(lambda m: m.group(0).strip("`"), re.sub(r"```(.*?)```", block, text, flags=re.S))


def first_sentences(text: str, limit: int) -> str:
    """The first plain lines (no headings, callouts, tables), as one line of text."""
    parts = []
    for line in keep_code_text(text).splitlines():
        s = line.strip()
        if not s or s.startswith(("#", ">", "|", "<!--", "![")):
            continue
        s = re.sub(r"^(?:[-*]|\d+\.)\s+(?:\[[ xX]\]\s+)?", "", s)
        parts.append(plain(" ".join(s.split())))
        if sum(len(p) for p in parts) >= limit:
            break
    return shorten(" ".join(parts), limit)


def section(body: str, heading: str) -> str:
    """Body of the '## <heading>' section, up to the next '## ' heading."""
    m = re.search(r"^##+ " + heading + r"[^\n]*\n(.*?)(?=^## |\Z)", body, re.M | re.S)
    return m.group(1).strip() if m else ""


def list_items(text: str) -> list[str]:
    """The '- ' items of a section, without the mark."""
    return [s.strip()[2:] for s in text.splitlines() if s.strip().startswith("- ")]


def summary_pair(kind: str, body: str) -> tuple[str, str]:
    if kind in SUMMARY_SECTIONS:
        first, second = SUMMARY_SECTIONS[kind]
        return first_sentences(section(body, first), SUMMARY_CHARS), first_sentences(section(body, second), DETAIL_CHARS)
    after_title = body.split("\n# ", 1)[-1].split("\n", 1)[-1] if body.lstrip().startswith("#") else body
    return first_sentences(after_title, SUMMARY_CHARS), ""


def link_target(value) -> str:
    if not isinstance(value, str):
        return ""
    m = LINK.search(value)
    return m.group(1).strip() if m else value.strip()


def joined(value) -> str:
    return ", ".join(value) if isinstance(value, list) else str(value)


def number(value) -> int:
    return int(value) if str(value).isdigit() else 0


def days_since(day: str, today: str) -> int:
    try:
        return (date.fromisoformat(today) - date.fromisoformat(str(day)[:10])).days
    except ValueError:
        return 0


def table_cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def table_rows(text: str) -> list[list[str]]:
    """Data rows of the first Markdown table in the text (header and separator left out), as cell lists."""
    lines = [s.strip() for s in text.splitlines() if s.strip().startswith("|")]
    return [table_cells(s) for s in lines[2:]]


def padded(cells: list[str], count: int) -> list[str]:
    return (cells + [""] * count)[:count]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def latest_date(lessons: list[str]) -> str:
    return max((d for lesson in lessons for d in DATE.findall(lesson)), default="")


def public_name(stem: str, private: set) -> str:
    """The name of a linked note, or "" when the note is private: its name does not travel either."""
    return "" if note_key(stem) in private else stem


def lesson_text(lessons: list[str]) -> str:
    return shorten(" • ".join(plain(lesson) for lesson in lessons), LIST_CHARS)


# ---------- vault layout ----------
def base_folder(local: str) -> str:
    """Local top folder name ('projeler') -> English base name ('projects'); unknown names stay as they are."""
    return next((base for base in TOP_FOLDERS if name(base) == local), local)


def is_private(relative: Path, fields: dict) -> bool:
    return (base_folder(relative.parts[0]) in PRIVATE_FOLDERS and len(relative.parts) > 1
            or relative.stem in PRIVATE_PAGES and len(relative.parts) == 1
            or str(fields.get("privacy", "")).lower() == "private"
            or sensitive_path(relative.as_posix()))


def public_text(path: Path) -> str:
    """The text of a vault page, or "" when the page is private."""
    text = read(path)
    if text and is_private(path.relative_to(common.VAULT), frontmatter(text)[0]):
        return ""
    return text


def weekly_summaries() -> list[Path]:
    folder = vault_path("research")
    found = {p for pattern in WEEKLY_PATTERNS for p in folder.glob(pattern)} if folder.is_dir() else set()
    return sorted(found, key=lambda p: p.name)


# ---------- chat trace ----------
TRANSCRIPTS = Path.home() / ".claude" / "projects"
TRACE_FILE = ("_system", "chat_trace.json")                         # in git: the trace outlives the transcripts
TRACE_POSITION = ("_system", "output", "chat_trace_position.json")  # outside git: how far each transcript was read
TRACE_WAITING = ("_system", "output", "chat_trace_waiting.json")    # outside git: chats read that have not written yet
WRITE_TOOLS = {"Write", "Edit", "MultiEdit"}
COMMAND_TOOLS = {"Bash", "PowerShell"}
NOT_TRACED_FOLDERS = PRIVATE_FOLDERS + NOT_NOTE_FOLDERS
SCRIPT_FILES = ("log.md", "-progress.md", "-ilerleme.md")   # a command that names one of these may write traced lines
SCRIPT_STRING = re.compile(r'"((?:[^"\\\n]|\\.)*)"|\'((?:[^\'\\\n]|\\.)*)\'')
TRAILING_QUOTE = re.compile(r"""\s*["']{1,3}\s*[),+\]]*\s*;?\s*$""")
TRACE_KEY_CHARS, TRACE_KEY_MIN, TRACE_HASH_CHARS = 160, 8, 12
STAMP_CHARS, SID_CHARS = 16, 8
WORKTREES = "/.claude/worktrees/"


def empty_trace() -> dict:
    return {"chats": {}, "notes": {}, "lines": {}}


def trace_key(line: str) -> str:
    """A short hash of a line, independent of its form: list, box and heading marks, `*`, `[[ ]]` and the closing stamp
    are dropped. Too short a line gives no key (it would match too much)."""
    s = line.strip().split(" | ✔")[0]
    s = re.sub(r"^#+\s*", "", s)
    s = re.sub(r"^[-*]\s*(?:\[[ xX]\]\s*)?", "", s)
    s = re.sub(r"[`*]|\[\[|\]\]", "", s)
    s = " ".join(s.lower().split())[:TRACE_KEY_CHARS]
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:TRACE_HASH_CHARS] if len(s) >= TRACE_KEY_MIN else ""


def traced_lines(text: str) -> list[str]:
    """Lines whose writer is traced: list items and log headings."""
    return [s for s in text.splitlines() if s.strip().startswith(("- ", "## ["))]


def unescape(text: str) -> str:
    return text.replace("\\n", "\n").replace('\\"', '"').replace("\\'", "'").replace("\\\\", "\\")


def script_lines(tool_input: dict) -> list[str]:
    """Log headings and list items inside a command or script that writes to the vault.

    Scripts often carry the lines inside quotes with `\\n` escapes; the escapes are opened and quote or bracket leftovers
    at the end of a line are dropped. Strings that stand next to each other ("..." "...") count as one text."""
    raw = "\n".join(str(v) for v in tool_input.values() if isinstance(v, str))
    markers = (common.VAULT.name, name("pending.md")) + SCRIPT_FILES
    if not any(m.lower() in raw.lower() for m in markers):
        return []
    lines = [TRAILING_QUOTE.sub("", s.strip()) for s in traced_lines(unescape(raw))]
    pieces, end = [], -1
    for m in SCRIPT_STRING.finditer(raw):
        piece = unescape(m.group(1) if m.group(1) is not None else m.group(2))
        if pieces and raw[end:m.start()].strip(" \t\r\n(") == "":
            pieces.append(piece)
        else:
            lines += traced_lines("".join(pieces))
            pieces = [piece]
        end = m.end()
    return lines + traced_lines("".join(pieces))


def added_lines(tool: str, tool_input: dict) -> list[str]:
    """The traced lines a Write brings, or the new lines of an Edit (lines already in the old text are not new)."""
    if tool == "Write":
        return traced_lines(str(tool_input.get("content", "")))
    edits = tool_input.get("edits") or [tool_input]
    lines = []
    for edit in edits if isinstance(edits, list) else []:
        if isinstance(edit, dict):
            old = set(str(edit.get("old_string", "")).splitlines())
            lines += [s for s in traced_lines(str(edit.get("new_string", ""))) if s not in old]
    return lines


def chat_folder(cwd: str) -> str:
    """The name of the chat's working folder (of the main folder for a worktree); "" for the home folder, whose name
    is the user name."""
    path = str(cwd or "").replace("\\", "/").split(WORKTREES)[0].rstrip("/")
    if path.lower() == Path.home().as_posix().lower():
        return ""
    return path.split("/")[-1]


def traced_note(relative: Path) -> bool:
    parts = relative.parts
    return bool(parts) and not (parts[0] in OUT_OF_VAULT or base_folder(parts[0]) in NOT_TRACED_FOLDERS
                                or name("sessions") in parts or relative.stem in PRIVATE_PAGES
                                or sensitive_path(relative.as_posix()))


def vault_marker() -> re.Pattern:
    """The vault path without its drive, as it appears inside any tool path ('c:/…', '/c/…' or a WSL path)."""
    path = re.sub(r"^[A-Za-z]:", "", common.VAULT.as_posix()).rstrip("/") + "/"
    return re.compile(re.escape(path), re.I)


class TraceReader:
    """Reads new transcript lines into the trace: chat titles and folders, which chat opened and last changed a note,
    which chat first wrote a line."""

    def __init__(self, trace: dict):
        self.trace = trace
        self.marker = vault_marker()
        self.hint = common.VAULT.name.lower().encode("utf-8")

    def read(self, path: Path, start: int) -> int:
        """Reads the transcript from `start` and returns the new position."""
        size = path.stat().st_size
        if start > size:
            start = 0   # the file was replaced: read it again
        if start == size:
            return start
        with open(path, "rb") as transcript:
            transcript.seek(start)
            for raw in transcript:
                if not raw.endswith(b"\n"):
                    break   # the last line is still being written; the next run reads it
                start += len(raw)
                self.line(raw)
        return start

    def line(self, raw: bytes) -> None:
        title_line = b'"custom-title"' in raw
        if not title_line and not (b'"tool_use"' in raw and self.hint in raw.lower()):
            return
        try:
            entry = json.loads(raw)
        except ValueError:
            return
        sid = str(entry.get("sessionId", ""))[:SID_CHARS] if isinstance(entry, dict) else ""
        if not sid:
            return
        chat = self.trace["chats"].setdefault(sid, {"title": "", "folder": ""})
        if entry.get("cwd") and not chat["folder"]:
            chat["folder"] = safe(chat_folder(entry["cwd"]))
        if title_line and entry.get("type") == "custom-title":
            chat["title"] = safe(str(entry.get("customTitle", "")).strip()) or chat["title"]
            return
        if entry.get("type") != "assistant":
            return
        stamp = str(entry.get("timestamp", ""))[:STAMP_CHARS]
        content = (entry.get("message") or {}).get("content") or []
        for part in content if isinstance(content, list) else []:
            if isinstance(part, dict) and part.get("type") == "tool_use" and part.get("name") in WRITE_TOOLS | COMMAND_TOOLS:
                self.tool_use(part["name"], part.get("input") or {}, stamp, sid)

    def tool_use(self, tool: str, tool_input, stamp: str, sid: str) -> None:
        if not isinstance(tool_input, dict):
            return
        path = str(tool_input.get("file_path", "")).replace("\\", "/")
        found = self.marker.search(path)
        if tool in COMMAND_TOOLS or not found or not path.lower().endswith(".md"):
            for line in script_lines(tool_input):   # lines written by a command or by a script file outside the vault
                self.keep_line(line, stamp, sid)
            return
        relative = Path(path[found.end():])
        if not traced_note(relative) or is_private(relative, frontmatter(read(common.VAULT / relative))[0]):
            return   # the lasting trace is in git: a private note's name stays out of it too
        self.note_write(relative.stem, stamp, sid)
        for line in added_lines(tool, tool_input):
            self.keep_line(line, stamp, sid)

    def note_write(self, stem: str, stamp: str, sid: str) -> None:
        entry = self.trace["notes"].setdefault(stem, {"first": [stamp, sid], "last": [stamp, sid]})
        if stamp < entry["first"][0]:
            entry["first"] = [stamp, sid]
        if stamp >= entry["last"][0]:
            entry["last"] = [stamp, sid]

    def keep_line(self, line: str, stamp: str, sid: str) -> None:
        key = trace_key(line)
        lines = self.trace["lines"]
        if key and (key not in lines or stamp < lines[key][0]):
            lines[key] = [stamp, sid]


def read_json(path: Path) -> dict:
    """The JSON object in the file, {} if there is none. A broken file raises ValueError, so it is never overwritten."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} is not a JSON object")
    return data


def read_positions() -> dict:
    """How far each transcript was read. A broken file counts as empty: the transcripts are read again from the start,
    and the lasting trace is kept (a line already traced keeps its earliest writer)."""
    try:
        return read_json(vault_path(*TRACE_POSITION))
    except ValueError as error:
        common.log_error("dashboard_data chat trace position", error)
        return {}


def position(value) -> int:
    """A stored position, or 0 (the start) when it is not a whole number of bytes."""
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0


def split_chats(trace: dict) -> tuple[dict, dict]:
    """(chats that wrote a traced note or line, the other chats). Only the writers go into the lasting trace in git; the
    others wait outside git, so a title read before the chat's first write is still known when it writes."""
    writers = {sid for entry in trace["notes"].values() for _, sid in (entry["first"], entry["last"])}
    writers |= {sid for _, sid in trace["lines"].values()}
    chats = trace["chats"].items()
    return {sid: chat for sid, chat in chats if sid in writers}, {sid: chat for sid, chat in chats if sid not in writers}


def read_waiting() -> dict:
    """The chats read before that have not written yet; a broken file counts as empty (only titles are lost)."""
    try:
        return read_json(vault_path(*TRACE_WAITING))
    except ValueError as error:
        common.log_error("dashboard_data chat trace waiting", error)
        return {}


def update_chat_trace(save: bool = True) -> dict:
    """Reads the new parts of the transcripts into the lasting trace and returns it; save=False (--dry) writes nothing.

    The lock keeps two chats that build at the same time from overwriting each other's update."""
    with locked("chat_trace") if save else nullcontext():
        trace = {**empty_trace(), **read_json(vault_path(*TRACE_FILE))}
        trace["chats"] = {**read_waiting(), **trace["chats"]}
        positions = read_positions()
        reader = TraceReader(trace)
        unrecorded = sm.unrecorded_filter()
        for transcript in sorted(TRANSCRIPTS.glob("*/*.jsonl")):
            if unrecorded(transcript.stem):
                continue   # not traced; its position stays, so a chat recorded later is read from the start
            positions[str(transcript)] = reader.read(transcript, position(positions.get(str(transcript))))
        trace["chats"], waiting = split_chats(trace)
        if save:
            atomic_write(vault_path(*TRACE_FILE), json.dumps(trace, ensure_ascii=False, indent=0, sort_keys=True))
            atomic_write(vault_path(*TRACE_WAITING), json.dumps(waiting, ensure_ascii=False, indent=0, sort_keys=True))
            atomic_write(vault_path(*TRACE_POSITION), json.dumps(positions, indent=1))
    return trace


def visible_trace(trace: dict) -> dict:
    """The trace without the chats that are unrecorded now (a chat may be turned unrecorded after it was traced).
    If the mode file cannot be read, no chat is shown (the safe side)."""
    try:
        hidden = {sid[:SID_CHARS] for sid in sm.unrecorded_sessions()}
    except sm.CorruptFile:
        return empty_trace()
    return {**trace, "chats": {sid: chat for sid, chat in trace.get("chats", {}).items() if sid not in hidden}}


def chat_name(trace: dict, sid: str) -> str:
    chat = trace["chats"].get(sid) or {}
    return chat.get("title") or chat.get("folder") or ""


def line_sid(trace: dict, line: str) -> str:
    record = trace["lines"].get(trace_key(line))
    return record[1] if record else ""


def line_chat(trace: dict, line: str) -> str:
    return chat_name(trace, line_sid(trace, line))


# ---------- notes ----------
class Scan:
    """One pass over the vault's notes: public notes, link sets, private names and the work rows built from them."""

    def __init__(self, vault: Path, today: str, trace: dict):
        self.vault, self.today, self.trace = vault, today, trace
        self.notes, self.outgoing, self.private, self.known = {}, {}, set(), set()
        self.tasks, self.progress, self.versions, self.councils, self.sessions = [], [], [], [], 0
        self.source_files = set()
        self.known |= {p.name for p in vault.rglob("*") if p.suffix.lower() in ATTACHMENTS and not OUT_OF_VAULT & set(p.parts)}
        sessions_folder = (name("inbox"), name("sessions"))
        pages, session_records = [], set()
        for path in sorted(vault.rglob("*.md")):
            relative = path.relative_to(vault)
            if relative.parts[0] in OUT_OF_VAULT:
                continue
            if base_folder(relative.parts[0]) in NOT_NOTE_FOLDERS:
                self.known.add(path.stem)   # Obsidian resolves links to these files
                continue
            if relative.parts[:2] == sessions_folder:
                self.sessions += 1
                session_records.add(path.stem)
                continue
            pages.append((path, relative, *frontmatter(read(path))))
        # Every private name is known before the first row is built, so no row names a private note
        self.private = {note_key(path.stem) for path, relative, fields, _ in pages if is_private(relative, fields)}
        self.private_notes = len(self.private)
        self.private |= {note_key(s) for s in session_records}   # a link to a raw session record is neither shown nor counted as broken
        for page in pages:
            self.add(*page)

    def hide(self, text: str) -> str:
        return hide_private_links(text, self.private)

    def add(self, path: Path, relative: Path, fields: dict, body: str) -> None:
        stem = path.stem
        if fields.get("source_file"):
            self.source_files.add(str(fields["source_file"]).replace("\\", "/").strip())
        self.outgoing[stem] = {m.strip() for m in LINK.findall(CODE_SPAN.sub("", CODE_BLOCK.sub("", body)))} - {stem}
        if is_private(relative, fields):
            return
        kind = fields.get("type", "") or "other"
        title = re.search(r"^# (.+)$", body, re.M)
        title = self.hide(title.group(1).strip()) if title else stem
        project = public_name(link_target(fields.get("project", "")), self.private)
        summary, detail = summary_pair(kind, self.hide(body))
        open_tasks = self.add_tasks(stem, title, kind, project, body)
        written = self.trace["notes"].get(stem) or {}
        self.notes[stem] = {
            "key": stem, "id": stem, "title": safe(title), "type": kind, "status": fields.get("status", ""),
            "project": project, "folder": base_folder(relative.parts[0]) if len(relative.parts) > 1 else "",
            "path": relative.as_posix(), "tags": joined(fields.get("tags", [])), "aliases": joined(fields.get("aliases", [])),
            "summary": safe(summary), "detail": safe(detail),
            "created": fields.get("created", ""), "updated": fields.get("updated", ""),
            "age_days": days_since(fields.get("updated", ""), self.today),
            "words": len(re.findall(r"\w+", body)), "open_tasks": open_tasks,
            "chat": chat_name(self.trace, written["first"][1]) if written else "",
            "chat_last": chat_name(self.trace, written["last"][1]) if written else "",
        }
        if kind == "progress":
            self.progress += progress_rows(project or stem, body, self.trace, self.private)
            self.versions += version_rows(project or stem, self.hide(body))
        if kind == "council":
            self.councils.append(council_row(stem, title, fields, self.hide(body), self.private))

    def add_tasks(self, stem: str, title: str, kind: str, project: str, body: str) -> int:
        if kind not in WORK_TYPES:
            return 0
        open_count = 0
        for i, (mark, raw) in enumerate(TASK.findall(CODE_BLOCK.sub("", body))):
            text = plain(self.hide(raw).replace("`", ""))
            if not text:
                continue
            done = 0 if mark == " " else 1
            open_count += 1 - done
            self.tasks.append({"key": f"{stem}#{i}", "note_id": stem, "note": safe(title),
                               "project": project or (stem if kind == "project" else ""), "task": safe(text), "done": done,
                               "chat": line_chat(self.trace, raw)})
        return open_count

    def links(self) -> list[dict]:
        everything = set(self.notes) | self.private | self.known
        rows = []
        for source, targets in self.outgoing.items():
            for target in sorted(targets):
                if note_key(source) in self.private or note_key(target) in self.private:
                    continue   # a link that touches a private note stays out
                rows.append({"key": f"{source}>{target}", "source": source, "target": target,
                             "broken": 0 if target in everything else 1})
        for stem, row in self.notes.items():
            row["links_out"] = len(self.outgoing.get(stem, ()))
            row["links_in"] = sum(1 for s, t in self.outgoing.items() if s != stem and stem in t)
            row["orphan"] = 1 if row["links_in"] == 0 and stem not in ROOT_PAGES else 0
        return rows


def progress_rows(project: str, body: str, trace: dict, private: set) -> list[dict]:
    """'### 2026-10-10 — Title' entries of the progress log, one row per '- **Label:** text' item."""
    rows = []
    parts = PROGRESS_HEADING.split(section(body, PROGRESS_SECTION))
    for i in range(1, len(parts), 4):
        day, count, entry = parts[i], parts[i + 1], parts[i + 3]
        title = hide_private_links((parts[i + 2] or "").strip(), private)
        order = 0
        for line in keep_code_text(entry).splitlines():
            s = line.strip()
            if not s.startswith("- "):
                continue
            m = LABELLED_ITEM.match(s)
            label, text = (m.group(1).strip(), m.group(2)) if m else ("", s[2:])
            text = plain(hide_private_links(" ".join(text.split()), private))
            if not text:
                continue
            order += 1
            rows.append({"key": f"{project}:{day}{f'({count})' if count else ''}:{order}", "project": project,
                         "date": day, "title": safe(title), "label": label, "text": safe(shorten(text, PROGRESS_CHARS)),
                         "order": order, "chat": line_chat(trace, s)})
    return rows


def version_rows(project: str, body: str) -> list[dict]:
    """The '| version | date | highlights |' table of the 'Version history' section of a progress note."""
    rows = []
    for line in section(body, VERSION_SECTION).splitlines():
        cells = table_cells(line)
        if len(cells) < 3 or not DATE.match(cells[1]):
            continue
        version = cells[0].replace("*", "")
        rows.append({"key": f"{project}:{version}", "project": project, "version": version, "date": cells[1][:10],
                     "summary": plain(cells[2])})
    return rows


def council_row(stem: str, title: str, fields: dict, body: str, private: set) -> dict:
    return {"key": stem, "id": stem, "date": fields.get("created") or stem[:10], "job": COUNCIL_TITLE.sub("", title),
            "mode": fields.get("mode", ""), "agents": joined(fields.get("agents", [])), "result": fields.get("result", ""),
            "calls": number(fields.get("calls")), "opus": number(fields.get("opus")),
            "project": public_name(link_target(fields.get("project", "")), private),
            "decision_note": public_name(link_target(fields.get("decision_note", "")), private),
            "summary": shorten(plain(section(body, COUNCIL_SUMMARY_SECTION)), COUNCIL_SUMMARY_CHARS)}


# ---------- records ----------
def log_text() -> str:
    archive = vault_path("archive", "log")
    texts = [read(p) for p in sorted(archive.glob("*.md"))] if archive.is_dir() else []
    return "\n".join(texts + [read(vault_path("log.md"))])


def log_rows(text: str, notes: dict, trace: dict, private: set) -> list[dict]:
    projects = {stem: [stem.lower()] + [a.lower() for a in n["aliases"].split(", ") if a]
                for stem, n in notes.items() if n["type"] == "project"}
    rows = []
    parts = LOG_ENTRY.split(text)
    for i in range(1, len(parts), 4):
        day, operation, title, body = parts[i], parts[i + 1], parts[i + 2].strip(), parts[i + 3]
        hidden = operation in HIDDEN_OPERATIONS
        sid = line_sid(trace, f"## [{day}] {operation} | {title}")
        folder = (trace["chats"].get(sid) or {}).get("folder", "")
        rows.append({"key": str(len(rows) + 1), "no": len(rows) + 1, "date": day, "operation": operation,
                     "title": "" if hidden else safe(plain(hide_private_links(title, private))),
                     "detail": "" if hidden else safe(first_sentences(hide_private_links(body, private), LOG_CHARS)),
                     "chat": chat_name(trace, sid),
                     "project": "" if hidden else log_project(title + "\n" + body, notes, projects, folder)})
    return rows


def log_project(text: str, notes: dict, projects: dict, folder: str) -> str:
    """The first linked project note or note with a project; otherwise the project the writing chat's folder is named after."""
    for target in LINK.findall(text):
        note = notes.get(target.strip())
        if note and (note["project"] or note["type"] == "project"):
            return note["project"] or note["id"]
    for project, words in projects.items():
        if any(re.search(r"\b" + re.escape(w) + r"\b", folder.lower()) for w in words):
            return project
    return ""


def pending_text() -> str:
    archive = vault_path("archive", "pending")
    texts = [read(p) for p in sorted(archive.glob("*.md"))] if archive.is_dir() else []
    return "\n".join([read(vault_path("inbox", "pending.md"))] + texts)


def pending_rows(notes: dict, private: set, trace: dict) -> list[dict]:
    """Pending items, with the closed ones of the monthly archives. A link to a private note is left empty, so its name
    does not travel either; without a project field the project of the source note is used."""
    rows = []
    for line in pending_text().splitlines():
        m = PENDING_LINE.match(line)
        if not m:
            continue
        mark, number_, kind, day, text, rest = m.groups()
        fields, source, closed = {}, "", ""
        for part in (rest or "").split("|"):
            part = part.strip()
            field = PENDING_FIELD.match(part)
            if field:
                key = "chat" if field.group(1).lower() in CHAT_FIELDS else "project"
                fields[key] = link_target(field.group(2))
                continue
            close = CLOSE_DATE.search(part)
            closed = close.group(1) if close else closed
            if not source and LINK.search(part):
                source = link_target(part)
        project = fields.get("project") or source_project(notes.get(source))
        done = mark != " "
        rows.append({"key": number_, "id": number_, "kind": kind, "date": day,
                     "text": safe(plain(hide_private_links(text, private))),
                     "source": public_name(source, private),
                     "chat": fields.get("chat") or line_chat(trace, line),
                     "project": public_name(project, private),
                     "status": "done" if done else "held" if kind.lower() in HELD_KINDS else "open",
                     "closed": closed if done else ""})
    return rows


def source_project(note: dict | None) -> str:
    if not note:
        return ""
    return note["project"] or (note["id"] if note["type"] == "project" else "")


def handoff_rows(private: set) -> list[dict]:
    from records import HANDOFF_HEADING, handoff_cards
    rows = []
    for order, (session, card) in enumerate(handoff_cards(hide_private_links(read(vault_path("inbox", "handoff.md")), private))):
        heading = HANDOFF_HEADING.match(card)
        body = card.split("\n", 1)[1] if "\n" in card else ""
        rows.append({"key": f"{heading.group(1)}-{heading.group(2)}-{session}", "date": heading.group(1),
                     "time": heading.group(2), "label": safe(heading.group(3)), "session": session,
                     "text": shorten(safe_lines(body.strip()), HANDOFF_CHARS), "order": order})
    return rows


def weekly_rows(private: set) -> list[dict]:
    """The sections of the newest weekly summary: its list items, or its first sentences."""
    summaries = weekly_summaries()
    if not summaries:
        return []
    path = summaries[-1]
    day = path.name[:10]
    body = hide_private_links(frontmatter(public_text(path))[1], private)
    rows = []
    for order, m in enumerate(re.finditer(r"^## (.+)$", body, re.M)):
        heading = m.group(1).strip()
        content = section(body, re.escape(heading))
        items = [plain(" ".join(LIST_ITEM.sub("", s.strip()).split())) for s in keep_code_text(content).splitlines()
                 if LIST_ITEM.match(s.strip())]
        text = " • ".join(items) if items else first_sentences(content, WEEKLY_CHARS)
        if text:
            rows.append({"key": f"{day}:{order}", "date": day, "section": heading, "text": shorten(text, LIST_CHARS), "order": order})
    return rows


def lesson_candidates() -> list[dict]:
    """The 'Pending candidates' table: lessons waiting for the user's approval. A leading number column is optional."""
    _, body = frontmatter(read(vault_path("rules", "lesson-candidates.md")))
    rows = []
    for i, cells in enumerate(table_rows(section(body, LESSON_CANDIDATES_SECTION)), start=1):
        count = cells.pop(0) if len(cells) > 4 and cells[0].isdigit() else str(i)
        candidate, evidence, place, day = padded(cells, 4)
        rows.append({"number": count, "candidate": candidate, "evidence": evidence, "place": place, "date": day})
    return rows


def count_rows(scan: Scan, log: list[dict], text_of_log: str) -> list[dict]:
    stale = sum(1 for n in scan.notes.values() if n["status"] == "active" and n["type"] != "entry" and n["age_days"] > STALE_DAYS)
    last_lint = max((r["date"] for r in log if r["operation"] == "lint"), default="")
    quiz = QUIZ_SCORE.findall("\n".join([text_of_log] + [public_text(p) for p in weekly_summaries()]))
    return [{"key": "sessions_waiting", "value": scan.sessions, "text": ""},
            {"key": "sources_waiting", "value": sources_waiting(scan.source_files), "text": ""},
            {"key": "stale_active", "value": stale, "text": ""},
            {"key": "private_notes", "value": scan.private_notes, "text": ""},
            {"key": "last_maintenance", "value": 0, "text": last_lint},
            {"key": "quiz_score", "value": 0, "text": quiz[-1].replace(" ", "") if quiz else ""},
            {"key": "lesson_candidates_waiting", "value": len(lesson_candidates()), "text": ""},
            {"key": "data_date", "value": 0, "text": scan.today}]


def sources_waiting(source_files: set) -> int:
    """Raw sources that no note names in its `source_file` field (the folder's own page and `assets/` left out)."""
    folder = vault_path("sources")
    if not folder.is_dir():
        return 0
    waiting = [p for p in folder.rglob("*") if p.is_file() and p.name not in SOURCES_NOT_WAITING | {f"{folder.name}.md"}
               and SOURCE_ASSETS not in p.relative_to(folder).parts]
    return sum(1 for p in waiting if p.relative_to(common.VAULT).as_posix() not in source_files)


# ---------- agents and skills ----------
CENTRAL_AGENT = {"key": "central", "name": "central", "display": "Central agent", "model": "", "effort": "", "color": "",
                 "level": "0", "tools": "all", "denied": "", "page": "",
                 "description": "The main chat itself: talks with the user, picks the mode of the work, does ordinary coding "
                                "itself, gives work to agents, merges and verifies their results, writes to the vault."}
DEFAULT_MODEL = "inherit"
DEFAULT_TOOLS = "all (except starting agents)"
NO_LEVEL = "—"
DISPLAY_SEPARATOR = " — "
# Result counters; the result is free text in the install language, compared from its start (ASCII folded)
RESULT_COUNTS = {"worked": ("worked", "ise"), "partly": ("partly", "kismen"), "unnecessary": ("unnecessary", "gereksiz"),
                 "upgraded": ("upgraded", "yukselt")}
INSTALLED_SKILLS = Path.home() / ".claude" / "skills"   # links Claude Code loads skills from


def agent_definitions() -> list[tuple[str, dict, str, str]]:
    """(name, frontmatter, body, whole text) of every agent definition."""
    found = []
    for path in sorted(vault_path("_system", "agents").glob("*.md")):
        text = read(path)
        fields, body = frontmatter(text)
        found.append((str(fields.get("name", "")).strip() or path.stem, fields, body, text))
    return found


def agent_pages(private: set) -> tuple[dict, list[dict]]:
    """({agent: (page, display name)}, runs) from the Log table of every public agent page."""
    pages, runs = {}, []
    folder = vault_path("knowledge", "agents-log")
    for page in sorted(folder.glob("*.md")) if folder.is_dir() else []:
        m = AGENT_PAGE.match(page.stem)
        text = public_text(page)
        if not m or not text:
            continue
        fields, body = frontmatter(text)
        body = hide_private_links(body, private)
        agent = str(fields.get("agent", "")).strip() or m.group(1)
        title = re.search(r"^# (.+)$", body, re.M)
        pages[agent] = (page.stem, title.group(1).split(DISPLAY_SEPARATOR)[0].strip() if title else agent)
        for i, line in enumerate(section(body, PROGRESS_SECTION).splitlines()):
            row = TABLE_DATE_ROW.match(line.strip())
            if not row:
                continue
            mode, model, job, result, chat, project = padded(table_cells(row.group(2)), 6)
            runs.append({"key": f"{agent}:{i}", "agent": agent, "date": row.group(1), "mode": mode, "model": model.lower(),
                         "job": safe(plain(job)), "result": safe(plain(result)),
                         "chat": "" if chat in EMPTY_CELLS else plain(chat),
                         "project": "" if project in EMPTY_CELLS else public_name(link_target(project), private)})
    return pages, runs


def run_statistics(runs: list[dict]) -> dict:
    def counted(prefixes: tuple[str, ...]) -> int:
        return sum(1 for r in runs if ascii_lower(r["result"]).startswith(prefixes))
    return {"total": len(runs), **{field: counted(prefixes) for field, prefixes in RESULT_COUNTS.items()},
            "last_date": max((r["date"] for r in runs), default="")}


def agent_rows(private: set) -> tuple[list[dict], list[dict]]:
    pages, runs = agent_pages(private)
    agents = [{**CENTRAL_AGENT, **run_statistics(runs)}]
    for agent, fields, _, _ in agent_definitions():
        description = str(fields.get("description", ""))
        level = AGENT_LEVEL.search(description)
        page, display = pages.get(agent, ("", agent))
        agents.append({"key": agent, "name": agent, "display": display, "model": str(fields.get("model") or DEFAULT_MODEL),
                       "effort": str(fields.get("effort", "")), "color": str(fields.get("color", "")),
                       "level": level.group(1) if level else NO_LEVEL, "tools": str(fields.get("tools") or DEFAULT_TOOLS),
                       "denied": str(fields.get("disallowedTools", "")), "description": description, "page": page,
                       **run_statistics([r for r in runs if r["agent"] == agent])})
    return agents, runs


def skill_files() -> list[tuple[str, dict, str, str]]:
    """(folder name, frontmatter, body, whole text) of every skill."""
    found = []
    for path in sorted(vault_path("_system", "skills").glob("*/SKILL.md")):
        text = read(path)
        fields, body = frontmatter(text)
        found.append((path.parent.name, fields, body, text))
    return found


def expertise_rows(private: set) -> list[dict]:
    rows = []
    for skill, fields, body, _ in skill_files():
        if not EXPERT_PACK.match(skill):
            continue
        lessons = list_items(section(hide_private_links(body, private), LESSONS_SECTION))
        rows.append({"key": skill, "name": str(fields.get("name") or skill),
                     "description": first_part(str(fields.get("description", ""))),
                     "lessons": len(lessons), "last_lesson": latest_date(lessons), "lesson_text": lesson_text(lessons)})
    return rows


def first_part(description: str) -> str:
    return description.split(". ")[0]


def registry() -> tuple[dict, set]:
    """From the skill registry: {skill: (what, uses, last used)} and the names in the method skills table."""
    text = read(vault_path("_system", "skills", "skills-registry.md"))
    counters, header = {}, []
    for line in text.splitlines():
        if not line.startswith("|"):
            header = []
            continue
        cells = table_cells(line)
        if not header:
            header = cells
            continue
        m = SKILL_CELL.match(cells[0])
        if not m:
            continue
        uses, last = column(header, cells, REGISTRY_USES), column(header, cells, REGISTRY_LAST)
        counters[m.group(1)] = (column(header, cells, REGISTRY_WHAT), number(uses), "" if last in EMPTY_CELLS else last)
    method_part = METHOD_SKILLS_HEADING.split(text, 1)
    methods = set(re.findall(r"^\| `([\w-]+)` \|", method_part[1].split("\n#", 1)[0], re.M)) if len(method_part) > 1 else set()
    return counters, methods


def column(header: list[str], cells: list[str], titles: tuple[str, ...]) -> str:
    """The cell under the first of `titles` that the table header has ("" if none)."""
    index = next((header.index(t) for t in titles if t in header), len(cells))
    return cells[index] if index < len(cells) else ""


def preloaded_skills(text: str) -> list[str]:
    """The YAML `skills:` list in the frontmatter of an agent definition."""
    end = text.find("\n---", 3)
    m = PRELOADED.search(text[:end] + "\n") if text.startswith("---") and end != -1 else None
    return [s.strip().lstrip("-").strip() for s in m.group(1).splitlines() if s.strip()] if m else []


def can_use_skills(fields: dict) -> bool:
    tools, denied = str(fields.get("tools", "")), str(fields.get("disallowedTools", ""))
    return (not tools or "Skill" in tools) and "Skill" not in denied


def mentions(body: str, skill: str) -> bool:
    expert_wildcard = EXPERT_PACK.match(skill) and re.search(r"`(?:expert|uzman)-\*`", body)
    return bool(re.search(rf"`/?{re.escape(skill)}`|skills/{re.escape(skill)}/", body) or expert_wildcard)


def source_names(text: str, body: str) -> list[str]:
    """Where a skill took its ideas from: GitHub repositories and sites in its links, 'Idea sources:' lines and the items
    of its 'Idea sources' section (claude.ai and full URLs left out)."""
    found = []

    def add(item: str) -> None:
        if item and item not in found:
            found.append(item)
    for url in URL.findall(text):
        parts = url.rstrip(".,;").split("/")
        if "." in parts[0] and parts[0] != "claude.ai":
            add("/".join(parts[1:3]) if parts[0] == "github.com" and len(parts) >= 3 else parts[0])
    listed = IDEA_SOURCES_LINE.findall(text) + list_items(section(body, IDEA_SOURCES_SECTION))
    for line in listed:
        for item in PARENTHESES.sub("", line).split(","):
            item = CODE_SPAN.sub("", item).strip(" .;:")
            if " " not in item and "://" not in item:
                add(item)
    return found


def skill_rows(private: set) -> list[dict]:
    """Every skill: what it is for, its kind, usage counter, which agent has it preloaded and which can load it."""
    agents = [(agent, preloaded_skills(text), body, can_use_skills(fields)) for agent, fields, body, text in agent_definitions()]
    counters, methods = registry()
    rows = []
    for skill, fields, body, text in skill_files():
        preloaded = [a for a, skills, _, _ in agents if skill in skills]
        loaders = [a for a, skills, agent_body, allowed in agents if allowed and skill not in skills and mentions(agent_body, skill)]
        kind = "expertise" if EXPERT_PACK.match(skill) else "method" if preloaded or skill in methods else "workflow"
        lessons = list_items(section(hide_private_links(body, private), LESSONS_SECTION))
        what, uses, last = counters.get(skill, ("", 0, ""))
        description = str(fields.get("description", ""))
        rows.append({"key": skill, "name": skill, "kind": kind, "command": "/" + skill, "what": bare(what) or first_part(description),
                     "description": description, "uses": uses, "last_used": last,
                     "preloaded": ", ".join(preloaded), "can_load": ", ".join(loaders),
                     "lessons": len(lessons), "last_lesson": latest_date(lessons), "lesson_text": lesson_text(lessons),
                     "sources": ", ".join(source_names(text, body)), "lines": len(text.splitlines()),
                     "installed": int((INSTALLED_SKILLS / skill / "SKILL.md").is_file())})
    return rows


# ---------- discoveries: trending projects and proposals (rule #31) ----------
STAR_MEASURE = re.compile(r"([\d.,]+)\s*(k|bin)?\s*★\s*·\s*(\d{4}-\d{2}-\d{2})(\s*\((?:unverified|doğrulanmadı|kaşif)\))?", re.I)
POPULARITY = ((100_000, "very_high"), (10_000, "high"), (1_000, "medium"), (0, "low"))   # GitHub stars
FIT = {4: "high", 3: "medium"}      # how many of the four proposal criteria hold; fewer is "low"
FIT_LOW = "low"
CRITERION_MET = "✓"
THOUSAND = 1000


def trending_page() -> Path:
    """The trending note; a Turkish install written by the Turkish weekly task keeps it under its Turkish name."""
    english = vault_path("knowledge", "trending", "trending-projects.md")
    turkish = vault_path("knowledge") / "gundem" / "gundemdeki-projeler.md"
    return english if english.is_file() or not turkish.is_file() else turkish


def star_count(digits: str, thousands: str) -> int:
    """'12.3' + 'k' -> 12300, '298,1' + 'bin' -> 298100, '1,234' -> 1234 (without a suffix, separators group thousands)."""
    if not thousands:
        return int(re.sub(r"[.,]", "", digits) or 0)
    decimal = re.sub(r"[.,](?=.*[.,])", "", digits).replace(",", ".")
    return round(float(decimal) * THOUSAND)


def star_measures(cell: str) -> list[tuple[int, str, bool]]:
    """'12.3k ★ · 2026-10-12; 13k ★ · 2026-10-20' -> [(12300, '2026-10-12', False), ...], by date."""
    measures = [(star_count(digits, thousands), day, bool(unverified))
                for digits, thousands, day, unverified in STAR_MEASURE.findall(cell)]
    return sorted(measures, key=lambda m: m[1])


def movement(measures: list[tuple[int, str, bool]]) -> str:
    """The average daily growth between the last two measures; one measure gives no guess."""
    if len(measures) < 2:
        return "single measure; growth not known yet"
    (before, first_day, _), (last, last_day, _) = measures[-2], measures[-1]
    days = max(1, (date.fromisoformat(last_day) - date.fromisoformat(first_day)).days)
    change = last - before
    return f"{'+' if change >= 0 else '−'}{abs(change):,} ★ ({days} days, ~{abs(change) // days:,}/day)"


def discovery_row(key: str, kind: str, **fields) -> dict:
    """The shared shape: the page expects the same fields in every row."""
    row = {"key": key, "kind": kind, "name": "", "url": "", "what": "", "goal": "", "use": "", "license": "", "date": "",
           "trending": "", "stars": 0, "rating": "", "unverified": 0, "movement": "", "criteria": "", "difficulty": "",
           "needs": "", "reason": "", "first_step": "", "source": "", "status": "", "rejected_kind": "", "words": "",
           "instead": ""}
    return {**row, **fields}


def trending_rows(private: set) -> list[dict]:
    rows = []
    for i, cells in enumerate(table_rows(hide_private_links(public_text(trending_page()), private))):
        project, what, goal, use, trend, license_, first_seen, source = padded(cells, 8)
        link = MD_LINK.search(project)
        measures = star_measures(trend)
        stars = measures[-1][0] if measures else 0
        rows.append(discovery_row(
            f"trending#{i}", "trending", name=link.group(1) if link else plain(project), url=link.group(2) if link else "",
            what=bare(what), goal=bare(goal), use=bare(use), license=license_, date=first_seen,
            trending=trend.split(";")[-1].strip(), stars=stars,
            rating=next(label for limit, label in POPULARITY if stars >= limit) if measures else "",
            unverified=int(bool(measures) and measures[-1][2]), movement=movement(measures), source=bare(source)))
    return rows


def proposal_rows(private: set) -> list[dict]:
    rows = []
    for i, cells in enumerate(table_rows(hide_private_links(public_text(vault_path("ideas", "project-proposals.md")), private))):
        day, proposal, what, goal, use, criteria, difficulty, needs, first_step, source, status = padded(cells, 11)
        rows.append(discovery_row(
            f"proposal#{i}", "proposal", name=bare(proposal), what=bare(what), goal=bare(goal), use=bare(use), date=day,
            rating=FIT.get(min(criteria.count(CRITERION_MET), 4), FIT_LOW), criteria=criteria, difficulty=bare(difficulty),
            needs=bare(needs), first_step=bare(first_step), source=bare(source), status=status))
    return rows


def rejected_rows(private: set) -> list[dict]:
    rows = []
    for i, cells in enumerate(table_rows(hide_private_links(public_text(vault_path("ideas", "rejected-proposals.md")), private))):
        day, proposal, words, reason, instead, status = padded(cells, 6)
        rows.append(discovery_row(f"rejected#{i}", "rejected", name=bare(proposal), date=day, words=bare(words),
                                  reason=bare(reason), instead=bare(instead), status=status))
    return rows


def discovery_rows(private: set) -> list[dict]:
    return trending_rows(private) + proposal_rows(private) + rejected_rows(private)


# ---------- rules ----------
def rule_title_and_text(cell: str) -> tuple[str, str]:
    """A bold start is the title, otherwise the first sentence; the title is not repeated in the text."""
    bold = BOLD_START.match(cell)
    if bold:
        return bare(bold.group(1)).rstrip(".:"), bare(cell[bold.end():])
    first, *rest = FIRST_SENTENCE.split(cell, maxsplit=1)
    return shorten(bare(first), RULE_TITLE_CHARS).rstrip(".:"), bare(rest[0] if rest else "")


def rule_table(text: str, source: str) -> list[dict]:
    """'| no | rule | why | (added) |' rows; each row keeps the '## ' section it stands in."""
    rows, heading = [], ""
    for line in text.splitlines():
        if line.startswith("## "):
            heading = line[3:].strip()
        m = RULE_ROW.match(line)
        if not m:
            continue
        rule, why, added = padded(table_cells(m.group(2)), 3)
        title, text = rule_title_and_text(rule)
        rows.append({"key": f"{source}#{m.group(1)}", "kind": "rule", "source": source, "number": int(m.group(1)),
                     "section": heading, "title": title, "text": text, "why": bare(why),
                     "date": added if DATE.fullmatch(added) else "", "rule": "", "noticed_by": "", "chat": "", "fix": ""})
    return rows


def project_rule_files() -> list[Path]:
    folder = vault_path("projects")
    return sorted({p for pattern in PROJECT_RULE_PATTERNS for p in folder.glob(pattern)}) if folder.is_dir() else []


def public_rules_text(path: Path, private: set) -> str:
    return hide_private_links(public_text(path), private)


def rule_rows(private: set) -> list[dict]:
    """General rules, the rules of every public project and the rule violations (#34). A private rule file, or the rule
    file of a private project, stays out whole."""
    rows = rule_table(public_rules_text(vault_path("rules", "general-rules.md"), private), "general")
    for path in project_rule_files():
        if note_key(path.parent.name) not in private:
            rows += rule_table(public_rules_text(path, private), path.parent.name)
    for i, cells in enumerate(table_rows(public_rules_text(vault_path("rules", "rule-violations.md"), private))):
        day, rule, what, cause, fix, noticed_by, chat = padded(cells, 7)
        rows.append({"key": f"violation#{i}", "kind": "violation", "source": "general", "number": number(re.sub(r"\D", "", rule)),
                     "section": "", "title": "", "text": bare(what), "why": bare(cause), "date": day, "rule": rule,
                     "noticed_by": bare(noticed_by), "chat": bare(chat), "fix": bare(fix)})
    return rows


# ---------- data that comes from other tools (not from the notes) ----------
def health_rows() -> list[dict]:
    import health
    return [{"key": r.key, "check": r.check, "status": r.status, "summary": r.summary, "details": r.details,
             "advice": r.advice, "count": r.count, "order": i} for i, r in enumerate(health.checks())]


TEST_RUNNER = "run_tests.py"      # runs the tests itself; not counted as "without a test"
IMPORT = re.compile(r"^\s*(?:import|from)\s+([A-Za-z_]\w*)", re.M)
# The same script does a different job in different events
HOOK_JOBS = {
    ("PreToolUse", "command_guard.py"): "Checks Bash and PowerShell commands before they run; stops or asks about dangerous ones.",
    ("PreToolUse", "write_guard.py"): "Stops the file-writing tools from changing the vault's protected files (raw sources, log.md).",
    ("PreToolUse", "site_guard.py"): "Checks the address before a site is visited and asks for permission.",
    ("PostToolUse", "site_guard.py"): "Scans the page text that came in for attacks such as invisible characters.",
    ("PreToolUse", "agent_gate.py"): "Before an agent starts, checks that task-writing was loaded and the model is written explicitly.",
    ("SessionStart", "session_log.py"): "Prints a reminder of unprocessed session records into the context.",
    ("SessionEnd", "session_log.py"): "Writes the record of the conversation into the session records when the session closes.",
    ("PreCompact", "session_log.py"): "Writes the session record before the context is compacted, so nothing is lost.",
    ("UserPromptSubmit", "search.py"): "Adds the vault notes related to the message to the context.",
    ("Stop", "context_check.py"): "Watches the context: saves to the vault and suggests a new chat before it fills up.",
    ("PreCompact", "context_check.py"): "Tells the compaction what to keep: unfinished work, where it stopped, the next step.",
    ("PostCompact", "context_check.py"): "Writes the compaction summary, secrets masked, into the session records.",
    ("Stop", "dashboard_check.py"): "Reminds a chat that wrote to the vault to update the dashboard when it is out of date.",
}


def system_row(kind: str, row_name: str, **fields) -> dict:
    """The shared shape of the system data set: the page table expects the same fields in every row."""
    row = {"key": f"{kind}:{row_name}:{fields.get('event', '')}", "kind": kind, "name": row_name, "what": "", "event": "",
           "status": "", "lines": 0, "test": 0, "started": "", "finished": "", "evidence": "", "place": "", "date": ""}
    return {**row, **fields}


def testing_files(system: Path) -> dict[str, list[str]]:
    """Module name -> the test files that import it (a module without its own test file may be tested in another)."""
    found: dict[str, list[str]] = {}
    for test in sorted(system.glob("*_test.py")):
        for module in sorted(set(IMPORT.findall(read(test)))):
            found.setdefault(module, []).append(test.name)
    return found


def tool_rows(system: Path) -> list[dict]:
    """_system/*.py (tests left out): first docstring line, line count, the test files that test it."""
    testers = testing_files(system)
    rows = []
    for path in sorted(system.glob("*.py")):
        if path.stem.endswith("_test"):
            continue
        text = read(path)
        try:
            doc = ast.get_docstring(ast.parse(text)) or ""
        except SyntaxError:
            doc = ""
        own = f"{path.stem}_test.py"   # its own test file may test it in a subprocess, without importing it
        by = sorted(set(testers.get(path.stem, [])) | ({own} if (system / own).is_file() else set()))
        rows.append(system_row("tool", path.name, what=doc.strip().split("\n", 1)[0], lines=text.count("\n"),
                               test=int(bool(by)), evidence=", ".join(by), status="runner" if path.name == TEST_RUNNER else ""))
    return rows


def hook_rows() -> list[dict]:
    import health
    try:
        states = [(event, script, "installed" if installed else "missing") for event, script, installed in health.hook_states()]
    except (OSError, ValueError):
        states = [(event, script, "unknown") for event, script in health.EXPECTED_HOOKS]
    return [system_row("hook", script, event=event, status=status, what=HOOK_JOBS.get((event, script), ""))
            for event, script, status in states]


def task_rows() -> list[dict]:
    """The last run of the scheduled tasks; the weekly task without a record is dated by its newest summary."""
    import task_status
    statuses = task_status.read_statuses()
    rows = [system_row("task", task, status=str(s.get("state", "")), started=str(s.get("started_at", "")),
                       finished=str(s.get("finished_at", ""))) for task, s in sorted(statuses.items()) if isinstance(s, dict)]
    if not any(task in statuses for task in WEEKLY_TASKS):
        summaries = weekly_summaries()
        rows.append(system_row("task", WEEKLY_TASKS[0], status="done" if summaries else "",
                               finished=summaries[-1].name[:10] if summaries else ""))
    return rows


def lesson_candidate_rows() -> list[dict]:
    return [system_row("lesson_candidate", f"candidate-{c['number']}", event=f"#{c['number']}", what=bare(c["candidate"]),
                       evidence=bare(c["evidence"]), place=bare(c["place"]), date=c["date"]) for c in lesson_candidates()]


def system_rows() -> list[dict]:
    """Tools, hooks, scheduled tasks and lesson candidates: to follow the system as it grows."""
    rows = tool_rows(vault_path("_system")) + hook_rows() + task_rows() + lesson_candidate_rows()
    return [{**row, "order": i} for i, row in enumerate(rows)]


COST_FIELDS = ("key", "kind", "model", "input", "output", "cache_read", "cache_write", "cost_usd", "unpriced_models", "chat",
               "folder", "agent", "date", "order")


def cost_rows() -> list[dict]:
    """Sessions and subagent runs of the days that ended (cost.py); the folder holds no user name (cost.folder_name)."""
    import cost
    return [{k: r.get(k, "") for k in COST_FIELDS} for r in cost.finished_rows(cost.rows())]


def collect_extras() -> dict:
    """Health, system and cost rows. A tool that fails leaves its data set to the placeholder, the rest still builds."""
    extras = {}
    for dataset, collect in (("health", health_rows), ("system", system_rows), ("cost", cost_rows)):
        try:
            extras[dataset] = collect()
        except Exception as error:   # one broken tool must not stop the dashboard; the error is kept for health.py
            common.log_error(f"dashboard_data {dataset}", error)
            extras[dataset] = []
    return extras


# ---------- build and write ----------
def build_datasets(today: str, extras: dict, trace: dict | None = None) -> dict:
    trace = visible_trace(trace or empty_trace())
    scan = Scan(common.VAULT, today, trace)
    links = scan.links()
    text_of_log = log_text()
    log = log_rows(text_of_log, scan.notes, trace, scan.private)
    agents, runs = agent_rows(scan.private)
    councils = sorted(scan.councils, key=lambda r: (str(r["date"]), r["key"]), reverse=True)
    data = {
        "meta": [{"key": "meta", "language": common.LANGUAGE, "generated": today}],
        "notes": list(scan.notes.values()), "log": log, "versions": scan.versions, "links": links, "tasks": scan.tasks,
        "counts": count_rows(scan, log, text_of_log), "progress": scan.progress, "weekly": weekly_rows(scan.private),
        "pending": pending_rows(scan.notes, scan.private, trace), "agents": agents, "agent_runs": runs,
        "expertise": expertise_rows(scan.private), "skills": skill_rows(scan.private), "discoveries": discovery_rows(scan.private),
        "rules": rule_rows(scan.private), "health": extras.get("health", []), "handoff": handoff_rows(scan.private),
        "system": extras.get("system", []),
        "cost": extras.get("cost", []), "councils": councils,
    }
    return {dataset: [scrubbed(row) for row in data[dataset]] or [placeholder()] for dataset in DATASETS}


def scrubbed(row: dict) -> dict:
    """The last safety net: every text value of every row passes the secret scan, whatever built it."""
    return {key: safe(value) if isinstance(value, str) else value for key, value in row.items()}


def write_outputs(data: dict, folder: Path) -> dict:
    """Writes <dataset>.json and manifest.json ({dataset: sha256}); returns the manifest."""
    folder.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for dataset in DATASETS:
        text = json.dumps(data[dataset], ensure_ascii=False, indent=1)
        atomic_write(folder / f"{dataset}.json", text)
        manifest[dataset] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    atomic_write(folder / "manifest.json", json.dumps(manifest, indent=1))
    return manifest


def output_folder() -> Path:
    return vault_path(*OUTPUT_FOLDER)


def chat_trace(save: bool) -> dict:
    """The updated chat trace; if it cannot be read or locked, the data sets are built without chat names."""
    try:
        return update_chat_trace(save=save)
    except (OSError, ValueError, common.LockUnavailable) as error:
        common.log_error("dashboard_data chat trace", error)
        return empty_trace()


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--dry", action="store_true", help="write nothing into the vault; only build the output files")
    args = parser.parse_args(argv)
    data = build_datasets(date.today().isoformat(), collect_extras(), chat_trace(save=not args.dry))
    write_outputs(data, output_folder())
    for dataset in DATASETS:
        rows = data[dataset]
        print(f"{dataset}: {0 if rows[0].get(PLACEHOLDER) else len(rows)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
