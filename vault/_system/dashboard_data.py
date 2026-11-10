"""Builds the data sets of the dashboard (a claude.ai Data artifact) from the vault.

Only Claude can publish them, with its own Artifact tools (the /dashboard skill); this script only writes JSON files
under `_system/output/dashboard/` (outside git) and a manifest of their SHA-256 values, so the skill uploads only the
data sets that changed.

Privacy filter (rules #17, #18): `me/`, the root `CLAUDE.md`, raw session records (only their number), notes with
`privacy: private` and paths with a sensitive name never reach a data set; neither do links that touch them. Every text
field passes the secret scan; a text with a finding is replaced by HIDDEN_TEXT. A data set is never an empty list (the
dashboard counts an empty file as an error): it gets one placeholder row instead.

Run (from the vault root):  python -I _system/dashboard_data.py
"""
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I does not put the script folder on the path
import common  # noqa: E402
from common import atomic_write, frontmatter, name, sensitive_path, vault_path  # noqa: E402

DATASETS = ("meta", "notes", "log", "links", "tasks", "counts", "progress", "pending", "agents", "agent_runs",
            "expertise", "skills", "rules", "councils", "handoff", "health", "system", "cost")
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
SUMMARY_CHARS, DETAIL_CHARS, LOG_CHARS, PROGRESS_CHARS, HANDOFF_CHARS, RULE_CHARS = 220, 260, 420, 420, 1500, 600
ATTACHMENTS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".pdf"}
OUTPUT_FOLDER = ("_system", "output", "dashboard")

LINK = re.compile(r"\[\[([^\]|#]+)")
LINK_TEXT = re.compile(r"\[\[([^\]|]+)\|?([^\]]*)\]\]")
CODE_BLOCK = re.compile(r"```.*?```", re.S)
CODE_SPAN = re.compile(r"`[^`\n]*`")
TASK = re.compile(r"^\s*- \[( |x|X)\] (.+)$", re.M)
LOG_ENTRY = re.compile(r"^## \[(\d{4}-\d{2}-\d{2})\] (\S+) \| (.+)$", re.M)
PROGRESS_HEADING = re.compile(r"^### (\d{4}-\d{2}-\d{2})(?: \((\d+)\))?[ \t]*(?:[—–-][ \t]*(.*))?$", re.M)
LABELLED_ITEM = re.compile(r"^- \*\*([^*]+?):?\*\*:?\s*(.*)$")
PENDING_LINE = re.compile(r"^\s*- \[( |x|X)\]\s*([PB]-\d+)\s*\|\s*([^|]+?)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*(.+?)\s*(?:\|\s*(.*?))?\s*$")
PENDING_PROJECT = re.compile(r"(?:project|proje):\s*\[\[([^\]|#]+)")
CLOSE_DATE = re.compile(r"✔ (\d{4}-\d{2}-\d{2})")
TABLE_DATE_ROW = re.compile(r"^\|\s*(\d{4}-\d{2}-\d{2})\s*\|(.*)\|\s*$")
RULE_ROW = re.compile(r"^\|\s*(\d+)\s*\|(.+)\|(.*)\|\s*$")
BOLD_START = re.compile(r"^\*\*(.+?)\*\*")
RULE_NUMBER = re.compile(r"#?(\d+)")
AGENT_PAGE = re.compile(r"^(?:agent|ajan)-(.+)$")
SKILL_ROW = re.compile(r"^\|\s*`(/?[\w-]+)`\s*\|(.*)\|\s*$")
LESSON = re.compile(r"^- (\d{4}-\d{2}-\d{2})\b", re.M)

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
LESSONS_SECTION = r"(?:Lessons|Dersler)"
OPTIONAL_RULES_SECTION = re.compile(r"^## (?:Optional rules|İsteğe bağlı kurallar)", re.M)


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
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


def plain(text: str) -> str:
    """[[a|b]] -> b, [[a]] -> a, **x** -> x."""
    text = LINK_TEXT.sub(lambda m: (m.group(2) or m.group(1)).strip(), text)
    return re.sub(r"\*\*|__", "", text).strip()


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


def days_since(day: str, today: str) -> int:
    try:
        return (date.fromisoformat(today) - date.fromisoformat(str(day)[:10])).days
    except ValueError:
        return 0


def table_cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


# ---------- vault layout ----------
def base_folder(local: str) -> str:
    """Local top folder name ('projeler') -> English base name ('projects'); unknown names stay as they are."""
    return next((base for base in TOP_FOLDERS if name(base) == local), local)


def is_private(relative: Path, fields: dict) -> bool:
    return (base_folder(relative.parts[0]) in PRIVATE_FOLDERS and len(relative.parts) > 1
            or relative.stem in PRIVATE_PAGES and len(relative.parts) == 1
            or str(fields.get("privacy", "")).lower() == "private"
            or sensitive_path(relative.as_posix()))


class Scan:
    """One pass over the vault's notes: public notes, link sets, private names and the work rows built from them."""

    def __init__(self, vault: Path, today: str):
        self.vault, self.today = vault, today
        self.notes, self.outgoing, self.private, self.known = {}, {}, set(), set()
        self.tasks, self.progress, self.councils, self.sessions = [], [], [], 0
        self.known |= {p.name for p in vault.rglob("*") if p.suffix.lower() in ATTACHMENTS and not OUT_OF_VAULT & set(p.parts)}
        sessions_folder = (name("inbox"), name("sessions"))
        for path in sorted(vault.rglob("*.md")):
            relative = path.relative_to(vault)
            if relative.parts[0] in OUT_OF_VAULT:
                continue
            if base_folder(relative.parts[0]) in NOT_NOTE_FOLDERS:
                self.known.add(path.stem)   # Obsidian resolves links to these files
                continue
            if relative.parts[:2] == sessions_folder:
                self.sessions += 1
                continue
            self.add(path, relative)

    def add(self, path: Path, relative: Path) -> None:
        fields, body = frontmatter(read(path))
        stem = path.stem
        self.outgoing[stem] = {m.strip() for m in LINK.findall(CODE_SPAN.sub("", CODE_BLOCK.sub("", body)))} - {stem}
        if is_private(relative, fields):
            self.private.add(stem)
            return
        kind = fields.get("type", "") or "other"
        title = re.search(r"^# (.+)$", body, re.M)
        title = title.group(1).strip() if title else stem
        project = link_target(fields.get("project", ""))
        summary, detail = summary_pair(kind, body)
        open_tasks = self.add_tasks(stem, title, kind, project, body)
        tags, aliases = fields.get("tags", []), fields.get("aliases", [])
        self.notes[stem] = {
            "key": stem, "id": stem, "title": safe(title), "type": kind, "status": fields.get("status", ""),
            "project": project, "folder": base_folder(relative.parts[0]) if len(relative.parts) > 1 else "",
            "path": relative.as_posix(),
            "tags": ", ".join(tags) if isinstance(tags, list) else str(tags),
            "aliases": ", ".join(aliases) if isinstance(aliases, list) else str(aliases),
            "summary": safe(summary), "detail": safe(detail),
            "created": fields.get("created", ""), "updated": fields.get("updated", ""),
            "age_days": days_since(fields.get("updated", ""), self.today),
            "words": len(re.findall(r"\w+", body)), "open_tasks": open_tasks,
        }
        if kind == "progress":
            self.progress += progress_rows(project or stem, body)
        if kind == "council":
            self.councils.append(council_row(stem, title, fields))

    def add_tasks(self, stem: str, title: str, kind: str, project: str, body: str) -> int:
        if kind not in WORK_TYPES:
            return 0
        open_count = 0
        for i, (mark, raw) in enumerate(TASK.findall(CODE_BLOCK.sub("", body))):
            text = plain(raw.replace("`", ""))
            if not text:
                continue
            done = 0 if mark == " " else 1
            open_count += 1 - done
            self.tasks.append({"key": f"{stem}#{i}", "note_id": stem, "note": safe(title),
                               "project": project or (stem if kind == "project" else ""), "task": safe(text), "done": done})
        return open_count

    def links(self) -> list[dict]:
        everything = set(self.notes) | self.private | self.known
        rows = []
        for source, targets in self.outgoing.items():
            for target in sorted(targets):
                if source in self.private or target in self.private:
                    continue   # a link that touches a private note stays out
                rows.append({"key": f"{source}>{target}", "source": source, "target": target,
                             "broken": 0 if target in everything else 1})
        for stem, row in self.notes.items():
            row["links_out"] = len(self.outgoing.get(stem, ()))
            row["links_in"] = sum(1 for s, t in self.outgoing.items() if s != stem and stem in t)
            row["orphan"] = 1 if row["links_in"] == 0 and stem not in ROOT_PAGES else 0
        return rows


def progress_rows(project: str, body: str) -> list[dict]:
    """'### 2026-10-10 — Title' entries of the progress log, one row per '- **Label:** text' item."""
    rows = []
    parts = PROGRESS_HEADING.split(section(body, PROGRESS_SECTION))
    for i in range(1, len(parts), 4):
        day, number, title, entry = parts[i], parts[i + 1], (parts[i + 2] or "").strip(), parts[i + 3]
        order = 0
        for line in keep_code_text(entry).splitlines():
            s = line.strip()
            if not s.startswith("- "):
                continue
            m = LABELLED_ITEM.match(s)
            label, text = (m.group(1).strip(), m.group(2)) if m else ("", s[2:])
            text = plain(" ".join(text.split()))
            if not text:
                continue
            order += 1
            rows.append({"key": f"{project}:{day}{f'({number})' if number else ''}:{order}", "project": project,
                         "date": day, "title": safe(title), "label": label, "text": safe(shorten(text, PROGRESS_CHARS)),
                         "order": order})
    return rows


def council_row(stem: str, title: str, fields: dict) -> dict:
    agents = fields.get("agents", [])
    return {"key": stem, "id": stem, "title": safe(title), "mode": fields.get("mode", ""),
            "agents": ", ".join(agents) if isinstance(agents, list) else str(agents),
            "result": fields.get("result", ""), "calls": fields.get("calls", ""), "opus": fields.get("opus", ""),
            "project": link_target(fields.get("project", "")), "date": fields.get("created", "")}


# ---------- records ----------
def log_rows(notes: dict) -> list[dict]:
    archive = vault_path("archive", "log")
    texts = [read(p) for p in sorted(archive.glob("*.md"))] if archive.is_dir() else []
    text = "\n".join(texts + [read(vault_path("log.md"))])
    projects = {stem for stem, n in notes.items() if n["type"] == "project"}
    rows = []
    parts = LOG_ENTRY.split(text)
    for i in range(1, len(parts), 4):
        day, operation, title, body = parts[i], parts[i + 1], parts[i + 2].strip(), parts[i + 3]
        hidden = operation in HIDDEN_OPERATIONS
        linked = [t.strip() for t in LINK.findall(title + "\n" + body)]
        rows.append({"key": str(len(rows) + 1), "date": day, "operation": operation,
                     "title": "" if hidden else safe(plain(title)),
                     "detail": "" if hidden else safe(first_sentences(body, LOG_CHARS)),
                     "project": "" if hidden else next((t for t in linked if t in projects), "")})
    return rows


def pending_rows(private: set) -> list[dict]:
    """Pending items; a link to a private note is left empty, so its name does not travel either."""
    rows = []
    for line in read(vault_path("inbox", "pending.md")).splitlines():
        m = PENDING_LINE.match(line)
        if not m:
            continue
        mark, number, kind, day, text, rest = m.groups()
        rest = rest or ""
        done = mark != " "
        closed = CLOSE_DATE.search(rest)
        project = PENDING_PROJECT.search(rest)
        source = link_target(rest.split("|")[0]) if "[[" in rest.split("|")[0] else ""
        project = project.group(1).strip() if project else ""
        rows.append({"key": number, "id": number, "kind": kind, "date": day, "text": safe(plain(text)),
                     "source": "" if source in private else source,
                     "project": "" if project in private else project,
                     "status": "done" if done else "held" if kind == "on-hold" else "open",
                     "closed": closed.group(1) if done and closed else ""})
    return rows


def handoff_rows() -> list[dict]:
    from records import HANDOFF_HEADING, handoff_cards
    rows = []
    for session, card in handoff_cards(read(vault_path("inbox", "handoff.md"))):
        heading = HANDOFF_HEADING.match(card)
        body = card.split("\n", 1)[1] if "\n" in card else ""
        rows.append({"key": f"{heading.group(1)}-{heading.group(2)}-{session}", "date": heading.group(1),
                     "time": heading.group(2), "label": safe(heading.group(3)), "session": session,
                     "text": safe_lines(shorten(body.strip(), HANDOFF_CHARS))})
    return rows


def agent_rows() -> tuple[list[dict], list[dict]]:
    runs = []
    folder = vault_path("knowledge", "agents-log")
    for page in sorted(folder.glob("*.md")) if folder.is_dir() else []:
        m = AGENT_PAGE.match(page.stem)
        if not m:
            continue
        for i, line in enumerate(read(page).splitlines()):
            row = TABLE_DATE_ROW.match(line)
            if not row:
                continue
            cells = table_cells(row.group(2)) + [""] * 6
            mode, model, job, result, _chat, project = cells[:6]
            runs.append({"key": f"{m.group(1)}:{i}", "agent": m.group(1), "date": row.group(1), "mode": mode,
                         "model": model, "job": safe(plain(job)), "result": safe(plain(result)),
                         "project": link_target(project)})
    agents = []
    for path in sorted(vault_path("_system", "agents").glob("*.md")):
        fields, _ = frontmatter(read(path))
        own = [r for r in runs if r["agent"] == path.stem]
        agents.append({"key": path.stem, "name": fields.get("name", path.stem), "description": safe(fields.get("description", "")),
                       "model": fields.get("model", ""), "color": fields.get("color", ""), "runs": len(own),
                       "last_run": max((r["date"] for r in own), default="")})
    return agents, runs


def expertise_rows() -> list[dict]:
    rows = []
    for skill in sorted(vault_path("_system", "skills").glob("*/SKILL.md")):
        if not re.match(r"^(?:expert|uzman)-", skill.parent.name):
            continue
        fields, body = frontmatter(read(skill))
        lessons = LESSON.findall(section(body, LESSONS_SECTION))
        rows.append({"key": skill.parent.name, "name": skill.parent.name, "description": safe(fields.get("description", "")),
                     "lessons": len(lessons), "last_lesson": max(lessons, default="")})
    return rows


def skill_rows() -> list[dict]:
    rows = []
    for line in read(vault_path("_system", "skills", "skills-registry.md")).splitlines():
        m = SKILL_ROW.match(line)
        if not m:
            continue
        skill = m.group(1)
        cells = table_cells(m.group(2)) + ["", "", ""]
        kind = "workflow" if skill.startswith("/") else "expertise" if re.match(r"^(?:expert|uzman)-", skill) else "method"
        uses = re.sub(r"\D", "", cells[1])
        rows.append({"key": skill, "name": skill, "kind": kind, "description": safe(plain(cells[0])),
                     "uses": int(uses) if uses else 0, "last_used": cells[2] if cells[2] not in ("—", "-") else ""})
    return rows


def rule_rows() -> list[dict]:
    text = read(vault_path("rules", "general-rules.md"))
    optional_at = (OPTIONAL_RULES_SECTION.search(text) or re.search(r"\Z", text)).start()
    violations = {}
    for line in read(vault_path("rules", "rule-violations.md")).splitlines():
        row = TABLE_DATE_ROW.match(line)
        number = RULE_NUMBER.search(table_cells(row.group(2))[0]) if row else None
        if number:
            violations[number.group(1)] = violations.get(number.group(1), 0) + 1
    rows = []
    offset = 0
    for line in text.splitlines(keepends=True):
        m = RULE_ROW.match(line.rstrip("\n"))
        if m:
            cell = m.group(2).strip()
            bold = BOLD_START.match(cell)
            rows.append({"key": m.group(1), "number": int(m.group(1)),
                         "title": plain(bold.group(1)).rstrip(".") if bold else shorten(plain(cell), 80),
                         "text": shorten(plain(cell[bold.end():] if bold else cell), RULE_CHARS),
                         "why": shorten(plain(m.group(3)), RULE_CHARS), "optional": offset >= optional_at,
                         "violations": violations.get(m.group(1), 0)})
        offset += len(line)
    return rows


def count_rows(scan: Scan, log: list[dict]) -> list[dict]:
    stale = sum(1 for n in scan.notes.values() if n["status"] == "active" and n["type"] != "entry" and n["age_days"] > STALE_DAYS)
    last_lint = max((r["date"] for r in log if r["operation"] == "lint"), default="")
    return [{"key": "sessions_waiting", "value": scan.sessions, "text": ""},
            {"key": "stale_active", "value": stale, "text": ""},
            {"key": "private_notes", "value": len(scan.private), "text": ""},
            {"key": "last_maintenance", "value": 0, "text": last_lint},
            {"key": "data_date", "value": 0, "text": scan.today}]


# ---------- data that comes from other tools (not from the notes) ----------
def health_rows() -> list[dict]:
    import health
    return [{"key": r.key, "check": r.check, "status": r.status, "summary": safe(r.summary), "advice": safe(r.advice)}
            for r in health.checks()]


def system_rows() -> list[dict]:
    system = vault_path("_system")
    tools = sorted(p for p in system.glob("*.py") if not p.stem.endswith("_test"))
    rows = [{"key": f"tool:{p.stem}", "kind": "tool", "name": p.stem, "event": "", "status": "",
             "has_test": int((system / f"{p.stem}_test.py").is_file()), "date": ""} for p in tools]
    rows += hook_rows(system)
    import task_status
    for task, status in sorted(task_status.read_statuses().items()):
        rows.append({"key": f"task:{task}", "kind": "task", "name": task, "event": "", "status": str(status.get("status", "")),
                     "has_test": 0, "date": str(status.get("finished") or status.get("started") or "")[:16]})
    return rows


def hook_rows(system: Path) -> list[dict]:
    """Vault hooks in ~/.claude/settings.json: event and script only (a full command holds the user's paths)."""
    try:
        settings = json.loads((Path.home() / ".claude" / "settings.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    marker = system.as_posix().lower()
    rows = []
    for event, groups in (settings.get("hooks") or {}).items():
        for group in groups if isinstance(groups, list) else []:
            for hook in group.get("hooks", []) if isinstance(group, dict) else []:
                command = str(hook.get("command", "")).replace("\\", "/")
                script = re.search(r"/([\w-]+\.py)\"?\s*(\w*)", command)
                if marker in command.lower() and script:
                    label = " ".join(filter(None, script.groups()))
                    rows.append({"key": f"hook:{event}:{label}", "kind": "hook", "name": label, "event": event,
                                 "status": "", "has_test": 0, "date": ""})
    return rows


def cost_rows() -> list[dict]:
    import cost
    keep = ("key", "model", "date", "cost_usd")   # no folder or chat title: they can hold the user's name (#18)
    return [{k: r.get(k, "") for k in keep} for r in cost.rows()]


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
def build_datasets(today: str, extras: dict) -> dict:
    scan = Scan(common.VAULT, today)
    links = scan.links()
    log = log_rows(scan.notes)
    agents, runs = agent_rows()
    data = {
        "meta": [{"key": "meta", "language": common.LANGUAGE, "generated": today}],
        "notes": list(scan.notes.values()), "log": log, "links": links, "tasks": scan.tasks,
        "counts": count_rows(scan, log), "progress": scan.progress, "pending": pending_rows(scan.private),
        "agents": agents, "agent_runs": runs, "expertise": expertise_rows(), "skills": skill_rows(),
        "rules": rule_rows(), "councils": scan.councils, "handoff": handoff_rows(),
        "health": extras.get("health", []), "system": extras.get("system", []), "cost": extras.get("cost", []),
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


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    data = build_datasets(date.today().isoformat(), collect_extras())
    write_outputs(data, output_folder())
    for dataset in DATASETS:
        rows = data[dataset]
        print(f"{dataset}: {0 if rows[0].get(PLACEHOLDER) else len(rows)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
