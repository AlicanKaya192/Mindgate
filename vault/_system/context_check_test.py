"""context_check.py tests: context measurement, one warning, a new warning after compaction, summary record.

Test files go under _system/output/test_context_check/ (outside git); nothing is deleted (#22)."""
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
import context_check as cc  # noqa: E402
import session_mode as sm  # noqa: E402

TEST_DIR = common.OUTPUT / "test_context_check"
SETTING = {"context_window": {"work_end_percent": 40, "warning_percent": 60, "compact_percent": 70, "default_window": 200000,
                              "windows": {"model-large": 1000000}}}


def assistant(tokens: int, model: str = "model-large", side: bool = False) -> dict:
    return {"type": "assistant", "isSidechain": side,
            "message": {"model": model, "usage": {"input_tokens": 10, "cache_read_input_tokens": tokens - 20,
                                                  "cache_creation_input_tokens": 5, "output_tokens": 5}}}


class ContextCheckTest(unittest.TestCase):
    def setUp(self):
        TEST_DIR.mkdir(parents=True, exist_ok=True)
        root = Path(tempfile.mkdtemp(dir=TEST_DIR))
        self.old = (cc.SETTINGS, cc.STATE, cc.SESSIONS_DIR, sm.FILE, common.LANGUAGE)
        cc.SETTINGS, cc.STATE, cc.SESSIONS_DIR = root / "config.json", root / "state.json", root / "sessions"
        sm.FILE = root / "session_mode.json"
        cc.SETTINGS.write_text(json.dumps(SETTING), encoding="utf-8")
        self.transcript = root / "session.jsonl"

    def tearDown(self):
        cc.SETTINGS, cc.STATE, cc.SESSIONS_DIR, sm.FILE, common.LANGUAGE = self.old

    def write(self, *lines: dict) -> dict:
        self.transcript.write_text("\n".join(json.dumps(s) for s in lines) + "\n", encoding="utf-8")
        return {"session_id": "abc12345-x", "transcript_path": str(self.transcript)}

    def test_last_main_message_measured_side_chain_skipped(self):
        self.write(assistant(300_000), assistant(900_000, side=True), {"type": "user"})
        self.assertEqual(cc.last_context(self.transcript), (300_000, "model-large"))

    def test_window_from_table_else_default_large_if_exceeded(self):
        setting = SETTING["context_window"]
        self.assertEqual(cc.window("model-large", 10, setting), 1_000_000)
        self.assertEqual(cc.window("unknown", 10, setting), 200_000)
        self.assertEqual(cc.window("unknown", 250_000, setting), 1_000_000)

    def test_real_config_has_the_keys(self):
        setting = json.loads(common.CONFIG_FILE.read_text(encoding="utf-8"))["context_window"]
        for key in ("work_end_percent", "warning_percent", "compact_percent", "default_window", "windows"):
            self.assertIn(key, setting)

    def test_silent_below_threshold(self):
        self.assertEqual(cc.stop(self.write(assistant(300_000))), "")

    def test_work_end_note_once_at_forty_then_warning_at_sixty(self):
        first = cc.stop(self.write(assistant(450_000)))
        self.assertIn("If the work is going on, continue", first)
        self.assertEqual(cc.stop(self.write(assistant(500_000))), "")
        self.assertIn("Write or update the handoff card", cc.stop(self.write(assistant(600_000))))

    def test_old_state_format_is_read(self):
        cc.STATE.write_text('{"abc12345-x": 620000}', encoding="utf-8")
        self.assertEqual(cc.stop(self.write(assistant(650_000))), "")

    def test_warns_once_at_threshold(self):
        text = cc.stop(self.write(assistant(620_000)))
        self.assertIn("62%", text)
        self.assertIn("--session abc12345-x", text)
        self.assertEqual(cc.stop(self.write(assistant(650_000))), "")

    def test_warns_again_after_compaction(self):
        cc.stop(self.write(assistant(620_000)))
        self.assertEqual(cc.stop(self.write(assistant(80_000))), "")       # compaction: the context shrank
        self.assertIn("61%", cc.stop(self.write(assistant(610_000))))

    def test_no_warning_during_hook_continuation(self):
        data = self.write(assistant(700_000))
        data["stop_hook_active"] = True
        self.assertEqual(cc.stop(data), "")

    def test_before_asks_for_session_id_and_unfinished_work(self):
        text = cc.before({"session_id": "abc12345-x"})
        self.assertIn("abc12345-x", text)
        self.assertIn("exactly where it stopped", text)
        self.assertIn("Write the summary in English", text)

    def test_before_follows_install_language(self):
        common.LANGUAGE = "tr"
        self.assertIn("Write the summary in Turkish", cc.before({"session_id": "abc12345-x"}))

    def test_after_writes_masked_summary(self):
        target = cc.after({"session_id": "abc12345-x", "cwd": "C:/x/Project", "trigger": "auto",
                           "compact_summary": "Work half done. Key sk-ant-api03-" + "a" * 40})
        text = target.read_text(encoding="utf-8")
        self.assertTrue(target.name.endswith(".md") and "-project-abc12345-summary-" in target.name)
        self.assertIn("Work half done", text)
        self.assertNotIn("a" * 40, text)

    def test_after_writes_no_file_for_empty_summary(self):
        self.assertIsNone(cc.after({"session_id": "x", "compact_summary": "  "}))

    def test_unrecorded_chat_context_warning_is_silent(self):
        sm.set_mode("abc12345-x", sm.UNRECORDED)
        self.assertEqual(cc.stop(self.write(assistant(650_000))), "")

    def test_unrecorded_chat_compaction_instruction_does_not_mention_vault(self):
        sm.set_mode("abc12345-x", sm.UNRECORDED)
        text = cc.before({"session_id": "abc12345-x"})
        self.assertIn("exactly where it stopped", text)
        self.assertNotIn("vault", text.lower())

    def test_unrecorded_chat_compaction_summary_not_written(self):
        sm.set_mode("abc12345-x", sm.UNRECORDED)
        self.assertIsNone(cc.after({"session_id": "abc12345-x", "cwd": "C:/x", "compact_summary": "Work half done."}))
        self.assertFalse(cc.SESSIONS_DIR.exists())

    def test_main_stops_on_another_machine_only_when_rule_on(self):
        old_config, old_argv, old_stdin = common.CONFIG, sys.argv, sys.stdin
        data = json.dumps({"session_id": "abc12345-x"})
        try:
            sys.argv = ["context_check.py", "before"]
            outputs = []
            for config in ({"optional_rules": {"single_machine": True, "machine_sha256": "0" * 64}}, {}):
                common.CONFIG = config
                sys.stdin = io.TextIOWrapper(io.BytesIO(data.encode("utf-8")), encoding="utf-8")
                buffer = io.StringIO()
                buffer.reconfigure = lambda **_k: None
                with redirect_stdout(buffer):
                    cc.main()
                outputs.append(buffer.getvalue())
        finally:
            common.CONFIG, sys.argv, sys.stdin = old_config, old_argv, old_stdin
        self.assertEqual(outputs[0], "")
        self.assertIn("abc12345-x", outputs[1])


if __name__ == "__main__":
    unittest.main()
