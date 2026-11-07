"""Runs every *_test.py file under _system/ in its own process.

Run (from the vault root): python -I -B _system/run_tests.py
Every test file runs without network and without changing the vault; temporary files stay under _system/output/.
Exit code: 1 if even one test file fails.
"""
import subprocess
import sys
import time
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
TIMEOUT_S = 300


def run(test: Path) -> tuple[bool, float, str]:
    start = time.monotonic()
    try:
        c = subprocess.run([sys.executable, "-I", "-B", str(test)], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", stdin=subprocess.DEVNULL, timeout=TIMEOUT_S, cwd=TOOLS.parent)
    except subprocess.TimeoutExpired:
        return False, TIMEOUT_S, "timed out"
    output = (c.stdout + c.stderr).strip().splitlines()
    return c.returncode == 0, time.monotonic() - start, (output[-1] if output else "")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    tests = sorted(TOOLS.glob("*_test.py"))
    failed = 0
    for test in tests:
        passed, duration, last = run(test)
        failed += not passed
        print(f"{'PASSED' if passed else 'FAILED'} {test.name:28} {duration:5.1f} s  {last[:90]}")
    print(f"{len(tests) - failed}/{len(tests)} test files passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
