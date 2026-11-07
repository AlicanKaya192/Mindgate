"""Hook script that connects Claude Code sessions to the second brain.

Hook modes:
  save      SessionEnd and PreCompact: writes a short trace of the session under inbox/sessions/ (before the
            context is lost).
  remind    SessionStart: if there are unprocessed session records, prints a short reminder into Claude's context
            (stdout is added to the context).

Records are a raw trace: the user's messages (shortened, secrets masked) and the changed files. They stay outside
git (.gitignore). After Claude processes a record into the vault it does NOT delete the file; the `process` mode
moves it to an archive outside git (_system/output/processed-sessions/; rule #22: no deletion without permission).

Modes: save, remind (hooks), scan (by hand or from the daily task), process <record.md> ... (moves processed records
to the archive).

Recording mode (#43): in a new chat `remind` makes Claude ask "should this chat be recorded in the vault?".
The raw record of an unrecorded or unanswered chat is not written in any mode (`session_mode.py`).

`scan` reads only the sessions that belong to the vault; `daily.scan_all_projects: true` in config.json scans
every Claude Code project.

Hooks must never break the session: every error is swallowed silently.

Optional rule #17 (single machine): when `optional_rules.single_machine` is true in config.json, the hooks run
only on the machine whose name has the SHA-256 fingerprint `optional_rules.machine_sha256`. The machine name itself
is never written (rule #18). The rule is off by default.
"""
import hashlib
import json
import os
import re
import socket
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the -I flag does not add the script folder to the path
import common  # noqa: E402
import session_mode as sm  # noqa: E402
from common import OUTPUT, VAULT, name, vault_path  # noqa: E402
from records import PENDING  # noqa: E402

SESSIONS_DIR = vault_path("inbox", "sessions")
VAULT_PROJECTS = vault_path("projects")
TRANSCRIPTS_DIR = Path.home() / ".claude" / "projects"          # Claude Code transcripts
LAST_SCAN = OUTPUT / "last_scan.txt"                          # outside git
RULES = vault_path("rules", "general-rules.md")              # its summary is printed into the context at start (#26)
VIOLATIONS = vault_path("rules", "rule-violations.md")
VIOLATION_DAYS = 14            # a rule broken 2+ times within this many days is warned about at start (#34)
PROCESSED_DIR = OUTPUT / "processed-sessions"                 # processed records are moved here (not deleted)
TAIL_BYTES = 25 * 1024 * 1024  # in huge transcripts only the last 25 MB is read
MESSAGE_LIMIT = 40
MESSAGE_LENGTH = 300
# Messages added by the system, not written by the user
NOISE = ("<", "This session is being continued", "[Request interrupted", "Caveat:")
# The Python command shown in printed commands; `python` in config.json overrides it
PY = str(common.CONFIG.get("python") or ("py -3" if os.name == "nt" else "python3"))

SECRETS = [
    re.compile(r"sk-[A-Za-z0-9_\-]{16,}"),
    re.compile(r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"xox[abprs]-[A-Za-z0-9\-]{10,}"),
    re.compile(r"(?i)(password|parola|şifre|sifre|token|secret|api[_-]?key)\s*[:=]\s*\S+"),
    re.compile(r"\b[A-Za-z0-9+/_\-]{40,}={0,2}\b"),
    re.compile(r"\b(?:[A-Z0-9]{5}-){4}[A-Z0-9]{5}\b"),                 # product / license key
    re.compile(r"\b(?:\d{6}-){7}\d{6}\b"),                               # BitLocker recovery key
    re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),                          # IPv4 address
    re.compile(r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b"),          # MAC address
    re.compile(r"(?i)\b(pin|wifi|wi-fi|kurtarma|recovery|lisans|license|serial|seri)\b"
               r"\s*(kodu|code|key|anahtar[ıi]?|no|numaras[ıi])?\s*[:=]\s*\S+"),
]
MASK = "[HIDDEN]"


def localized(en: str, tr: str) -> str:
    """Text the user sees directly, in the install language (config.json `language`)."""
    return tr if common.LANGUAGE == "tr" else en


def mask(text: str) -> str:
    for pattern in SECRETS:
        text = pattern.sub(MASK, text)
    return text


def shorten(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= MESSAGE_LENGTH else text[:MESSAGE_LENGTH] + "…"


def read_transcript(path: Path):
    """(user messages, changed files, truncated or not)"""
    messages, files = [], []
    size = path.stat().st_size
    with path.open("rb") as f:
        truncated = size > TAIL_BYTES
        if truncated:
            f.seek(size - TAIL_BYTES)
            f.readline()  # drop the half line
        for raw in f:
            try:
                o = json.loads(raw)
            except ValueError:
                continue
            kind = o.get("type")
            if kind == "user" and not o.get("isMeta") and not o.get("isSidechain"):
                content = o.get("message", {}).get("content")
                parts = [content] if isinstance(content, str) else [
                    p.get("text", "") for p in (content or []) if isinstance(p, dict) and p.get("type") == "text"]
                for text in parts:
                    text = text.strip()
                    if text and not text.startswith(NOISE):
                        messages.append(shorten(mask(text)))
            elif kind == "assistant":
                for p in o.get("message", {}).get("content", []) or []:
                    if isinstance(p, dict) and p.get("type") == "tool_use" and p.get("name") in ("Write", "Edit", "NotebookEdit"):
                        file_path = (p.get("input") or {}).get("file_path")
                        if file_path and file_path not in files:
                            files.append(file_path)
    return messages[-MESSAGE_LIMIT:], files, truncated


def session_ended(data: dict) -> None:
    """SessionEnd and PreCompact: on /clear the recording mode is handed to the new session, then the raw record
    (if recorded)."""
    if data.get("hook_event_name") == "SessionEnd":
        sm.ended(str(data.get("session_id") or ""), str(data.get("reason") or ""), str(data.get("cwd") or ""))
    save(data)


def save(data: dict) -> None:
    if sm.is_unrecorded(str(data.get("session_id") or "")):
        return  # temporary chat: not even a raw trace is taken; the daily scan also passes through here
    path = Path(data.get("transcript_path") or "")
    if not path.is_file():
        return
    messages, files, truncated = read_transcript(path)
    if not messages:
        return
    cwd = Path(data.get("cwd") or ".")
    project = re.sub(r"[^a-z0-9]+", "-", cwd.name.lower()).strip("-") or "session"
    sid = (data.get("session_id") or "unknown")[:8]
    now = datetime.now()
    event = data.get("hook_event_name", "")
    reason = data.get("reason") or data.get("trigger") or ""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    existing = sorted(SESSIONS_DIR.glob(f"*-{project}-{sid}.md"))
    target = existing[0] if existing else SESSIONS_DIR / f"{now:%Y-%m-%d}-{project}-{sid}.md"
    lines = [
        "---",
        "type: session",
        "status: open",
        f"created: {now:%Y-%m-%d}",
        f"updated: {now:%Y-%m-%d}",
        "---",
        "",
        f"# Session record — {cwd.name} ({now:%Y-%m-%d %H:%M})",
        "",
        "> Automatic raw trace (hook). After Claude processes it into the vault it moves this file to the archive "
        "(does not delete it). See `CLAUDE.md` §7.8.",
        "",
        f"- **Folder:** `{cwd}`",
        f"- **Session:** `{data.get('session_id', '')}`",
        f"- **Last event:** {event} ({reason})",
        f"- **Transcript:** `{path}`" + (" (huge; only the last part was read)" if truncated else ""),
        "",
        "## User messages (last " + str(len(messages)) + ")",
        *[f"{i}. {m}" for i, m in enumerate(messages, 1)],
        "",
        "## Changed files",
        *([f"- `{f}`" for f in files] or ["- (none)"]),
        "",
    ]
    target.write_text("\n".join(lines), encoding="utf-8")


def rule_summary() -> str:
    """Short title of every rule from the general-rules table (its bold part or its first sentence)."""
    if not RULES.is_file():
        return ""
    rules = []
    for line in RULES.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*(\d+)\s*\|\s*(.+?)\s*\|", line)
        if not m:
            continue
        bold = re.match(r"\*\*(.+?)\*\*", m.group(2))  # the bold part is the title only if the rule starts with it
        short = re.sub(r"\*\*|`|\[\[|\]\]", "", bold.group(1) if bold else m.group(2).split(". ")[0]).strip().rstrip(":.")
        rules.append((int(m.group(1)), short if len(short) <= 120 else short[:119] + "…"))
    return " · ".join(f"#{no} {r}" for no, r in sorted(rules))


def repeated_violations(days: int = VIOLATION_DAYS, today: str = "") -> list[tuple[str, int, str]]:
    """Rules broken 2+ times in the last `days` days: (rule, count, latest root cause). Rule #34: the safeguard is
    strengthened."""
    if not VIOLATIONS.is_file():
        return []
    limit = (datetime.fromisoformat(today) if today else datetime.now()).date().toordinal() - days
    counts: dict[str, list] = {}
    for line in VIOLATIONS.read_text(encoding="utf-8").splitlines():
        p = [c.strip() for c in line.split("|")]
        if len(p) < 6 or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", p[1]) or not re.fullmatch(r"#\d+", p[2]):
            continue
        if datetime.fromisoformat(p[1]).date().toordinal() <= limit:
            continue
        entry = counts.setdefault(p[2], [0, ""])
        entry[0] += 1
        entry[1] = p[4]
    return sorted(((r, n, cause) for r, (n, cause) in counts.items() if n >= 2), key=lambda x: (-x[1], x[0]))


def on_hold_topics() -> list[str]:
    """Items the user said they will look at later (#12): they are not reopened on their own."""
    if not PENDING.is_file():
        return []
    return [re.sub(r"\s+", " ", m.group(1) + " " + m.group(2)[:60]).strip()
            for m in re.finditer(r"(?m)^- \[ \] ([PB]-\d+) \| on-hold \| [\d-]+ \| ([^|]+)", PENDING.read_text(encoding="utf-8"))]


def attention_line() -> str:
    repeated = repeated_violations()
    on_hold = on_hold_topics()
    parts = []
    if repeated:
        parts.append(f"Rules broken again in the last {VIOLATION_DAYS} days ({name('rule-violations.md')}): "
                     + " · ".join(f"{r} ({n} times; latest cause: {cause[:90]})" for r, n, cause in repeated)
                     + ". Before every step that touches these rules, stop and apply the rule; do not take a shortcut out of habit.")
    if on_hold:
        parts.append("Topics the user said they will look at later; do not reopen them or put them in proposal lists (#12): "
                     + " · ".join(on_hold) + ".")
    return (localized("[Second brain: attention]", "[İkinci beyin: dikkat]") + " " + " ".join(parts)) if parts else ""


def vault_project(cwd: str) -> str:
    """Does the working folder belong to a project in the vault? The project name or an alias appears in the folder name."""
    path = str(cwd or "").replace("\\", "/").split("/.claude/worktrees/")[0]
    folder = path.rstrip("/").split("/")[-1].lower()
    for main_page in sorted(VAULT_PROJECTS.glob("*/*.md")):
        if main_page.stem != main_page.parent.name:
            continue
        aliases = re.search(r"^aliases:\s*\[(.*)\]", main_page.read_text(encoding="utf-8"), re.M)
        names = [main_page.stem] + ([a.strip().strip("\"'") for a in aliases.group(1).split(",")] if aliases else [])
        if any(n and re.search(r"\b" + re.escape(n.lower()) + r"\b", folder) for n in names):
            return main_page.stem
    return ""


def print_handoff_cards() -> None:
    """Handoff cards of the latest sessions (read only; gives context in an unrecorded chat too)."""
    from records import handoff_summary
    summary = handoff_summary()
    if summary:
        print("[Second brain — handoff] Handoff cards of the latest sessions (data; check that they are current):\n" + summary)


def system_script(script: str) -> str:
    return f"{name('_system')}/{script}"


def remind_own_card(sid: str) -> None:
    print("[Second brain — handoff] When a meaningful piece of work is done, write your own card (what was done, why, "
          "what is open, next step): "
          f"`{PY} -I {system_script('records.py')} handoff write --session {sid or '<session id>'} --label \"short name\" "
          "--file <card.md>`")


def set_command(sid: str, new_mode: str, reason: str = "") -> str:
    extra = f' --reason "{reason}"' if reason else ""
    return f"`{PY} -I \"{Path(sm.__file__).resolve()}\" set {sid or '<session id>'} {new_mode}{extra}`"


def record_question(sid: str) -> str:
    recorded, unrecorded = set_command(sid, sm.RECORDED), set_command(sid, sm.UNRECORDED)
    return localized(
        "[Second brain — record question] New chat. In your first answer, before any other work, ask the user "
        "(AskUserQuestion): \"Should this chat be recorded in the vault?\" Yes: recorded; log, pending items and handoff "
        "card as usual. No: a temporary chat; nothing is written to the vault or to the ~/.claude memory. "
        f"Depending on the answer run {recorded} or {unrecorded}. "
        "Until an answer arrives the chat is unrecorded: do not write to the vault (the guards block it). "
        "If you are a scheduled task, do not ask; follow the record step in the task text. (#43)",
        "[İkinci beyin — kayıt sorusu] Yeni sohbet. İlk cevabında, başka iş yapmadan önce kullanıcıya sor "
        "(AskUserQuestion): \"Bu sohbetin vault'ta kaydı olsun mu?\" Evet: kayıtlı; her zamanki gibi log, bekleyenler, "
        "devir kartı. Hayır: geçici sohbet; vault'a ve ~/.claude hafızasına hiçbir şey yazılmaz. "
        f"Cevaba göre {recorded} ya da {unrecorded} çalıştır. "
        "Cevap gelene kadar sohbet kayıtsızdır: vault'a yazma (kapılar engeller). "
        "Zamanlanmış görevsen sorma; görev metnindeki kayıt adımını uygula. (#43)")


def task_command(sid: str) -> str:
    return set_command(sid, sm.RECORDED, sm.SCHEDULED_TASK)


def unrecorded_warning(sid: str, inherited: bool = False) -> str:
    task = (" If you are a scheduled task this choice is not yours: follow the record step in the task text: "
            + task_command(sid) if inherited else "")
    return ("[Second brain — unrecorded chat] The user chose this chat as unrecorded (temporary). Write nothing to the "
            "vault, the log, pending items, the handoff card or the ~/.claude memory; do not process session records. You "
            "may read the vault and the rules still apply. If the user wants recording turned on: "
            + set_command(sid, sm.RECORDED) + "." + task + " (#43)")


def inherited_note(sid: str, current: str) -> str:
    choice = "recorded" if current == sm.RECORDED else "unrecorded (temporary)"
    other = sm.UNRECORDED if current == sm.RECORDED else sm.RECORDED
    minutes = sm.RECENT_CHAT_S // 60
    return (f"[Second brain — recording mode inherited] This chat took over the choice of the chat used in the same folder "
            f"in the last {minutes} minutes: {choice} (on the desktop app /clear opens a new session). Do not ask the record "
            f"question; tell the user this in one line at the start of your first answer. To change it: "
            f"{set_command(sid, other)}. If you are a scheduled task, do not use the inherited choice; follow the record "
            f"step in the task text: {task_command(sid)} (#43)")


def recording_mode(data: dict) -> str:
    sid, source = str(data.get("session_id") or ""), str(data.get("source") or "")
    try:
        return sm.started(sid, source, str(data.get("cwd") or ""), str(data.get("transcript_path") or ""))
    except Exception as error:  # if the mode file cannot be read, the safe side: ask the question, writing stays closed
        common.log_error("session_log.recording_mode", error)
        return sm.WAITING


def remind(data: dict) -> None:
    sid = str(data.get("session_id") or "")
    current = recording_mode(data)
    if current == sm.WAITING:
        print(record_question(sid))
    elif data.get("source") in ("startup", "clear"):
        print(inherited_note(sid, current))   # new session but the choice was inherited (if unrecorded the warning below follows)
    if current == sm.UNRECORDED:
        print(unrecorded_warning(sid, inherited=data.get("source") in ("startup", "clear")))
    # Rule #26: every session starts connected to the second brain; the rules are not forgotten (read in unrecorded chats too)
    summary = rule_summary()
    if summary:
        print("[Second brain] This session is connected to the user's second brain (vault: "
              f"`{VAULT}`). Do not act on your own: read `{name('me')}/{name('profile.md')}`; when a task or decision touches "
              f"a rule, read that rule's full text in `{name('rules')}/{name('general-rules.md')}`; before deciding, search "
              f"the vault for the rule, ADR, problem note and earlier decision (`search.py`) and follow them. "
              "Do only what was asked, ask before unrequested work (#23); do not claim anything without checking (#24); "
              f"no unnecessary steps (#25); no deletion without permission (#22). General rules: {summary}")
    attention = attention_line()
    if attention:
        print(attention)
    project = vault_project(data.get("cwd", ""))
    if project:
        print(f"[Second brain] This folder is the `{project}` project in the vault. Before starting, read "
              f"`{name('projects')}/{project}/{project}.md`, `{project}-rules.md` and `{project}-progress.md` and follow "
              "the project rules.")
    try:
        print_handoff_cards()
    except Exception as error:  # even if the handoff cannot be read the other reminders are printed; a trace remains
        common.log_error("session_log.handoff", error)
    if current != sm.RECORDED:
        return  # what follows asks for writing to the vault; it stays quiet in unrecorded and unanswered chats
    remind_own_card(sid)
    records = sorted(SESSIONS_DIR.glob("*.md")) if SESSIONS_DIR.is_dir() else []
    source = data.get("source", "")
    if source in ("compact", "clear"):
        why = "was compacted (compact)" if source == "compact" else "was cleared (/clear)"
        print(f"[Second brain] The context {why}. Ideas, problems/solutions, decisions and progress discussed in the "
              f"previous context may not be in the vault yet. Before continuing, read the related session record under "
              f"`{SESSIONS_DIR}` and add what is missing to the vault (vault CLAUDE.md §7.8).")
    if records:
        listing = ", ".join(r.name for r in records[-5:])
        print(f"[Second brain] There are {len(records)} unprocessed session records: {listing}. Process them at the first "
              f"good moment, then move them to the archive with `{PY} -I {system_script('session_log.py')} process "
              "<record>`; do not delete (vault CLAUDE.md §7.8, rule #22).")


def transcript_cwd(path: Path) -> str:
    """Finds the working folder in the first lines of the transcript."""
    with path.open("rb") as f:
        for i, raw in enumerate(f):
            if i > 300:
                break
            try:
                cwd = json.loads(raw).get("cwd")
            except ValueError:
                continue
            if cwd:
                return cwd
    return ""


def in_vault(cwd: str) -> bool:
    """Is the working folder the vault or a folder inside it?"""
    if not cwd:
        return False
    folder = Path(os.path.normcase(os.path.abspath(cwd)))
    return folder.is_relative_to(Path(os.path.normcase(os.path.abspath(VAULT))))


def scan_all_projects() -> bool:
    return bool((common.CONFIG.get("daily") or {}).get("scan_all_projects"))


def scan(all_projects: bool | None = None) -> None:
    """Writes session records from every transcript that changed since the last scan.

    The SessionEnd hook may not run if the computer is shut down while the app is open. The daily task runs this
    first, so the last sessions of the previous day are not missed. By default only the vault's own sessions are
    read; `daily.scan_all_projects` in config.json (or `all_projects=True`) reads every project.
    """
    if all_projects is None:
        all_projects = scan_all_projects()
    start = datetime.now().timestamp()
    try:
        last = float(LAST_SCAN.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        last = start - 48 * 3600  # first run: the last 2 days
    scanned = 0
    for path in sorted(TRANSCRIPTS_DIR.glob("*/*.jsonl")):
        try:
            if path.stat().st_mtime < last - 600:  # 10 min margin
                continue
        except OSError:
            continue
        try:
            cwd = transcript_cwd(path)
            if not all_projects and not in_vault(cwd):
                continue
            scanned += 1
            save({"transcript_path": str(path), "session_id": path.stem, "cwd": cwd,
                  "hook_event_name": "DailyScan", "reason": sm.SCHEDULED_TASK})
        except Exception as error:
            print(f"! {path.name}: {error}")
    LAST_SCAN.parent.mkdir(parents=True, exist_ok=True)
    LAST_SCAN.write_text(str(start), encoding="utf-8")
    records = sorted(SESSIONS_DIR.glob("*.md")) if SESSIONS_DIR.is_dir() else []
    scope = "all projects" if all_projects else "vault sessions only"
    print(f"{scanned} transcripts scanned ({scope}); {len(records)} session records waiting to be processed.")
    for r in records:
        print(f"- {r.name}")


def process(names: list[str]) -> None:
    """Moves processed records from inbox/sessions/ to _system/output/processed-sessions/.

    Does not delete (rule #22). Touches only .md files in the record folder; if the same name exists in the archive a
    number is added, nothing is overwritten.
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    for record in names:
        source = SESSIONS_DIR / Path(record).name
        if source.suffix != ".md" or not source.is_file():
            print(f"skipped (not in the record folder): {record}")
            continue
        target, n = PROCESSED_DIR / source.name, 1
        while target.exists():
            target, n = PROCESSED_DIR / f"{source.stem}-{n}{source.suffix}", n + 1
        source.rename(target)
        print(f"moved to the archive: {source.name} → {target.relative_to(VAULT).as_posix()}")


def machine_fingerprint() -> str:
    return hashlib.sha256(socket.gethostname().lower().encode()).hexdigest()


def this_machine(config: dict | None = None) -> bool:
    """Optional rule #17: with `optional_rules.single_machine` on, only the machine whose fingerprint is
    `optional_rules.machine_sha256` counts; with the rule on and no fingerprint, no machine counts (safe side)."""
    rules = (common.CONFIG if config is None else config).get("optional_rules") or {}
    if not rules.get("single_machine"):
        return True
    expected = str(rules.get("machine_sha256") or "").strip().lower()
    return bool(expected) and machine_fingerprint() == expected


def main() -> None:
    if not this_machine():
        return
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # the Windows console uses a legacy code page; Claude Code reads UTF-8
    except (AttributeError, ValueError):
        pass
    if mode == "scan":  # by hand or from the scheduled task; does not read stdin, shows errors
        scan()
        return
    if mode == "process":  # moves processed records to the archive; rule #22: no deletion
        process(sys.argv[2:])
        return
    try:
        sys.stdin.reconfigure(encoding="utf-8")
        data = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        data = {}
    try:
        if mode == "save":
            session_ended(data)
        elif mode == "remind":
            remind(data)
    except Exception:
        pass  # the hook must never break the session


if __name__ == "__main__":
    main()
