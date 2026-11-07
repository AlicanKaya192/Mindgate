"""Expected decisions of write_guard.py. Run: python -I _system/write_guard_test.py

The guard only decides; no protected file is written. Cases that need an existing source or archive file run in
this process against a test copy under _system/output/test_write_guard/ (overwritten on every run, nothing is
deleted, #22); the others run the hook as a subprocess against the install's real paths."""
import io
import json
import os
import re
import subprocess
import sys
import time
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
import write_guard as wg  # noqa: E402
from common import VAULT, name  # noqa: E402

SCRIPT = Path(__file__).with_name("write_guard.py")
TEST_DIR = common.OUTPUT / "test_write_guard"
TEST_SOURCES = TEST_DIR / "sources"
TEST_ARCHIVES = (TEST_DIR / "archive" / "log", TEST_DIR / "archive" / "pending")
EXISTING_SOURCE = TEST_SOURCES / "raw.md"
NEW_SOURCE = TEST_SOURCES / "2099-01-01-missing-source.md"
OUTSIDE = VAULT.parent.parent / "other-project"

# (tool, input, expected) run in this process with SOURCES and ARCHIVES pointing at the test copy
IN_PROCESS_CASES = [
    # sources/: an existing file is not changed, a new file may be added
    ("Write", {"file_path": str(EXISTING_SOURCE), "content": "x"}, "deny"),
    ("Edit", {"file_path": str(EXISTING_SOURCE), "old_string": "a", "new_string": "b"}, "deny"),
    ("MultiEdit", {"file_path": str(EXISTING_SOURCE), "edits": []}, "deny"),
    ("Write", {"file_path": str(NEW_SOURCE), "content": "new source"}, ""),
    ("Edit", {"file_path": str(EXISTING_SOURCE).replace("\\", "/").lower(), "old_string": "a", "new_string": "b"}, "deny"),  # other spelling
    ("Write", {"file_path": str(TEST_SOURCES / ".." / "sources" / "raw.md"), "content": "x"}, "deny"),                    # ../ trick
    ("NotebookEdit", {"notebook_path": str(EXISTING_SOURCE), "new_source": "x"}, "deny"),
    # archives: an existing month is not changed, a missing one is not the guard's business
    ("Write", {"file_path": str(TEST_ARCHIVES[0] / "2026-10.md"), "content": "x"}, "deny"),
    ("Edit", {"file_path": str(TEST_ARCHIVES[1] / "pending-2026-10.md"), "old_string": "a", "new_string": "b"}, "deny"),
    ("Write", {"file_path": str(TEST_ARCHIVES[0] / "2099-01.md"), "content": "x"}, ""),
]

# (tool, input, expected) run as a hook subprocess — expected: "deny", "ask" or "" (silent)
CASES = [
    # log.md: only appended to with records.py log
    ("Write", {"file_path": str(VAULT / "log.md"), "content": "x"}, "deny"),
    ("Edit", {"file_path": str(VAULT / "log.md"), "old_string": "a", "new_string": "ab"}, "deny"),
    ("MultiEdit", {"file_path": str(VAULT / "log.md"), "edits": []}, "deny"),
    # other files are allowed
    ("Edit", {"file_path": str(VAULT / "index.md"), "old_string": "a", "new_string": "b"}, ""),
    ("Write", {"file_path": str(VAULT / name("archive") / "log" / "2099-01.md"), "content": "x"}, ""),  # missing archive
    ("Write", {"file_path": str(VAULT / name("sources") / "2099-01-01-missing-source.md"), "content": "x"}, ""),  # new source
    ("Write", {"file_path": str(VAULT / name("problems") / "raw-data-problem.md"), "content": "x"}, ""),
    ("Write", {"file_path": str(OUTSIDE / "raw" / "data.csv"), "content": "x"}, ""),  # sources/ outside the vault
    ("Write", {"file_path": str(OUTSIDE / "log.md"), "content": "x"}, ""),
    # without a path there is nothing to check: the guard does not crash, it stays silent
    ("Write", {"file_path": None}, ""),
]


MODE_FILE = TEST_DIR / "session_mode.json"
MEMORY = Path.home() / ".claude" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(VAULT)) / "memory" / "x.md"
PROJECT_FILE = str(OUTSIDE / "app.py")
# #43: (session, tool, path, expected). private: unrecorded, unanswered: question not answered, open: recorded
RECORD_MODE_CASES = [
    ("private", "Write", str(VAULT / name("inbox") / "2099-01-01-idea.md"), "deny"),
    ("private", "Edit", str(VAULT / "index.md"), "deny"),
    ("private", "Write", str(MEMORY), "deny"),
    ("private", "Write", PROJECT_FILE, ""),
    ("unanswered", "Edit", str(VAULT / name("inbox") / name("pending.md")), "deny"),
    ("unanswered", "Write", PROJECT_FILE, ""),
    ("open", "Edit", str(VAULT / "index.md"), ""),
    ("open", "Write", str(MEMORY), ""),
    # red-team: junctions and lasting instruction areas
    ("private", "Edit", str(Path.home() / ".claude" / "skills" / "idea" / "SKILL.md"), "deny"),   # junction → vault
    ("private", "Write", str(Path.home() / ".claude" / "CLAUDE.md"), "deny"),
    ("private", "Write", str(Path.home() / ".claude" / "scheduled-tasks" / "new" / "SKILL.md"), "deny"),
    ("private", "Write", str(common.OUTPUT / "session_mode.json"), "deny"),
]


def short_name(path: Path) -> str:
    """Windows 8.3 short name (e.g. LONGNA~1); empty if it cannot be read."""
    import ctypes
    buffer = ctypes.create_unicode_buffer(1024)
    n = ctypes.windll.kernel32.GetShortPathNameW(str(path), buffer, 1024) if os.name == "nt" else 0
    return buffer.value if n else ""


SHORT_VAULT = short_name(VAULT)
if SHORT_VAULT and SHORT_VAULT.lower() != str(VAULT).lower():
    RECORD_MODE_CASES.append(("private", "Write", str(Path(SHORT_VAULT) / name("inbox") / "a.md"), "deny"))


def prepare_files() -> None:
    TEST_SOURCES.mkdir(parents=True, exist_ok=True)
    EXISTING_SOURCE.write_text("raw source\n", encoding="utf-8")
    for archive, file_name in zip(TEST_ARCHIVES, ("2026-10.md", "pending-2026-10.md")):
        archive.mkdir(parents=True, exist_ok=True)
        (archive / file_name).write_text("archived\n", encoding="utf-8")
    now = time.time()
    sessions = {"private": "unrecorded", "unanswered": "waiting", "open": "recorded"}
    MODE_FILE.write_text(json.dumps({"sessions": {s: {"mode": m, "cwd": "", "time": now, "reason": "test"}
                                                  for s, m in sessions.items()}, "handoff": {}}), encoding="utf-8")


def run(tool: str, data: dict, cwd: str = "", session: str = "") -> dict:
    payload = json.dumps({"tool_name": tool, "tool_input": data, "cwd": cwd or str(VAULT), "session_id": session})
    env = {**os.environ, "SESSION_MODE_FILE": str(MODE_FILE)}
    output = subprocess.run([sys.executable, "-I", str(SCRIPT)], input=payload, capture_output=True, text=True, encoding="utf-8",
                            env=env)
    return json.loads(output.stdout)["hookSpecificOutput"] if output.stdout.strip() else {}


def decision(tool: str, data: dict, cwd: str = "", session: str = "") -> str:
    return run(tool, data, cwd, session).get("permissionDecision", "")


def in_process(data: dict) -> dict:
    """The decision path of main() with SOURCES and ARCHIVES pointing at the test copy (a recorded session)."""
    old = wg.SOURCES, wg.ARCHIVES
    wg.SOURCES, wg.ARCHIVES = TEST_SOURCES, TEST_ARCHIVES
    buffer = io.StringIO()
    try:
        with redirect_stdout(buffer):
            path = wg.target_path({"tool_input": data, "cwd": str(VAULT)})
            if path is not None:
                wg.check(path)
    finally:
        wg.SOURCES, wg.ARCHIVES = old
    return json.loads(buffer.getvalue())["hookSpecificOutput"] if buffer.getvalue().strip() else {}


def failed(ok: bool, text: str) -> int:
    if not ok:
        print(f"FAIL: {text}")
    return not ok


def record_mode_failures() -> int:
    failures = 0
    for session, tool, path, expected in RECORD_MODE_CASES:
        found = decision(tool, {"file_path": path, "content": "x", "old_string": "a", "new_string": "b"}, session=session)
        failures += failed(found == expected, f"[{session}] {tool} {path} → '{found}', expected '{expected}'")
    return failures


def language_failures() -> int:
    old = common.LANGUAGE
    try:
        common.LANGUAGE = "tr"
        turkish = in_process({"file_path": str(EXISTING_SOURCE), "content": "x"}).get("permissionDecisionReason", "")
        common.LANGUAGE = "en"
        english = in_process({"file_path": str(EXISTING_SOURCE), "content": "x"}).get("permissionDecisionReason", "")
    finally:
        common.LANGUAGE = old
    # The hook process reads the language from this install's config.json
    installed = run("Write", {"file_path": str(VAULT / "log.md"), "content": "x"}).get("permissionDecisionReason", "")
    expected = {"en": "[Write guard] log.md is only appended to",
                "tr": "[Yazma kapısı] log.md yalnızca sona eklenir"}[common.LANGUAGE]
    return (failed(turkish.startswith("[Yazma kapısı]") and "değiştirilmez" in turkish, f"Turkish reason: {turkish}")
            + failed(english.startswith("[Write guard]") and "are not changed" in english, f"English reason: {english}")
            + failed(installed.startswith(expected), f"install language ({common.LANGUAGE}) reason: {installed}"))


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")   # the "→" in a failure line must not crash a legacy console
    prepare_files()
    failures = record_mode_failures()
    for tool, data, expected in IN_PROCESS_CASES:
        found = in_process(data).get("permissionDecision", "")
        failures += failed(found == expected, f"(in process) {tool} {data.get('file_path') or data.get('notebook_path')} → "
                                              f"'{found}', expected '{expected}'")
    for tool, data, expected in CASES:
        found = decision(tool, data)
        failures += failed(found == expected, f"{tool} {data.get('file_path') or data.get('notebook_path')} → '{found}', "
                                              f"expected '{expected}'")
    # a relative path is resolved against cwd
    failures += failed(decision("Edit", {"file_path": "log.md", "old_string": "a", "new_string": "b"}, cwd=str(VAULT)) == "deny",
                       "relative log.md path not caught")
    failures += language_failures()
    total = len(IN_PROCESS_CASES) + len(CASES) + 1 + len(RECORD_MODE_CASES) + 2
    print(f"{total - failures}/{total} passed")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
