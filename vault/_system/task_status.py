"""Status record of the scheduled tasks: the weekly maintenance must not touch the session logs before the daily
task has finished.

Why: if the computer is off at the scheduled time, both tasks start together at the next start-up and try to process
the same session logs.

Usage (from the vault root):
  python _system/task_status.py start daily    # at the start of the task
  python _system/task_status.py finish daily   # at the end of the task (even after an error)
  python _system/task_status.py read daily     # writes the status as JSON
  python _system/task_status.py wait daily     # waits at most ~9 min; exit 0 = not running, 1 = still running

File: _system/output/task_status.json (outside git). Nothing is deleted; the status is overwritten.
"""
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the -I flag does not add the script folder to the path
from common import OUTPUT  # noqa: E402

STATUS_FILE = OUTPUT / "task_status.json"
STUCK_AFTER = timedelta(hours=3)   # a task shown as "running" for this long counts as interrupted
WAIT_STEP_S = 30
MAX_WAIT_S = 540                   # stays below the command timeout (10 min)
RUNNING, DONE = "running", "done"
COMMANDS = ("start", "finish", "read", "wait")


def read_statuses() -> dict:
    try:
        return json.loads(STATUS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def write_status(task: str, fields: dict) -> None:
    statuses = read_statuses()
    statuses[task] = {**statuses.get(task, {}), **fields}
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATUS_FILE.write_text(json.dumps(statuses, ensure_ascii=False, indent=1), encoding="utf-8")


def is_running(record: dict) -> bool:
    if record.get("state") != RUNNING:
        return False
    started = datetime.fromisoformat(record["started_at"])
    return datetime.now() - started < STUCK_AFTER


def summary(task: str) -> dict:
    record = read_statuses().get(task, {})
    today = datetime.now().date().isoformat()
    return {"task": task, "running": is_running(record),
            "finished_today": str(record.get("finished_at", ""))[:10] == today, **record}


def wait(task: str) -> int:
    start = time.monotonic()
    while is_running(read_statuses().get(task, {})):
        if time.monotonic() - start >= MAX_WAIT_S:
            return 1
        time.sleep(WAIT_STEP_S)
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2 or argv[0] not in COMMANDS:
        print(__doc__)
        return 2
    command, task = argv
    now = datetime.now().isoformat(timespec="seconds")
    if command == "start":
        write_status(task, {"state": RUNNING, "started_at": now})
    elif command == "finish":
        write_status(task, {"state": DONE, "finished_at": now})
    elif command == "wait":
        result = wait(task)
        print(json.dumps(summary(task), ensure_ascii=False))
        return result
    print(json.dumps(summary(task), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # the Windows console default breaks non-ASCII text
    sys.exit(main())
