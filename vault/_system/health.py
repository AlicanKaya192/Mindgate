"""Second brain health check: are the parts of the system installed and consistent?

Modes (from the vault root):
  health.py                   quick checks (~1-2 s), written as a list
  health.py --full            also the secret scan, the security scan, the search hit rate and every test
  health.py --json            writes the results as JSON
  health.py --save-baseline   lowers the monotonic baseline to today's counts (never raises it)

Exit code: 1 when any check has the status "error". Apart from `--save-baseline` nothing is changed; the script only
reads and reports. Optional dashboard: not included in v1.

Folder and file names come from `common.name()` / `vault_path()`; paths are built from `VAULT` at call time, so the
tests can point the checks at a temporary folder.
"""
import argparse
import io
import json
import os
import re
import subprocess
import sys
from contextlib import redirect_stdout
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the -I flag does not add the script folder to the path
import common  # noqa: E402
import install_instructions  # noqa: E402
import search_eval  # noqa: E402
import task_status  # noqa: E402
from common import CONFIG_FILE, HOOK_ERRORS, frontmatter, load_config, name  # noqa: E402
from records import HANDOFF_CARD_LIMIT, LEARNED_OPERATIONS  # noqa: E402
from secret_scan import HOOK_SIGNATURE  # noqa: E402

VAULT = common.VAULT
CLAUDE = Path.home() / ".claude"
PY = str(common.CONFIG.get("python") or ("py -3" if os.name == "nt" else "python3"))
VALID_TYPE = {"project", "progress", "idea", "problem", "decision", "experiment", "model-card", "data-card", "concept",
              "source", "research", "profile", "rule", "draft", "session", "entry", "person", "council"}
VALID_STATUS = {"active", "paused", "done", "archived", "open", "solved", "draft", "accepted", "proposed", "superseded",
                "ready", "published"}
VALID_FIELD = {"source_type": {"stated", "inferred", "verified"}, "privacy": {"private"}}
# Not scanned as notes: system folders, raw sources and `.claude` (worktree copies of the vault)
NOT_NOTES = {name("_templates"), name("_system"), name("sources"), ".obsidian", ".git", ".trash", ".claude"}
NOT_FILES = {".git", ".claude"}
SESSIONS_FOLDER = (name("inbox"), name("sessions"))
# Kept by the write guard; a broken link inside them cannot be fixed. Archives only grow, scripts read them whole.
FIXED_ARCHIVES = {(name("archive"), name("log")), (name("archive"), name("pending"))}
ROOT_PAGES = {"index", "log", "CLAUDE"}
EXPECTED_HOOKS = [
    ("PreToolUse", "command_guard.py"), ("PreToolUse", "write_guard.py"), ("PreToolUse", "site_guard.py"),
    ("PreToolUse", "agent_gate.py"), ("PostToolUse", "site_guard.py"),
    ("SessionStart", "session_log.py"), ("SessionEnd", "session_log.py"), ("PreCompact", "session_log.py"),
    ("UserPromptSubmit", "search.py"),
    ("Stop", "context_check.py"), ("PreCompact", "context_check.py"), ("PostCompact", "context_check.py"),
]
RULE_START = "2026-10-14"            # the Learned line and the closing evidence are required in entries after this date
PENDING_OLD_DAYS = 14
SESSION_OLD_DAYS = 2
REMIND_LIMIT = 9500                  # Claude Code cuts hook context longer than ~10,000 characters
HOOK_ERROR_DAYS = 7
CONTEXT_MODES = {"normal", "economy", "off"}
LINK = re.compile(r"\[\[([^\]|#]+)")
CODE = re.compile(r"```.*?```|`[^`\n]*`", re.S)
LOG_HEADING = re.compile(r"^## \[(\d{4}-\d{2}-\d{2})\] (\S+) \| .+$")
PENDING_LINE = re.compile(r"^- \[( |x|X)\] ([PB]-\d+) \|([^|]*)\|\s*(\d{4}-\d{2}-\d{2})")
TRIED_HEADINGS = ("Tried solutions", "Attempted solutions", "Denenen çözümler")
MARKER_HEADINGS = ("Regression marker", "Regresyon işaretçisi")


@dataclass
class Result:
    key: str
    check: str
    status: str          # ok | warning | error
    summary: str
    details: str = ""
    advice: str = ""
    count: int | None = None   # the number the monotonic baseline follows


def first(items: list[str], n: int = 8) -> str:
    return ", ".join(items[:n]) + (f" … (+{len(items) - n})" if len(items) > n else "")


def vpath(*parts: str) -> Path:
    """Like common.vault_path(), but from the current VAULT (tests replace it)."""
    path = VAULT
    for part in parts:
        for segment in part.split("/"):
            if segment:
                path = path / name(segment)
    return path


def system_dir() -> Path:
    return vpath("_system")


def read_config() -> dict:
    """config.json; OSError/ValueError if it cannot be read or is not an object."""
    data, error = load_config(CONFIG_FILE)
    if error:
        raise ValueError(error)
    return data


# ---------- installation ----------
def hook_states() -> list[tuple[str, str, bool]]:
    """(event, script, installed in settings.json) for every expected hook. OSError/ValueError if settings.json fails."""
    settings = json.loads((CLAUDE / "settings.json").read_text(encoding="utf-8")).get("hooks", {})
    states = []
    for event, script in EXPECTED_HOOKS:
        commands = [" ".join([h.get("command", ""), *h.get("args", [])]) for g in settings.get(event, []) for h in g.get("hooks", [])]
        states.append((event, script, any(script in c for c in commands)))
    return states


def hooks() -> Result:
    try:
        states = hook_states()
    except (OSError, ValueError) as error:
        return Result("hooks", "Hooks", "error", f"settings.json could not be read: {type(error).__name__}",
                      advice="install the hooks from setup/hooks.template.json")
    missing = [f"{event}:{script}" for event, script, installed in states if not installed]
    absent = sorted({s for _, s in EXPECTED_HOOKS if not (system_dir() / s).is_file()})
    if missing or absent:
        return Result("hooks", "Hooks", "error", f"{len(missing)} hooks missing, {len(absent)} scripts not found",
                      first(missing + absent), "compare the hooks section of ~/.claude/settings.json with setup/hooks.template.json")
    return Result("hooks", "Hooks", "ok", f"{len(EXPECTED_HOOKS)} hooks installed, scripts in place")


def same_file(a: Path, b: Path) -> bool:
    try:
        return a.resolve().samefile(b.resolve())
    except OSError:
        return False


def compact_threshold() -> Result:
    """Is the automatic compaction threshold (settings.json env) equal to config.json → context_window.compact_percent."""
    try:
        env = json.loads((CLAUDE / "settings.json").read_text(encoding="utf-8")).get("env", {})
        expected = str(read_config()["context_window"]["compact_percent"])
    except (OSError, ValueError, KeyError) as error:
        return Result("compact", "Automatic compaction threshold", "error", f"setting could not be read: {type(error).__name__}")
    installed = env.get("CLAUDE_AUTOCOMPACT_PCT_OVERRIDE")
    if installed == expected:
        return Result("compact", "Automatic compaction threshold", "ok", f"the context is compacted at {installed}%")
    return Result("compact", "Automatic compaction threshold", "warning", f"settings.json: {installed or 'none'}, config.json: {expected}",
                  advice="set ~/.claude/settings.json → env → CLAUDE_AUTOCOMPACT_PCT_OVERRIDE to the config.json value")


def links() -> Result:
    skills_dir = system_dir() / name("skills")
    wrong = [d.name for d in sorted(skills_dir.iterdir()) if (d / "SKILL.md").is_file()
             and not same_file(CLAUDE / "skills" / d.name / "SKILL.md", d / "SKILL.md")] if skills_dir.is_dir() else []
    if not same_file(CLAUDE / "agents", system_dir() / name("agents")):
        wrong.append("agents folder")
    if wrong:
        return Result("links", "Skill and agent links", "error", f"{len(wrong)} links missing or wrong",
                      first(wrong), "link the folders into ~/.claude (Windows: mklink /J; elsewhere: ln -s), see skill-writing")
    return Result("links", "Skill and agent links", "ok", "every skill and agent is linked to Claude Code")


def precommit() -> Result:
    hook = VAULT / ".git" / "hooks" / "pre-commit"
    if hook.is_file() and HOOK_SIGNATURE in hook.read_text(encoding="utf-8", errors="replace"):
        return Result("precommit", "Secret scan before commit", "ok", "pre-commit hook installed")
    return Result("precommit", "Secret scan before commit", "error", "no pre-commit hook",
                  advice=f"{PY} -I {name('_system')}/secret_scan.py --install")


def settings() -> Result:
    try:
        mode = read_config()["context"]["mode"]
    except (OSError, ValueError, KeyError, TypeError) as error:
        return Result("settings", "Settings", "error", f"config.json could not be read: {type(error).__name__}")
    return Result("settings", "Settings", "ok" if mode in CONTEXT_MODES else "error", f"automatic context: {mode}")


# ---------- notes ----------
def read_notes() -> dict[str, tuple[Path, dict, str]]:
    notes = {}
    for path in VAULT.rglob("*.md"):
        relative = path.relative_to(VAULT)
        if relative.parts[0] in NOT_NOTES or relative.parts[:2] == SESSIONS_FOLDER:
            continue
        fields, body = frontmatter(path.read_text(encoding="utf-8"))
        notes[path.stem] = (relative, fields, body)
    return notes


def fields(notes: dict) -> Result:
    problems = []
    for note, (_, fm, _) in sorted(notes.items()):
        if note in ROOT_PAGES and not fm:
            continue
        if not fm:
            problems.append(f"{note}: no frontmatter")
            continue
        if fm.get("type") not in VALID_TYPE:
            problems.append(f"{note}: type '{fm.get('type', '')}'")
        if fm.get("status") and fm["status"] not in VALID_STATUS:
            problems.append(f"{note}: status '{fm['status']}'")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(fm.get("updated", ""))):
            problems.append(f"{note}: updated '{fm.get('updated', '')}'")
        for field, valid in VALID_FIELD.items():
            if fm.get(field) and fm[field] not in valid:
                problems.append(f"{note}: {field} '{fm[field]}'")
    return Result("fields", "Note fields (frontmatter)", "warning" if problems else "ok",
                  f"{len(problems)} problems" if problems else f"{len(notes)} notes valid",
                  first(problems), "fix them as in vault CLAUDE.md §5" if problems else "", count=len(problems))


ATTEMPT_ROW = re.compile(r"^\|\s*\d{4}-\d{2}-\d{2}\s*\|.*\|$", re.M)
MARKER = re.compile(r"^- `([^`]+)` → `([^`]+)`", re.M)


def section(body: str, headings: tuple[str, ...]) -> str:
    alternatives = "|".join(re.escape(h) for h in headings)
    m = re.search(rf"^## (?:{alternatives})[^\n]*\n(.*?)(?=^## |\Z)", body, re.M | re.S)
    return m.group(1) if m else ""


def problem_history(notes: dict) -> Result:
    """Rule #38: every attempt stays in the problem note with its result; a solved note has at least one 'worked' row."""
    gaps = []
    for note, (_, fm, body) in sorted(notes.items()):
        if fm.get("type") != "problem" or str(fm.get("updated", "")) < RULE_START:
            continue
        rows = ATTEMPT_ROW.findall(section(body, TRIED_HEADINGS))
        if not rows:
            gaps.append(f"{note}: Tried solutions table missing or empty")
        elif fm.get("status") == "solved" and not any("✔" in r for r in rows):
            gaps.append(f"{note}: solved but no 'worked' (✔) row")
    if gaps:
        return Result("problem_history", "Problem solution history (#38)", "warning", f"{len(gaps)} problem notes incomplete",
                      first(gaps), "write every attempt with its result in the table; do not delete an old solution (/problem)",
                      count=len(gaps))
    return Result("problem_history", "Problem solution history (#38)", "ok", "attempt history complete in problem notes", count=0)


def regression_markers(notes: dict) -> Result:
    """#38: is the distinctive string a fix left in the code still there? If not, the fix may have been reverted silently."""
    markers = [(note, path, text) for note, (_, fm, body) in sorted(notes.items()) if fm.get("type") == "problem"
               for path, text in MARKER.findall(section(body, MARKER_HEADINGS))]
    lost = []
    for note, path, text in markers:
        try:
            if text not in Path(path).expanduser().read_text(encoding="utf-8", errors="replace"):
                lost.append(f"{note}: marker not in {path}")
        except OSError as error:   # moved, deleted or locked file: the check must not crash, it warns
            lost.append(f"{note}: {path} could not be read ({type(error).__name__})")
    if lost:
        return Result("regression", "Regression markers (#38)", "warning", f"{len(lost)}/{len(markers)} markers lost",
                      first(lost), "check whether the fix was reverted; if the file moved, update the path in the note",
                      count=len(lost))
    return Result("regression", "Regression markers (#38)", "ok", f"{len(markers)} markers in place", count=0)


BASELINE_KEYS = ("fields", "problem_history", "broken_links", "orphans", "index")


def baseline_file() -> Path:
    return system_dir() / "health_baseline.json"


def tracked_counts(results: list[Result]) -> dict[str, int]:
    return {r.key: r.count for r in results if r.key in BASELINE_KEYS and r.count is not None}


def read_baseline() -> dict[str, int]:
    try:
        return json.loads(baseline_file().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def baseline_check(results: list[Result]) -> Result:
    """Monotonic baseline: tracked counts may only go down; a count above the baseline is a regression."""
    baseline = read_baseline()
    if not baseline:
        return Result("baseline", "Monotonic baseline", "warning", "baseline file missing or unreadable",
                      advice="health.py --save-baseline")
    now = tracked_counts(results)
    higher = [f"{k}: {baseline[k]} → {n}" for k, n in now.items() if k in baseline and n > baseline[k]]
    lower = [f"{k}: {baseline[k]} → {n}" for k, n in now.items() if k in baseline and n < baseline[k]]
    if higher:
        return Result("baseline", "Monotonic baseline", "warning", f"{len(higher)} counts above the baseline", first(higher),
                      "fix the new problem; the baseline is raised only on purpose and by hand")
    return Result("baseline", "Monotonic baseline", "ok", "no count above the baseline", first(lower),
                  "lower the baseline with health.py --save-baseline" if lower else "")


def save_baseline(results: list[Result]) -> dict[str, int]:
    """Lowers the baseline to today's counts; a new key is added, no existing count is raised."""
    baseline = read_baseline()
    new = {k: min(n, baseline.get(k, n)) for k, n in tracked_counts(results).items()}
    baseline_file().parent.mkdir(parents=True, exist_ok=True)
    baseline_file().write_text(json.dumps({**baseline, **new}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return new


def existing_names() -> set[str]:
    files = [p for p in VAULT.rglob("*") if p.is_file() and not set(p.relative_to(VAULT).parts) & NOT_FILES]
    return {p.stem for p in files} | {p.name for p in files}


def is_fixed(relative: Path) -> bool:
    return tuple(relative.parts[:2]) in FIXED_ARCHIVES


def link_checks(notes: dict) -> tuple[Result, Result]:
    names = existing_names()
    broken, incoming = [], {note: 0 for note in notes}
    for note, (relative, _, body) in notes.items():
        for target in {t.strip() for t in LINK.findall(CODE.sub("", body))}:
            if target not in names:
                if not is_fixed(relative):
                    broken.append(f"{note} → {target}")
            elif target in incoming and target != note:
                incoming[target] += 1
    orphans = sorted(note for note, n in incoming.items() if n == 0 and note not in ROOT_PAGES)
    b = Result("broken_links", "Broken links", "warning" if broken else "ok", f"{len(broken)} broken links",
               first(sorted(broken)), "create the target note or turn the link into plain text" if broken else "",
               count=len(broken))
    o = Result("orphans", "Orphan notes", "warning" if orphans else "ok", f"{len(orphans)} orphan notes",
               first(orphans), "link them from the related entry page or project (§6)" if orphans else "", count=len(orphans))
    return b, o


def index_missing(notes: dict) -> Result:
    path = VAULT / "index.md"
    listed = set(LINK.findall(path.read_text(encoding="utf-8"))) if path.is_file() else set()
    missing = sorted(note for note, (_, fm, _) in notes.items()
                     if note not in listed and note not in ROOT_PAGES and fm.get("type") != "session")
    return Result("index", "index.md coverage", "warning" if missing else "ok", f"{len(missing)} notes not in the index",
                  first(missing), "add a line to the matching category in index.md (not to the automatic block)" if missing else "",
                  count=len(missing))


# ---------- records ----------
def pending() -> Result:
    path = vpath("inbox", "pending.md")
    if not path.is_file():
        return Result("pending", "Pending items", "warning", f"{name('pending.md')} not found")
    rows = [(m, line) for line in path.read_text(encoding="utf-8").splitlines() if (m := PENDING_LINE.match(line))]
    numbers = [m.group(2) for m, _ in rows]
    double = sorted({n for n in numbers if numbers.count(n) > 1})
    open_items = [m for m, _ in rows if not m.group(1).strip()]
    old = [m.group(2) for m in open_items if m.group(3).strip() != "on-hold"
           and (date.today() - date.fromisoformat(m.group(4))).days > PENDING_OLD_DAYS]
    no_evidence = [m.group(2) for m, line in rows if m.group(1).strip()
                   and (c := re.search(r"✔\s*(\d{4}-\d{2}-\d{2})", line)) and c.group(1) >= RULE_START and "evidence:" not in line]
    problems = ([f"duplicate number: {first(double)}"] if double else []) + \
               ([f"closed without evidence: {first(no_evidence)}"] if no_evidence else [])
    status = "error" if double else "warning" if (no_evidence or old) else "ok"
    summary = f"{len(open_items)} open" + (f", {len(old)} of them older than {PENDING_OLD_DAYS} days" if old else "")
    return Result("pending", "Pending items", status, summary, "; ".join(problems + ([f"old: {first(old)}"] if old else [])),
                  "close with records.py pending close … --evidence; fix the duplicate number" if problems else "")


def log_check() -> Result:
    path = VAULT / "log.md"
    if not path.is_file():
        return Result("log", "log.md", "warning", "log.md not found")
    lines = path.read_text(encoding="utf-8").splitlines()
    bad = [s[:60] for s in lines if s.startswith("## [") and not LOG_HEADING.match(s)]
    entries, current = [], None
    for s in lines:
        m = LOG_HEADING.match(s)
        if m:
            current = [m.group(1), m.group(2), s, False]
            entries.append(current)
        elif current and s.lstrip("- ").startswith("Learned:"):
            current[3] = True
    no_learned = [e[2][3:60] for e in entries if e[0] >= RULE_START and e[1] in LEARNED_OPERATIONS and not e[3]]
    status = "error" if bad else "warning" if no_learned else "ok"
    summary = f"{len(entries)} entries" + (f", {len(bad)} bad headings" if bad else "") + \
        (f", {len(no_learned)} entries without 'Learned:'" if no_learned else "")
    return Result("log", "log.md", status, summary, first(bad + no_learned, 5),
                  "add a '- Learned: … / none' line to the entry" if no_learned else "")


def handoff() -> Result:
    path = vpath("inbox", "handoff.md")
    if not path.is_file():
        return Result("handoff", "Handoff cards", "warning", "no handoff card yet",
                      advice="at the end of a meaningful session: records.py handoff write")
    cards = re.split(r"(?m)^(?=## \d{4}-\d{2}-\d{2} \d{2}:\d{2} · )", path.read_text(encoding="utf-8"))[1:]
    long = [c.splitlines()[0][3:40] for c in cards if len(c) > HANDOFF_CARD_LIMIT + 120]
    return Result("handoff", "Handoff cards", "warning" if long else "ok", f"{len(cards)} cards" + (f", {len(long)} long" if long else ""),
                  first(long), "shorten the card, link the details to a note" if long else "")


def session_records() -> Result:
    records = sorted(vpath("inbox", "sessions").glob("*.md"))
    old = [r.name for r in records if (datetime.now() - datetime.fromtimestamp(r.stat().st_mtime)).days > SESSION_OLD_DAYS]
    return Result("sessions", "Unprocessed session records", "warning" if old else "ok", f"{len(records)} records",
                  first(old), "process the records: /keep-records" if old else "")


def tasks() -> Result:
    statuses = task_status.read_statuses()
    if not statuses:
        return Result("tasks", "Scheduled tasks", "ok", "no status record")
    stuck = []
    for task, record in statuses.items():
        try:
            if record.get("state") == task_status.RUNNING and \
                    datetime.now() - datetime.fromisoformat(record["started_at"]) > task_status.STUCK_AFTER:
                stuck.append(task)
        except (AttributeError, KeyError, TypeError, ValueError):
            stuck.append(task)
    return Result("tasks", "Scheduled tasks", "warning" if stuck else "ok", f"stuck: {first(stuck)}" if stuck else "no stuck task",
                  advice="the task stopped halfway; task_status.py finish <name>" if stuck else "")


def remind_size() -> Result:
    import session_log
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        session_log.remind({"source": "startup", "cwd": str(VAULT)})
    size = len(buffer.getvalue())
    return Result("remind", "Session-start context size", "warning" if size > REMIND_LIMIT else "ok",
                  f"{size} characters (limit {REMIND_LIMIT})",
                  advice="shorten the rule summary or the number of handoff cards" if size > REMIND_LIMIT else "")


LINE_LIMIT, BYTE_LIMIT = 1500, 150_000   # the read tool cuts at 2,000 lines; growing files are rotated


def file_sizes(notes: dict) -> Result:
    """Notes so large that reading them whole gets cut (log and pending are rotated by records.py)."""
    large = [f"{note} ({text.count(chr(10))} lines)" for note, (path, _, text) in sorted(notes.items())
             if not is_fixed(path)
             and (text.count(chr(10)) > LINE_LIMIT or (VAULT / path).stat().st_size > BYTE_LIMIT)]
    return Result("size", "Large files", "warning" if large else "ok",
                  f"{len(large)} notes over {LINE_LIMIT} lines or {BYTE_LIMIT // 1000} KB" if large else "no note over the limit",
                  first(large), "split the note (with links); log.md is rotated by records.py at the next log write" if large else "")


def instructions() -> Result:
    """Is the installed global instructions file the same as the master copy in the vault."""
    state = install_instructions.status()
    messages = {install_instructions.SAME: "installed copy matches the master copy",
                install_instructions.DIFFERENT: "~/.claude/CLAUDE.md differs from the master copy",
                install_instructions.NOT_INSTALLED: "~/.claude/CLAUDE.md does not exist",
                install_instructions.NO_SOURCE: "master copy not found"}
    advice = {install_instructions.SAME: "",
              install_instructions.DIFFERENT: "an existing file is never overwritten: see the difference with "
                                              "install_instructions.py status, then run the installer again with the user's approval",
              install_instructions.NOT_INSTALLED: "install_instructions.py install --force-new",
              install_instructions.NO_SOURCE: f"restore {name('_system')}/{name('instructions')}/global-CLAUDE.md from git"}
    return Result("instructions", "Global instructions version", "ok" if state == install_instructions.SAME else "warning",
                  messages.get(state, state), advice=advice.get(state, ""))


SEARCH_THRESHOLD = 0.8                   # hit@3


def search_hit_rate() -> Result:
    """search.py retrieval hit rate: is the expected note in the top 3 for the fixed question set."""
    try:
        summary, details = search_eval.measure()
    except (OSError, ValueError, KeyError) as error:
        return Result("search", "Search hit rate", "warning", f"measurement could not run: {type(error).__name__}",
                      advice=f"check {name('_system')}/search_exam.json")
    missed = [d["question"][:40] for d in details if not d["rank"] or d["rank"] > 3]
    good = summary["hit@3"] >= SEARCH_THRESHOLD
    return Result("search", "Search hit rate", "ok" if good else "warning",
                  f"hit@3 {summary['hit@3']}, MRR {summary['mrr']} ({summary['questions']} questions)", first(missed, 5),
                  "" if good else "look at the missed questions: a note title, alias or link may be missing; "
                                  "replace the sample questions with questions about your own notes")


def hook_errors() -> Result:
    if not HOOK_ERRORS.is_file():
        return Result("hook_errors", "Hook errors", "ok", "no recorded error")
    since = (datetime.now() - timedelta(days=HOOK_ERROR_DAYS)).strftime("%Y-%m-%d")
    recent = [s for s in HOOK_ERRORS.read_text(encoding="utf-8").splitlines() if s[:10] >= since]
    return Result("hook_errors", "Hook errors", "warning" if recent else "ok", f"{len(recent)} errors in the last {HOOK_ERROR_DAYS} days",
                  first([s.split("\t", 1)[-1][:90] for s in recent[-5:]], 5),
                  f"find the root cause with debugging ({name('_system')}/{name('output')}/hook_errors.log)" if recent else "")


def leftover_files() -> Result:
    leftovers = [p.relative_to(VAULT).as_posix() for p in VAULT.rglob(".*.tmp")
                 if not set(p.relative_to(VAULT).parts) & NOT_FILES]
    return Result("leftovers", "Temporary files left behind", "warning" if leftovers else "ok", f"{len(leftovers)} files",
                  first(leftovers), "show them to the user; deleting needs permission (#22)" if leftovers else "")


def git_state() -> Result:
    def git(*a):
        return subprocess.run(["git", "-C", str(VAULT), *a], capture_output=True, text=True, encoding="utf-8",
                              errors="replace", stdin=subprocess.DEVNULL).stdout
    try:
        changed = [s for s in git("status", "--porcelain").splitlines() if not s.endswith(".obsidian/graph.json")]
        ahead = git("rev-list", "--count", "@{u}..HEAD").strip() or "0"
    except OSError as error:
        return Result("git", "Git", "warning", f"git could not run: {type(error).__name__}")
    status = "warning" if changed or ahead != "0" else "ok"
    return Result("git", "Git", status, f"{len(changed)} uncommitted changes, {ahead} unpushed commits",
                  first([s[3:] for s in changed]),
                  "commit and push (do not touch half-done files of another chat)" if status != "ok" else "")


# ---------- full ----------
def command_result(key: str, check: str, command: list[str], advice: str) -> Result:
    c = subprocess.run([sys.executable, "-I", "-B", *command], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=VAULT, stdin=subprocess.DEVNULL)
    last = (c.stdout.strip().splitlines() or [""])[-1]
    return Result(key, check, "ok" if c.returncode == 0 else "error", last[:120],
                  (c.stderr.strip().splitlines() or [""])[0][:200], "" if c.returncode == 0 else advice)


def security_scan() -> Result:
    c = subprocess.run([sys.executable, "-I", "-B", str(system_dir() / "security_scan.py")], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=VAULT, stdin=subprocess.DEVNULL)
    m = re.search(r"(\d+) files scanned, (\d+) findings", c.stdout)
    findings = int(m.group(2)) if m else -1
    return Result("security", "Vault security scan", "ok" if findings == 0 else "warning",
                  m.group(0) if m else "scan output could not be read",
                  advice="review the findings in the weekly maintenance" if findings else "")


def checks(full: bool = False) -> list[Result]:
    notes = read_notes()
    broken, orphans = link_checks(notes)
    results = [hooks(), compact_threshold(), links(), precommit(), settings(), fields(notes), problem_history(notes),
               broken, orphans, index_missing(notes), pending(), log_check(), handoff(), hook_errors(), leftover_files(),
               instructions(), file_sizes(notes)]
    results.append(baseline_check(results))
    results += [session_records(), tasks(), remind_size(), git_state(), regression_markers(notes)]
    if full:
        results += [command_result("secrets", "Secret scan (tracked files)", [str(system_dir() / "secret_scan.py"), "--all"],
                                   "take the value out of the file (#18)"),
                    security_scan(), search_hit_rate(),
                    command_result("tests", "Tests", [str(system_dir() / "run_tests.py")], "fix the failing test (debugging)")]
    return results


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Second brain health check")
    p.add_argument("--full", action="store_true")
    p.add_argument("--json", action="store_true")
    p.add_argument("--save-baseline", action="store_true")
    args = p.parse_args()
    results = checks(full=args.full)
    if args.save_baseline:
        print(f"baseline: {json.dumps(save_baseline(results), ensure_ascii=False)}")
        return 0
    if args.json:
        print(json.dumps([asdict(r) for r in results], ensure_ascii=False, indent=1))
    else:
        mark = {"ok": "✓", "warning": "!", "error": "✗"}
        for r in results:
            print(f"{mark[r.status]} {r.check}: {r.summary}" + (f"\n    {r.details}" if r.details and r.status != "ok" else "")
                  + (f"\n    → {r.advice}" if r.advice else ""))
        counts = {s: sum(1 for r in results if r.status == s) for s in ("ok", "warning", "error")}
        print(f"\n{counts['ok']} ok, {counts['warning']} warnings, {counts['error']} errors")
    return 1 if any(r.status == "error" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
