"""task_status.py tests. The status file is redirected to a temporary copy."""
import contextlib
import io
import json
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import task_status  # noqa: E402
from common import OUTPUT  # noqa: E402

TEST_FILE = OUTPUT / "test_task_status.json"


class TaskStatusTest(unittest.TestCase):
    def setUp(self):
        TEST_FILE.parent.mkdir(parents=True, exist_ok=True)
        TEST_FILE.write_text("{}", encoding="utf-8")
        self.old = task_status.STATUS_FILE
        task_status.STATUS_FILE = TEST_FILE

    def tearDown(self):
        task_status.STATUS_FILE = self.old

    def test_start_finish(self):
        task_status.write_status("daily", {"state": "running", "started_at": datetime.now().isoformat()})
        self.assertTrue(task_status.summary("daily")["running"])
        task_status.write_status("daily", {"state": "done", "finished_at": datetime.now().isoformat()})
        summary = task_status.summary("daily")
        self.assertFalse(summary["running"])
        self.assertTrue(summary["finished_today"])

    def test_stuck_task_does_not_count_as_running(self):
        old = (datetime.now() - task_status.STUCK_AFTER - timedelta(minutes=1)).isoformat()
        TEST_FILE.write_text(json.dumps({"daily": {"state": "running", "started_at": old}}), encoding="utf-8")
        self.assertFalse(task_status.summary("daily")["running"])

    def test_broken_file_counts_as_empty(self):
        TEST_FILE.write_text("{broken", encoding="utf-8")
        self.assertEqual(task_status.read_statuses(), {})

    def test_wait_returns_at_once_for_a_task_not_running(self):
        self.assertEqual(task_status.wait("missing"), 0)

    def test_command_line_start_and_finish(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(task_status.main(["start", "weekly"]), 0)
            self.assertEqual(task_status.main(["finish", "weekly"]), 0)
            self.assertEqual(task_status.main(["unknown", "weekly"]), 2)
        last = json.loads(out.getvalue().splitlines()[1])
        self.assertEqual((last["task"], last["running"], last["finished_today"], last["state"]), ("weekly", False, True, "done"))


if __name__ == "__main__":
    unittest.main(verbosity=1)
