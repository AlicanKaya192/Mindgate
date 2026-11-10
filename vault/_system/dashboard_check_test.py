"""dashboard_check.py tests: end-of-chat reminder, publish record, dashboard address.

Each test works in a new folder under _system/output/test_dashboard_check/ (outside git); nothing is deleted (#22)."""
import io
import json
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
import dashboard_check as dc  # noqa: E402

TEST_DIR = common.OUTPUT / "test_dashboard_check"
URL = "https://claude.ai/artifact/AbC123xyz"


class CheckCase(unittest.TestCase):
    def setUp(self):
        TEST_DIR.mkdir(parents=True, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix="check-", dir=TEST_DIR))
        self.vault = self.root / "My-Vault"
        (self.vault / "_system" / "output").mkdir(parents=True)
        (self.vault / "knowledge").mkdir()
        self.note = self.vault / "knowledge" / "a.md"
        self.note.write_text("# A\n", encoding="utf-8")
        self.config = self.vault / "_system" / "config.json"
        self.config.write_text(json.dumps({"language": "en", "names": {}, "dashboard": {"url": ""}}, indent=1), encoding="utf-8")
        patches = [mock.patch.object(common, "VAULT", self.vault), mock.patch.object(common, "NAMES", {"folders": {}, "files": {}}),
                   mock.patch.object(dc, "CONFIG_FILE", self.config), mock.patch.object(dc.sm, "is_unrecorded", return_value=False)]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def transcript(self, file_path: str, name: str = "t.jsonl") -> Path:
        path = self.root / name
        call = {"type": "assistant", "cwd": str(self.root), "message": {"content": [
            {"type": "tool_use", "name": "Write", "input": {"file_path": file_path, "content": "x"}}]}}
        path.write_text(json.dumps(call) + "\n", encoding="utf-8")
        return path

    def wrote_in_vault(self) -> Path:
        return self.transcript(str(self.note))

    def check(self, transcript: Path, sid: str = "s1", **extra) -> str:
        out = io.StringIO()
        with redirect_stdout(out):
            dc.check({"session_id": sid, "transcript_path": str(transcript), **extra})
        text = out.getvalue()
        return json.loads(text)["hookSpecificOutput"]["additionalContext"] if text else ""

    def touch_vault(self) -> None:
        time.sleep(0.01)
        self.note.write_text("# A\nchanged\n", encoding="utf-8")


class ReminderTest(CheckCase):
    def test_silent_when_the_chat_did_not_write_to_the_vault(self):
        self.assertEqual(self.check(self.transcript(str(self.root / "My-Vault-old" / "a.md"))), "")

    def test_silent_while_a_stop_hook_already_continues(self):
        self.assertEqual(self.check(self.wrote_in_vault(), stop_hook_active=True), "")

    def test_silent_in_an_unrecorded_chat(self):
        with mock.patch.object(dc.sm, "is_unrecorded", return_value=True):
            self.assertEqual(self.check(self.wrote_in_vault()), "")

    def test_not_published_yet_only_informs(self):
        text = self.check(self.wrote_in_vault())
        self.assertIn("/dashboard", text)
        self.assertIn(dc.MESSAGES["en"]["not_published"][:40], text)

    def test_out_of_date_asks_for_an_update(self):
        dc.set_url(URL)
        self.assertIn(dc.MESSAGES["en"]["out_of_date"][:40], self.check(self.wrote_in_vault()))

    def test_silent_after_save(self):
        dc.set_url(URL)
        dc.save()
        self.assertEqual(self.check(self.wrote_in_vault()), "")

    def test_reminds_once_per_vault_state(self):
        dc.set_url(URL)
        transcript = self.wrote_in_vault()
        self.assertNotEqual(self.check(transcript), "")
        self.assertEqual(self.check(transcript), "")       # the same vault state: no second reminder (CLI has no tools)
        self.touch_vault()
        self.assertNotEqual(self.check(transcript), "")    # the vault changed again

    def test_turkish_message(self):
        config = json.loads(self.config.read_text(encoding="utf-8"))
        config["language"] = "tr"
        self.config.write_text(json.dumps(config), encoding="utf-8")
        self.assertIn(dc.MESSAGES["tr"]["not_published"][:40], self.check(self.wrote_in_vault()))

    def test_a_broken_transcript_never_breaks_the_hook(self):
        bad = self.root / "bad.jsonl"
        bad.write_text("{not json\n", encoding="utf-8")
        self.assertEqual(self.check(bad), "")


class SignatureTest(CheckCase):
    def test_output_and_session_records_do_not_change_the_signature(self):
        before = dc.vault_signature()
        (self.vault / "_system" / "output" / "x.md").write_text("x", encoding="utf-8")
        (self.vault / "inbox" / "sessions").mkdir(parents=True)
        (self.vault / "inbox" / "sessions" / "s.md").write_text("x", encoding="utf-8")
        self.assertEqual(dc.vault_signature(), before)

    def test_a_note_change_changes_the_signature(self):
        before = dc.vault_signature()
        self.touch_vault()
        self.assertNotEqual(dc.vault_signature(), before)


class UrlTest(CheckCase):
    def test_set_url_keeps_other_settings(self):
        dc.set_url(URL)
        config = json.loads(self.config.read_text(encoding="utf-8"))
        self.assertEqual((config["dashboard"]["url"], config["language"]), (URL, "en"))
        self.assertEqual(dc.dashboard_url(), URL)

    def test_set_url_refuses_other_addresses(self):
        for bad in ("https://example.com/artifact/x", "http://claude.ai/artifact/x", URL + "/../x", URL + "?a=1"):
            with self.assertRaises(ValueError, msg=bad):
                dc.set_url(bad)
        self.assertEqual(dc.dashboard_url(), "")


class ShellWriteTest(CheckCase):
    def shell(self, command: str, cwd: str) -> bool:
        part = {"type": "tool_use", "name": "Bash", "input": {"command": command}}
        return dc.writes(part, dc.vault_marker(), cwd)

    def test_git_with_a_folder_option_counts(self):
        self.assertTrue(self.shell(f'git -C "{self.vault}" commit -m x', str(self.root)))

    def test_cd_into_the_vault_counts(self):
        self.assertTrue(self.shell(f'cd "{self.vault}" && git add -A', str(self.root)))

    def test_git_bash_path_counts(self):
        posix = self.vault.as_posix()
        bash = "/" + posix[0].lower() + posix[2:]
        self.assertTrue(self.shell(f"cp a.md {bash}/knowledge/a.md", str(self.root)))

    def test_a_reading_command_does_not_count(self):
        self.assertFalse(self.shell(f"grep -n write_text {self.vault.as_posix()}/a.md", str(self.root)))

    def test_a_path_that_leaves_the_vault_does_not_count(self):
        part = {"type": "tool_use", "name": "Write", "input": {"file_path": str(self.vault / ".." / "other" / "a.md")}}
        self.assertFalse(dc.writes(part, dc.vault_marker(), str(self.root)))

    def test_a_new_line_after_the_address_is_refused(self):
        with self.assertRaises(ValueError):
            dc.set_url(URL + "\n")

    def test_a_bad_address_in_the_settings_is_not_used(self):
        config = json.loads(self.config.read_text(encoding="utf-8"))
        config["dashboard"]["url"] = "https://example.com/x"
        self.config.write_text(json.dumps(config), encoding="utf-8")
        self.assertEqual(dc.dashboard_url(), "")


if __name__ == "__main__":
    unittest.main()
