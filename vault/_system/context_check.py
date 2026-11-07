"""Context window management: save to the vault before it fills up, say what to keep when compacting, keep the summary.

Why: compact when the context reaches 65-70%, but first write the unfinished work, where it stopped, the next step
and the important topics discussed into the vault, so that a passing idea is not lost.

Three layers, three hook modes:
  stop    Stop: two steps, each once until the next compaction (config.json → context_window):
          - work_end_percent (40%): "If the work is going on, continue; if a piece of work has just ended, save and
            suggest a new chat or /clear." Early compaction happens when work ends, not while it is going on; an early
            summary in the middle of work drops file paths and error details, and the same files are read again.
          - warning_percent (60%): "Write the handoff card, add what is not processed yet to the vault."
  before  PreCompact: the text it prints is added to Claude Code's compaction summary as custom instructions ("what
          to keep"): Claude Code turns PreCompact hook output into `newCustomInstructions`. If the work crosses the
          threshold in the middle of a turn, the record is kept this way.
  after   PostCompact: writes the compaction summary (`compact_summary`), secrets masked, under inbox/sessions/
          (outside git). The SessionStart reminder and the daily task process this record.

Automatic compaction itself is Claude Code's job: ~/.claude/settings.json → env → CLAUDE_AUTOCOMPACT_PCT_OVERRIDE
(threshold = percent of the active window). Its value is kept equal to context_window.compact_percent; health.py
checks it. The hook never breaks the session: errors are swallowed, a trace goes to `output/hook_errors.log`.
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the -I flag does not add the script folder to the path
import common  # noqa: E402
import session_mode as sm  # noqa: E402
from common import CONFIG_FILE, OUTPUT, log_error, name  # noqa: E402
from session_log import PY, SESSIONS_DIR, mask, this_machine  # noqa: E402

SETTINGS = CONFIG_FILE
STATE = OUTPUT / "context_state.json"
LARGE_WINDOW = 1_000_000
TAIL_BYTES = 4 * 1024 * 1024        # for the context size only the end of the transcript is read
STATE_SESSION_LIMIT = 200
LANGUAGE_NAMES = {"en": "English", "tr": "Turkish"}


def settings() -> dict:
    return json.loads(SETTINGS.read_text(encoding="utf-8")).get("context_window", {})


def last_context(transcript: Path) -> tuple[int, str]:
    """Context size of the main chat's last message (input + cache read + cache write + output) and the model."""
    if not transcript.is_file():
        return 0, ""
    with transcript.open("rb") as f:
        f.seek(max(0, transcript.stat().st_size - TAIL_BYTES))
        lines = f.read().splitlines()
    for raw in reversed(lines):
        if b'"usage"' not in raw:
            continue
        try:
            line = json.loads(raw)
        except ValueError:
            continue   # a cut first line or a broken line
        message = line.get("message")
        if line.get("type") != "assistant" or line.get("isSidechain") or not isinstance(message, dict):
            continue
        u = message.get("usage") or {}
        total = sum(int(u.get(k) or 0) for k in ("input_tokens", "cache_read_input_tokens",
                                                 "cache_creation_input_tokens", "output_tokens"))
        if total:
            return total, str(message.get("model") or "")
    return 0, ""


def window(model: str, tokens: int, setting: dict) -> int:
    """The model's context window; the default if it is not in the table. If the seen context exceeds the default,
    the window is large."""
    guess = int(setting.get("windows", {}).get(model) or setting.get("default_window") or 200_000)
    return LARGE_WINDOW if tokens > guess else guess


def read_state() -> dict:
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def records_command(arguments: str) -> str:
    return f"`{PY} -I {name('_system')}/records.py {arguments}`"


def work_end_text(percent: int, compact: int, warning: int) -> str:
    return (f"[Second brain — context] The context is at {percent}%. If the work is going on, continue; the record "
            f"reminder comes at {warning}%, automatic compaction at {compact}%; do not suggest early compaction in the middle "
            "of work. If a piece of work has just ended and a new topic is next: write the handoff card, add unprocessed "
            "ideas, decisions and problems to the vault, then suggest to the user in one line a new chat or `/clear` (free; "
            "`/compact` is a large request and brings back the skills already used). "
            "This note is given once until this compaction.")


def warning_text(percent: int, tokens: int, window_size: int, compact: int, sid: str) -> str:
    card_command = records_command(f'handoff write --session {sid} --label "…" --file <card.md>')
    return (f"[Second brain — context] The context is {percent}% full (~{tokens // 1000}k / {window_size // 1000}k tokens). "
            f"Automatic compaction comes at about {compact}%. Before compaction, now: "
            "1) Write or update the handoff card: goal, what was done, the unfinished work and exactly the step where you "
            f"stopped, the next steps, open questions ({card_command}). "
            "2) Add the ideas, decisions, problems/solutions, progress and rules discussed in this chat and not yet in the "
            "vault to the related notes; log and commit. 3) Then continue the work where you stopped. If the work is done "
            "you may suggest a new chat to the user (one chat, one task). This warning is given once until this compaction.")


def stop(data: dict) -> str:
    """Stop hook: returns a warning text once when a threshold is crossed (else empty)."""
    if data.get("stop_hook_active"):
        return ""   # already continuing because of a hook; no loop
    sid = str(data.get("session_id") or "")
    if sm.is_unrecorded(sid):
        return ""   # the warnings ask for a handoff card and vault records; a temporary chat has nothing to write
    tokens, model = last_context(Path(str(data.get("transcript_path") or "")))
    if not sid or not tokens:
        return ""
    setting = settings()
    size = window(model, tokens, setting)
    percent = round(tokens * 100 / size)
    state = read_state()
    previous = state.get(sid)
    if isinstance(previous, int):                      # old format: only the token count of the 60% warning
        previous = {"tokens": previous, "level": 60}
    changed, text = False, ""
    if previous is not None and tokens < int(previous["tokens"]):
        previous, changed = None, True                  # the context shrank: compaction or /clear happened, steps restart
    level = int(previous["level"]) if previous else 0
    warning, work_end = int(setting.get("warning_percent", 60)), int(setting.get("work_end_percent", 40))
    compact = int(setting.get("compact_percent", 70))
    if percent >= warning and level < warning:
        previous, changed = {"tokens": tokens, "level": warning}, True
        text = warning_text(percent, tokens, size, compact, sid)
    elif work_end <= percent < warning and level < work_end:
        previous, changed = {"tokens": tokens, "level": work_end}, True
        text = work_end_text(percent, compact, warning)
    if previous is None:
        state.pop(sid, None)
    else:
        state[sid] = previous
    if changed:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps(dict(list(state.items())[-STATE_SESSION_LIMIT:]), indent=1), encoding="utf-8")
    return text


def before(data: dict) -> str:
    """PreCompact: the "what to keep" instruction added to the compaction summary."""
    sid = str(data.get("session_id") or "")
    language = LANGUAGE_NAMES.get(common.LANGUAGE, "English")
    keep = (f"Write the summary in {language} and keep the following in full: "
            "(1) The work going on now: goal, finished steps, the unfinished step and exactly where it stopped, the next "
            "steps, the changed files and the last commit. "
            "(2) The user's requests and decisions in this session, with a short quote; what the user rejected and what "
            "the user said to look at later. ")
    if sm.is_unrecorded(sid):
        return keep + (f"(3) Open questions. (4) Session id {sid}. This chat is unrecorded (temporary, #43): "
                       "nothing is saved after compaction either.")
    return keep + ("(3) The ideas, problems and solutions, and rules discussed; whether each one was added to the vault "
                   "(with the note name). (4) Open questions and pending items (P-NNN). "
                   f"(5) Session id {sid}; whether the handoff card was written. After compaction what is not processed "
                   "yet will be added to the vault.")


def after(data: dict) -> Path | None:
    """PostCompact: writes the compaction summary, masked, into the session record folder."""
    summary = str(data.get("compact_summary") or "").strip()
    if not summary or sm.is_unrecorded(str(data.get("session_id") or "")):
        return None
    cwd = Path(str(data.get("cwd") or "."))
    project = re.sub(r"[^a-z0-9]+", "-", cwd.name.lower()).strip("-") or "session"
    sid = str(data.get("session_id") or "unknown")
    now = datetime.now()
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    target = SESSIONS_DIR / f"{now:%Y-%m-%d}-{project}-{sid[:8]}-summary-{now:%H%M%S}.md"
    target.write_text("\n".join([
        "---", "type: session", "status: open", f"created: {now:%Y-%m-%d}", f"updated: {now:%Y-%m-%d}", "---", "",
        f"# Compaction summary — {cwd.name} ({now:%Y-%m-%d %H:%M})", "",
        "> Automatic (PostCompact hook, `context_check.py`). Claude Code's compaction summary; secrets masked. "
        "Add what is not processed yet to the vault, then move it to the archive with `session_log.py process` (no "
        "deletion). See `CLAUDE.md` §7.8.", "",
        f"- **Session:** `{sid}`", f"- **Trigger:** {data.get('trigger', '')}", "",
        "## Summary", mask(summary), "",
    ]), encoding="utf-8")
    return target


def main() -> None:
    if not this_machine():
        return
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")
        data = json.loads(sys.stdin.read() or "{}")
        if mode == "stop":
            text = stop(data)
            if text:
                print(json.dumps({"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": text}},
                                 ensure_ascii=False))
        elif mode == "before":
            print(before(data))
        elif mode == "after":
            after(data)
    except Exception as error:  # the hook must never break the session; a trace remains
        log_error(f"context_check.{mode}", error)


if __name__ == "__main__":
    main()
