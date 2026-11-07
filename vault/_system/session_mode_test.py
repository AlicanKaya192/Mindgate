"""session_mode.py tests: a new chat waits (unrecorded), answer entry, /clear handoff, old sessions are recorded.
Temporary file: _system/output/test_session_mode/. No network; does not write to the vault."""
import io
import os
import shutil
import sys
import unittest
from contextlib import redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
import session_mode as sm  # noqa: E402

ROOT = common.OUTPUT / "test_session_mode"


class SessionModeTest(unittest.TestCase):
    def setUp(self):
        ROOT.mkdir(parents=True, exist_ok=True)
        self.old = (sm.FILE, sm.now, sm._corruption_trace)
        sm.FILE = ROOT / "session_mode.json"
        self.clock = 1_000_000.0
        sm.now = lambda: self.clock
        self.traces = []
        sm._corruption_trace = self.traces.append   # must not write to the real hook_errors.log

    def tearDown(self):
        sm.FILE, sm.now, sm._corruption_trace = self.old
        shutil.rmtree(ROOT, ignore_errors=True)

    def test_old_session_without_entry_is_recorded(self):
        self.assertEqual(sm.mode("old-session"), sm.RECORDED)
        self.assertFalse(sm.is_unrecorded("old-session"))

    def test_new_chat_is_unrecorded_until_answered(self):
        self.assertEqual(sm.started("s1", "startup", "C:/project"), sm.WAITING)
        self.assertTrue(sm.is_unrecorded("s1"))

    def test_yes_answer_makes_recorded(self):
        sm.started("s1", "startup", "C:/project")
        sm.set_mode("s1", sm.RECORDED)
        self.assertFalse(sm.is_unrecorded("s1"))

    def test_no_answer_makes_unrecorded(self):
        sm.started("s1", "startup", "C:/project")
        sm.set_mode("s1", sm.UNRECORDED)
        self.assertEqual(sm.mode("s1"), sm.UNRECORDED)

    def test_invalid_mode_rejected(self):
        with self.assertRaises(ValueError):
            sm.set_mode("s1", "maybe")

    def test_resume_and_compact_do_not_change_mode(self):
        sm.started("s1", "startup", "C:/project")
        sm.set_mode("s1", sm.UNRECORDED)
        self.assertEqual(sm.started("s1", "resume", "C:/project"), sm.UNRECORDED)
        self.assertEqual(sm.started("s1", "compact", "C:/project"), sm.UNRECORDED)

    def test_old_session_stays_recorded_on_resume(self):
        self.assertEqual(sm.started("old", "resume", "C:/project"), sm.RECORDED)
        self.assertEqual(sm.mode("old"), sm.RECORDED)

    def test_clear_hands_previous_choice_to_new_session(self):
        sm.started("s1", "startup", "C:/project")
        sm.set_mode("s1", sm.UNRECORDED)
        sm.ended("s1", "clear", "C:/project")
        self.clock += 2
        self.assertEqual(sm.started("s2", "clear", "C:/project"), sm.UNRECORDED)

    def test_clear_from_old_recorded_session_hands_recorded(self):
        sm.ended("old", "clear", "C:/project")
        self.assertEqual(sm.started("s2", "clear", "C:/project"), sm.RECORDED)

    def test_stale_clear_handoff_asks_again(self):
        sm.set_mode("s1", sm.RECORDED)
        sm.ended("s1", "clear", "C:/project")
        self.clock += sm.HANDOFF_S + 1
        self.assertEqual(sm.started("s2", "clear", "C:/project"), sm.WAITING)

    def test_clear_handoff_does_not_cross_folders(self):
        sm.set_mode("s1", sm.RECORDED)
        sm.ended("s1", "clear", "C:/project-a")
        self.assertEqual(sm.started("s2", "clear", "C:/project-b"), sm.WAITING)

    def test_end_other_than_clear_leaves_no_handoff(self):
        sm.set_mode("s1", sm.RECORDED)
        sm.ended("s1", "logout", "C:/project")
        self.assertEqual(sm.started("s2", "clear", "C:/project"), sm.WAITING)

    # The desktop app reports /clear as "startup" and does not send SessionEnd reliably:
    # the choice of an answered chat active in the same folder in the last 15 minutes is taken over
    def transcript(self, sid: str, age_s: float) -> str:
        folder = ROOT / "project"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{sid}.jsonl"
        path.write_text("{}\n", encoding="utf-8")
        os.utime(path, (self.clock - age_s, self.clock - age_s))
        return str(path)

    def test_startup_takes_over_from_recent_recorded_chat(self):
        self.transcript("s1", 240)
        sm.set_mode("s1", sm.RECORDED)
        new = str(ROOT / "project" / "s2.jsonl")
        self.assertEqual(sm.started("s2", "startup", "C:/project", new), sm.RECORDED)
        self.assertEqual(sm.mode("s2"), sm.RECORDED)

    def test_startup_takes_over_from_recent_unrecorded_chat(self):
        self.transcript("s1", 60)
        sm.set_mode("s1", sm.UNRECORDED)
        self.assertEqual(sm.started("s2", "startup", "C:/project", str(ROOT / "project" / "s2.jsonl")), sm.UNRECORDED)

    def test_startup_does_not_take_over_from_chat_older_than_15_minutes(self):
        self.transcript("s1", sm.RECENT_CHAT_S + 1)
        sm.set_mode("s1", sm.RECORDED)
        self.assertEqual(sm.started("s2", "startup", "C:/project", str(ROOT / "project" / "s2.jsonl")), sm.WAITING)

    def test_startup_does_not_take_over_from_scheduled_task(self):
        self.transcript("task", 30)
        sm.set_mode("task", sm.RECORDED, reason=sm.SCHEDULED_TASK)
        self.assertEqual(sm.started("s2", "startup", "C:/project", str(ROOT / "project" / "s2.jsonl")), sm.WAITING)

    def test_startup_unanswered_chat_conflicts_with_parallel_recorded(self):
        # Review finding: the /clear of an unanswered (counted unrecorded) chat must not become recorded
        # because of a parallel recorded chat (#37)
        self.transcript("s1", 30)
        sm.started("s1", "startup", "C:/project")
        self.transcript("s3", 60)
        sm.set_mode("s3", sm.RECORDED)
        self.assertEqual(sm.started("s2", "startup", "C:/project", str(ROOT / "project" / "s2.jsonl")), sm.WAITING)

    def test_clear_handoff_wins_over_recent_chat(self):
        self.transcript("s3", 30)
        sm.set_mode("s3", sm.RECORDED)
        sm.set_mode("s1", sm.UNRECORDED)
        sm.ended("s1", "clear", "C:/project")
        self.assertEqual(sm.started("s2", "clear", "C:/project", str(ROOT / "project" / "s2.jsonl")), sm.UNRECORDED)

    def test_startup_asks_when_choices_conflict(self):
        self.transcript("s1", 30)
        self.transcript("s3", 60)
        sm.set_mode("s1", sm.RECORDED)
        sm.set_mode("s3", sm.UNRECORDED)
        self.assertEqual(sm.started("s2", "startup", "C:/project", str(ROOT / "project" / "s2.jsonl")), sm.WAITING)

    def test_taken_over_choice_is_taken_over_again_on_next_clear(self):
        self.transcript("s1", 30)
        sm.set_mode("s1", sm.RECORDED)
        sm.started("s2", "startup", "C:/project", self.transcript("s2", 0))
        self.clock += sm.RECENT_CHAT_S + 60
        self.transcript("s2", 10)
        self.assertEqual(sm.started("s4", "startup", "C:/project", str(ROOT / "project" / "s4.jsonl")), sm.RECORDED)

    def test_unrecorded_sessions_list(self):
        sm.started("s1", "startup", "C:/p")
        sm.started("s2", "startup", "C:/p")
        sm.set_mode("s2", sm.RECORDED)
        sm.started("s3", "startup", "C:/p")
        sm.set_mode("s3", sm.UNRECORDED)
        self.assertEqual(sm.unrecorded_sessions(), {"s1", "s3"})

    def test_empty_session_id_not_stored_counts_recorded(self):
        # A call without an id (e.g. a health measurement) must leave no entry; otherwise every hook without an id
        # would count as unrecorded
        sm.started("", "startup", "C:/p")
        self.assertEqual(sm.read()["sessions"], {})
        self.assertFalse(sm.is_unrecorded(""))

    def test_old_faulty_empty_id_entry_ignored(self):
        sm.FILE.write_text('{"sessions": {"": {"mode": "waiting", "cwd": "", "time": 1, "reason": "x"}}, "handoff": {}}',
                           encoding="utf-8")
        self.assertFalse(sm.is_unrecorded(""))
        self.assertEqual(sm.unrecorded_sessions(), set())

    def test_corrupt_file_makes_every_session_unrecorded(self):
        # If it counted as empty, unrecorded chats would silently turn recorded and the nightly task would process them
        # (#37: the safe side)
        sm.FILE.write_text("{broken", encoding="utf-8")
        self.assertTrue(sm.is_unrecorded("old-session"))
        self.assertTrue(sm.is_unrecorded("s1"))
        self.assertTrue(sm.unrecorded_filter()("any-session"))
        self.assertTrue(all(isinstance(t, sm.CorruptFile) for t in self.traces) and self.traces)   # a trace was left

    def test_corrupt_file_is_not_overwritten(self):
        sm.FILE.write_text("{broken", encoding="utf-8")
        with self.assertRaises(sm.CorruptFile):
            sm.set_mode("s1", sm.RECORDED)
        with self.assertRaises(sm.CorruptFile):
            sm.started("s1", "startup", "C:/p")
        self.assertEqual(sm.FILE.read_text(encoding="utf-8"), "{broken")

    def test_cli_gives_error_code_on_corrupt_file(self):
        sm.FILE.write_text("{broken", encoding="utf-8")
        err = io.StringIO()
        with redirect_stderr(err):
            self.assertEqual(sm.main(["set", "s1", "recorded"]), 1)
        self.assertIn("ERROR", err.getvalue())
        self.assertEqual(sm.FILE.read_text(encoding="utf-8"), "{broken")

    def test_old_recorded_entries_are_pruned(self):
        sm.set_mode("old", sm.RECORDED)
        self.clock += sm.RETENTION_S + 1
        sm.set_mode("new", sm.RECORDED)
        self.assertNotIn("old", sm.read()["sessions"])

    def test_unrecorded_entry_is_never_pruned(self):
        # Once pruned it would count as an "old session without an entry" and turn recorded; the nightly scan would
        # process the transcript
        sm.set_mode("private", sm.UNRECORDED)
        sm.started("unanswered", "startup", "C:/p")
        self.clock += sm.RETENTION_S * 10
        sm.set_mode("new", sm.RECORDED)
        self.assertTrue(sm.is_unrecorded("private"))
        self.assertTrue(sm.is_unrecorded("unanswered"))


class FilePathTest(unittest.TestCase):
    """For guard tests that run in a subprocess: the mode file is chosen by an environment variable, but only under output/."""

    def test_default_is_under_output(self):
        self.assertEqual(sm.file_path({}), common.OUTPUT / "session_mode.json")

    def test_path_under_output_accepted(self):
        path = common.OUTPUT / "test_x" / "m.json"
        self.assertEqual(sm.file_path({sm.ENV_VAR: str(path)}), path)

    def test_path_outside_output_ignored(self):
        outside = common.vault_path("index.md")
        self.assertEqual(sm.file_path({sm.ENV_VAR: str(outside)}), common.OUTPUT / "session_mode.json")

    def test_relative_escape_ignored(self):
        escape = common.OUTPUT / ".." / ".." / "log.md"
        self.assertEqual(sm.file_path({sm.ENV_VAR: str(escape)}), common.OUTPUT / "session_mode.json")


if __name__ == "__main__":
    unittest.main()
