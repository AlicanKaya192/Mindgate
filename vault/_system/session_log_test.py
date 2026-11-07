"""session_log.py tests: secret masking, rule summary, project detection, recording mode, handoff reminder,
optional single-machine rule, daily scan scope and the name map.

Test files go under _system/output/test_session_log/ (outside git); nothing is deleted (#22)."""
import hashlib
import importlib
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
import session_log  # noqa: E402
import session_mode as sm  # noqa: E402

TEST_DIR = common.OUTPUT / "test_session_log"
TR_NAMES = {"folders": {"inbox": "gelen", "sessions": "oturumlar", "rules": "kurallar", "projects": "projeler"},
            "files": {"general-rules": "genel-kurallar", "rule-violations": "kural-ihlalleri"}}


def new_folder() -> Path:
    TEST_DIR.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(dir=TEST_DIR))


def capture(function, *args, **kwargs) -> str:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        function(*args, **kwargs)
    return buffer.getvalue()


class SessionLogTest(unittest.TestCase):
    def setUp(self):
        self.root = new_folder()
        self.old = (session_log.RULES, session_log.VAULT_PROJECTS)

    def tearDown(self):
        session_log.RULES, session_log.VAULT_PROJECTS = self.old

    def test_secrets_are_masked(self):
        fake_key = "sk-" + "a1B2c3D4e5F6g7H8i9J0"
        fake_password = "hidden" + "123"
        text = session_log.mask(f"my key {fake_key} and password: " + fake_password)
        self.assertNotIn(fake_key, text)
        self.assertNotIn(fake_password, text)
        self.assertIn(session_log.MASK, text)

    def test_rule_summary_is_numbered(self):
        session_log.RULES = self.root / "general-rules.md"
        session_log.RULES.write_text("| No | Rule | Why |\n|---|---|---|\n| 1 | **Notes in the vault language.** More. | x |\n"
                                     "| 22 | No deletion without permission. Ask first. | y |\n", encoding="utf-8")
        summary = session_log.rule_summary()
        self.assertIn("#1 Notes in the vault language", summary)
        self.assertIn("#22 No deletion without permission", summary)

    def test_vault_project_by_alias(self):
        session_log.VAULT_PROJECTS = self.root / "projects"
        (session_log.VAULT_PROJECTS / "atlas").mkdir(parents=True)
        (session_log.VAULT_PROJECTS / "atlas" / "atlas.md").write_text("---\naliases: [Project Atlas]\n---\n", encoding="utf-8")
        desktop = Path(self.root) / "Desktop"
        self.assertEqual(session_log.vault_project(str(desktop / "Project Atlas")), "atlas")
        self.assertEqual(session_log.vault_project(str(desktop / "something-else")), "")


class RecordingModeTest(unittest.TestCase):
    """#43: record question in a new chat; the raw record of an unrecorded chat is not written."""

    QUESTION, UNRECORDED = "[Second brain — record question]", "[Second brain — unrecorded chat]"
    INHERITED = "[Second brain — recording mode inherited]"

    def setUp(self):
        self.root = new_folder()
        self.old = (sm.FILE, session_log.SESSIONS_DIR, session_log.print_handoff_cards, common.LANGUAGE)
        sm.FILE = self.root / "session_mode.json"
        session_log.SESSIONS_DIR = self.root / "sessions"
        # Real handoff cards change every session (one may contain the question sentence); the test must not depend on them
        session_log.print_handoff_cards = lambda: None
        self.transcript = self.root / "s.jsonl"
        self.transcript.write_text(json.dumps({"type": "user", "message": {"content": "hello, there is a task"}}) + "\n",
                                   encoding="utf-8")

    def tearDown(self):
        sm.FILE, session_log.SESSIONS_DIR, session_log.print_handoff_cards, common.LANGUAGE = self.old

    def remind(self, source: str, sid: str = "abcd1234-5678", transcript: str = "") -> str:
        return capture(session_log.remind, {"source": source, "cwd": "C:/x", "session_id": sid, "transcript_path": transcript})

    def save(self, sid: str, event: str = "SessionEnd", reason: str = "other") -> list[Path]:
        session_log.save({"transcript_path": str(self.transcript), "session_id": sid, "cwd": "C:/x",
                          "hook_event_name": event, "reason": reason})
        return sorted(session_log.SESSIONS_DIR.glob("*.md")) if session_log.SESSIONS_DIR.is_dir() else []

    def test_new_chat_gets_record_question_and_set_command(self):
        output = self.remind("startup")
        self.assertIn(self.QUESTION, output)
        self.assertIn("session_mode.py\" set abcd1234-5678", output)
        self.assertNotIn("records.py handoff write", output)
        self.assertLess(len(output), 9500)

    def test_record_question_in_turkish_install(self):
        common.LANGUAGE = "tr"
        output = self.remind("startup")
        self.assertIn("[İkinci beyin — kayıt sorusu]", output)
        self.assertIn("Bu sohbetin vault'ta kaydı olsun mu?", output)
        self.assertIn("session_mode.py\" set abcd1234-5678 recorded", output)
        self.assertNotIn(self.QUESTION, output)

    def test_attention_header_has_one_form_per_language(self):
        old = session_log.on_hold_topics
        session_log.on_hold_topics = lambda: ["P-001 later"]
        try:
            self.assertTrue(session_log.attention_line().startswith("[Second brain: attention] "))
            common.LANGUAGE = "tr"
            self.assertTrue(session_log.attention_line().startswith("[İkinci beyin: dikkat] "))
        finally:
            session_log.on_hold_topics = old

    def test_recorded_chat_gets_handoff_reminder_with_id(self):
        sm.set_mode("abcd1234-5678", sm.RECORDED)
        output = self.remind("resume")
        self.assertIn("records.py handoff write --session abcd1234-5678", output)
        self.assertNotIn(self.QUESTION, output)

    def test_unrecorded_chat_gets_no_write_warning(self):
        sm.set_mode("abcd1234-5678", sm.UNRECORDED)
        output = self.remind("resume")
        self.assertIn(self.UNRECORDED, output)
        self.assertNotIn("records.py handoff write", output)
        self.assertNotIn("unprocessed", output)

    def test_clear_inherits_choice_question_not_repeated(self):
        sm.set_mode("old-session", sm.UNRECORDED)
        session_log.session_ended({"transcript_path": str(self.transcript), "session_id": "old-session",
                                   "cwd": "C:/x", "hook_event_name": "SessionEnd", "reason": "clear"})
        output = self.remind("clear", sid="new-session")
        self.assertNotIn(self.QUESTION, output)
        self.assertTrue(sm.is_unrecorded("new-session"))

    def test_desktop_clear_as_startup_inherits_from_recent_chat_and_says_so(self):
        # Desktop /clear: no SessionEnd, the new session is "startup"; the previous chat's transcript is in the same folder and new
        (self.root / "old-session.jsonl").write_text("{}\n", encoding="utf-8")
        sm.set_mode("old-session", sm.RECORDED)
        output = self.remind("startup", sid="new-session", transcript=str(self.root / "new-session.jsonl"))
        self.assertNotIn(self.QUESTION, output)
        self.assertIn(self.INHERITED, output)
        self.assertIn("recorded", output)
        self.assertEqual(sm.mode("new-session"), sm.RECORDED)
        self.assertIn('set new-session recorded --reason "scheduled task"', output)

    def test_unrecorded_inherited_prints_both_notes_and_task_exception(self):
        (self.root / "old-session.jsonl").write_text("{}\n", encoding="utf-8")
        sm.set_mode("old-session", sm.UNRECORDED)
        output = self.remind("startup", sid="new-session", transcript=str(self.root / "new-session.jsonl"))
        self.assertIn(self.INHERITED, output)
        self.assertIn(self.UNRECORDED, output)
        self.assertIn("If you are a scheduled task", output.split(self.UNRECORDED)[1])

    def test_unrecorded_session_raw_record_not_written(self):
        sm.set_mode("private-session", sm.UNRECORDED)
        self.assertEqual(self.save("private-session"), [])

    def test_unanswered_session_raw_record_not_written(self):
        sm.started("unanswered-session", "startup", "C:/x")
        self.assertEqual(self.save("unanswered-session", event="PreCompact"), [])

    def test_recorded_session_raw_record_written(self):
        sm.set_mode("open-session", sm.RECORDED)
        self.assertEqual(len(self.save("open-session")), 1)


class SingleMachineTest(unittest.TestCase):
    """Optional rule #17: the fingerprint check runs only when `optional_rules.single_machine` is on."""

    def setUp(self):
        self.old = (common.CONFIG, session_log.scan, sys.argv)
        self.calls = []
        session_log.scan = lambda: self.calls.append("scan")

    def tearDown(self):
        common.CONFIG, session_log.scan, sys.argv = self.old

    def test_rule_off_by_default(self):
        self.assertTrue(session_log.this_machine({}))
        self.assertTrue(session_log.this_machine({"optional_rules": {"single_machine": False, "machine_sha256": "0" * 64}}))

    def test_rule_on_compares_fingerprint(self):
        own = session_log.machine_fingerprint()
        self.assertEqual(own, hashlib.sha256(session_log.socket.gethostname().lower().encode()).hexdigest())
        self.assertTrue(session_log.this_machine({"optional_rules": {"single_machine": True, "machine_sha256": own}}))
        self.assertFalse(session_log.this_machine({"optional_rules": {"single_machine": True, "machine_sha256": "0" * 64}}))

    def test_rule_on_without_fingerprint_counts_no_machine(self):
        self.assertFalse(session_log.this_machine({"optional_rules": {"single_machine": True}}))

    def test_main_stops_on_another_machine_only_when_rule_on(self):
        sys.argv = ["session_log.py", "scan"]
        common.CONFIG = {"optional_rules": {"single_machine": True, "machine_sha256": "0" * 64}}
        session_log.main()
        self.assertEqual(self.calls, [])
        common.CONFIG = {}
        session_log.main()
        self.assertEqual(self.calls, ["scan"])


class DailyScanTest(unittest.TestCase):
    """`scan` reads only vault sessions unless `daily.scan_all_projects` is on."""

    def setUp(self):
        self.root = new_folder()
        self.old = (sm.FILE, session_log.SESSIONS_DIR, session_log.TRANSCRIPTS_DIR, session_log.LAST_SCAN, common.CONFIG)
        sm.FILE = self.root / "session_mode.json"
        session_log.SESSIONS_DIR = self.root / "sessions"
        session_log.TRANSCRIPTS_DIR = self.root / "projects"
        session_log.LAST_SCAN = self.root / "last_scan.txt"
        for sid, cwd in (("vault-session", common.VAULT / "_system"), ("other-session", common.VAULT.parent / "other-project")):
            folder = session_log.TRANSCRIPTS_DIR / sid.split("-")[0]
            folder.mkdir(parents=True)
            (folder / f"{sid}.jsonl").write_text(json.dumps({"type": "user", "cwd": str(cwd),
                                                             "message": {"content": "a task for the scan"}}) + "\n",
                                                 encoding="utf-8")
            sm.set_mode(sid, sm.RECORDED)

    def tearDown(self):
        sm.FILE, session_log.SESSIONS_DIR, session_log.TRANSCRIPTS_DIR, session_log.LAST_SCAN, common.CONFIG = self.old

    def records(self) -> list[str]:
        return sorted(p.name for p in session_log.SESSIONS_DIR.glob("*.md")) if session_log.SESSIONS_DIR.is_dir() else []

    def test_default_scans_only_vault_sessions(self):
        common.CONFIG = {}
        output = capture(session_log.scan)
        self.assertIn("1 transcripts scanned (vault sessions only)", output)
        self.assertEqual(len(self.records()), 1)
        self.assertIn("vault-se", self.records()[0])

    def test_scan_all_projects_from_config(self):
        common.CONFIG = {"daily": {"scan_all_projects": True}}
        output = capture(session_log.scan)
        self.assertIn("2 transcripts scanned (all projects)", output)
        self.assertEqual(len(self.records()), 2)

    def test_in_vault(self):
        self.assertTrue(session_log.in_vault(str(common.VAULT)))
        self.assertTrue(session_log.in_vault(str(common.VAULT / "_system")))
        self.assertFalse(session_log.in_vault(str(common.VAULT.parent / (common.VAULT.name + "-other"))))
        self.assertFalse(session_log.in_vault(""))


class NameMapTest(unittest.TestCase):
    def test_turkish_name_map_gives_turkish_record_path(self):
        old = common.NAMES
        common.NAMES = TR_NAMES
        try:
            importlib.reload(session_log)
            self.assertEqual(session_log.SESSIONS_DIR, common.VAULT / "gelen" / "oturumlar")
            self.assertEqual(session_log.RULES, common.VAULT / "kurallar" / "genel-kurallar.md")
            self.assertEqual(session_log.VIOLATIONS, common.VAULT / "kurallar" / "kural-ihlalleri.md")
        finally:
            common.NAMES = old
            importlib.reload(session_log)
        self.assertEqual(session_log.SESSIONS_DIR, common.VAULT / "inbox" / "sessions")


if __name__ == "__main__":
    unittest.main(verbosity=1)
