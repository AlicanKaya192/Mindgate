"""agent_gate.py tests: model and task-writing checks.

Test files go under _system/output/test_agent_gate/ (outside git); nothing is deleted (#22)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import agent_gate as ag  # noqa: E402
import common  # noqa: E402

TEST_DIR = common.OUTPUT / "test_agent_gate"


class AgentGateTest(unittest.TestCase):
    def setUp(self):
        TEST_DIR.mkdir(parents=True, exist_ok=True)
        self.transcript = Path(tempfile.mkdtemp(dir=TEST_DIR)) / "session.jsonl"
        self.old_language = common.LANGUAGE

    def tearDown(self):
        common.LANGUAGE = self.old_language

    def data(self, model: str | None, skill: str | None) -> dict:
        lines = [{"type": "user", "message": {"content": "hello"}}]
        if skill:
            lines.append({"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": "Skill", "input": {"skill": skill}}]}})
        self.transcript.write_text("\n".join(json.dumps(s, separators=(",", ":")) for s in lines), encoding="utf-8")
        tool = {"description": "x", "prompt": "y"} | ({"model": model} if model else {})
        return {"tool_input": tool, "transcript_path": str(self.transcript)}

    def test_denies_without_model(self):
        decision, reason = ag.decide(self.data(None, skill="task-writing"))
        self.assertEqual(decision, "deny")
        self.assertIn("model", reason)

    def test_denies_if_skill_not_loaded(self):
        decision, reason = ag.decide(self.data("haiku", skill=None))
        self.assertEqual(decision, "deny")
        self.assertIn("task-writing", reason)

    def test_passes_with_model_and_skill(self):
        self.assertEqual(ag.decide(self.data("sonnet", skill="task-writing")), ("", ""))

    def test_skill_loaded_by_command_counts(self):
        self.transcript.write_text('{"type":"user","message":{"content":"<command-name>/task-writing</command-name>"}}',
                                   encoding="utf-8")
        self.assertTrue(ag.skill_loaded(self.transcript))

    def test_turkish_skill_name_counts(self):
        self.assertEqual(ag.decide(self.data("opus", skill="gorev-yazma")), ("", ""))

    def test_another_skill_does_not_count(self):
        self.assertEqual(ag.decide(self.data("opus", skill="idea"))[0], "deny")

    def test_reason_follows_install_language(self):
        self.assertTrue(ag.decide(self.data(None, skill="task-writing"))[1].startswith("Agent gate (#28)"))
        common.LANGUAGE = "tr"
        self.assertTrue(ag.decide(self.data(None, skill="task-writing"))[1].startswith("Ajan kapısı (#28)"))


if __name__ == "__main__":
    unittest.main()
