"""Recording mode of a chat: recorded (everything goes into the vault) or unrecorded (a temporary chat, nothing is
written to the vault).

Why: at the start of every new chat the user is asked "should this chat be recorded in the vault?"; if the answer is
"no", the chat behaves like a temporary one (general rules #43). Until an answer arrives, and for a chat that closes
without an answer, the chat is unrecorded.

Modes:
  recorded    the question was answered "yes", or the chat started before this feature (it has no entry)
  unrecorded  the question was answered "no"
  waiting     new chat, no answer: counts as unrecorded
/clear opens a new session id but it is the same chat: the old session's mode is handed to the new session and the
question is not asked again. The desktop app reports /clear as "startup" and does not send SessionEnd reliably, so a
new session also takes over the choice of an answered chat that was active in the same transcript folder in the last
15 minutes. If the choices conflict, the question is asked.
The entries are kept outside git in `_system/output/session_mode.json`; they hold only the session id, mode, folder
and time.

Usage:
  session_mode.py set <session> recorded|unrecorded [--reason "..."]
  session_mode.py status <session>
  session_mode.py unrecorded          unrecorded (and unanswered) session ids, one per line
"""
import argparse
import json
import os
import sys
import time
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the -I flag does not add the script folder to the path
from common import OUTPUT, atomic_write, locked  # noqa: E402

DEFAULT_FILE = OUTPUT / "session_mode.json"
ENV_VAR = "SESSION_MODE_FILE"   # only for guard tests that run in a subprocess
RECORDED, UNRECORDED, WAITING = "recorded", "unrecorded", "waiting"
ANSWERS = (RECORDED, UNRECORDED)
HANDOFF_S = 300                   # /clear: time between SessionEnd and the new SessionStart; older ones belong to another chat
RECENT_CHAT_S = 15 * 60           # when /clear arrives as "startup": at most this long since the previous chat's last activity
SCHEDULED_TASK = "scheduled task"   # the --reason value of scheduled tasks; a task's choice is not handed to a chat
RETENTION_S = 90 * 24 * 3600      # only recorded entries are pruned
now = time.time                   # tests change the clock


def file_path(env: dict) -> Path:
    """The environment variable may only point under output/: the guard must not take another file for the mode file."""
    wanted = env.get(ENV_VAR)
    if not wanted:
        return DEFAULT_FILE
    path = Path(os.path.abspath(wanted))
    return path if path.is_relative_to(Path(os.path.abspath(OUTPUT))) else DEFAULT_FILE


FILE = file_path(os.environ)


class CorruptFile(Exception):
    """The mode file cannot be read. Readers fall to the safe side (everyone unrecorded); writers do not overwrite it."""


def read() -> dict:
    try:
        data = json.loads(FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        data = {}
    except ValueError as error:
        # If it counted as empty, unrecorded chats would silently turn recorded and the nightly task would process them (#37)
        raise CorruptFile(f"{FILE} could not be read ({error}); until it is fixed every session counts as unrecorded") from error
    # An entry without an id is ignored: otherwise every hook call without an id would count as unrecorded
    sessions = {s: e for s, e in data.get("sessions", {}).items() if s}
    return {"sessions": sessions, "handoff": data.get("handoff", {})}


def _write(data: dict) -> None:
    # An unrecorded entry is not pruned: once pruned it would count as an "old session without an entry" and turn recorded
    limit = now() - RETENTION_S
    data["sessions"] = {s: e for s, e in data["sessions"].items() if e["mode"] != RECORDED or e["time"] >= limit}
    data["handoff"] = {f: h for f, h in data["handoff"].items() if h["time"] >= now() - HANDOFF_S}
    atomic_write(FILE, json.dumps(data, ensure_ascii=False, indent=1))


def _folder(cwd: str) -> str:
    return os.path.normcase(os.path.abspath(cwd)) if cwd else ""


def _corruption_trace(error: CorruptFile) -> None:
    from common import log_error
    log_error("session_mode", error)


def mode(sid: str) -> str:
    try:
        entry = read()["sessions"].get(sid)
    except CorruptFile as error:
        _corruption_trace(error)
        return UNRECORDED
    return entry["mode"] if entry else RECORDED


def is_unrecorded(sid: str) -> bool:
    return mode(sid) != RECORDED


def unrecorded_sessions() -> set[str]:
    return {s for s, e in read()["sessions"].items() if e["mode"] != RECORDED}


def unrecorded_filter() -> Callable[[str], bool]:
    """For callers that scan many transcripts: the file is read once; if it is corrupt, every session is skipped."""
    try:
        unrecorded = unrecorded_sessions()
    except CorruptFile as error:
        _corruption_trace(error)
        return lambda _sid: True
    return unrecorded.__contains__


def _store(data: dict, sid: str, new_mode: str, cwd: str, reason: str) -> None:
    if sid:
        data["sessions"][sid] = {"mode": new_mode, "cwd": _folder(cwd), "time": now(), "reason": reason}


def set_mode(sid: str, new_mode: str, cwd: str = "", reason: str = "") -> None:
    if new_mode not in ANSWERS:
        raise ValueError(f"invalid mode '{new_mode}': {' or '.join(ANSWERS)}")
    with locked("session_mode"):
        data = read()
        previous = data["sessions"].get(sid, {})
        _store(data, sid, new_mode, cwd or previous.get("cwd", ""), reason)
        _write(data)


def _recent_chat_choice(sessions: dict, sid: str, transcript: str) -> str | None:
    """The shared choice of chats active in the same transcript folder within the last RECENT_CHAT_S.
    An unanswered (waiting) chat in the window counts as a conflict: its /clear must not become recorded because of a
    parallel recorded chat (#37)."""
    if not transcript:
        return None
    folder = Path(transcript).parent
    limit = now() - RECENT_CHAT_S
    choices = set()
    for other, entry in sessions.items():
        if other == sid or entry.get("reason") == SCHEDULED_TASK:
            continue
        try:
            if (folder / f"{other}.jsonl").stat().st_mtime >= limit:
                choices.add(entry["mode"])
        except OSError:
            continue
    return choices.pop() if len(choices) == 1 and not choices & {WAITING} else None


def started(sid: str, source: str, cwd: str, transcript: str = "") -> str:
    """SessionStart: a new chat is waiting; /clear (or the same folder with a recent choice) takes over the mode;
    resume and compact leave it alone."""
    if source not in ("startup", "clear"):
        return mode(sid)
    with locked("session_mode"):
        data = read()
        handoff = data["handoff"].pop(_folder(cwd), None) if source == "clear" else None
        recent = _recent_chat_choice(data["sessions"], sid, transcript)
        if handoff and now() - handoff["time"] <= HANDOFF_S:
            new_mode, reason = handoff["mode"], "clear: taken over from the previous session"
        elif recent:
            new_mode, reason = recent, "taken over from a recent chat in the same folder"
        else:
            new_mode, reason = WAITING, "new chat, waiting for an answer"
        _store(data, sid, new_mode, cwd, reason)
        _write(data)
    return new_mode


def ended(sid: str, reason: str, cwd: str) -> None:
    """SessionEnd: on /clear, leaves the mode for the session that will start shortly in the same folder."""
    if reason != "clear":
        return
    with locked("session_mode"):
        data = read()
        data["handoff"][_folder(cwd)] = {"mode": mode(sid), "time": now()}
        _write(data)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Recording mode of a chat (rule #43)")
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("set")
    s.add_argument("session")
    s.add_argument("mode", choices=ANSWERS)
    s.add_argument("--reason", default="the user's answer")
    sub.add_parser("status").add_argument("session")
    sub.add_parser("unrecorded")
    args = p.parse_args(argv)
    try:
        if args.command == "set":
            set_mode(args.session, args.mode, reason=args.reason)
            print(f"{args.session}: {args.mode}")
        elif args.command == "status":
            print(f"{args.session}: {mode(args.session)}")
        else:
            print("\n".join(sorted(unrecorded_sessions())))
    except CorruptFile as error:
        print(f"ERROR: {error}. Nothing was written; treat every transcript as unrecorded and process none.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
