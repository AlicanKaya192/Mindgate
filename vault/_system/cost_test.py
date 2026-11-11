"""cost.py tests. Fake transcript folder: _system/output/test_cost/ (real transcripts are never touched)."""
import contextlib
import io
import json
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cost  # noqa: E402
import session_mode as sm  # noqa: E402
from common import CONFIG_FILE, OUTPUT  # noqa: E402

ROOT = OUTPUT / "test_cost" / "projects"
PRICES = {"claude-opus-5-5": {"input": 4.0, "output": 20.0, "cache_read": 0.20}}
YESTERDAY = (date.today() - timedelta(days=1)).isoformat()
EARLIER = (date.today() - timedelta(days=3)).isoformat()


def line(**fields) -> str:
    return json.dumps(fields, ensure_ascii=False) + "\n"


def message(mid: str, model: str, tokens_in: int, tokens_out: int, read: int = 0, write_5m: int = 0,
            stamp: str = YESTERDAY + "T10:00:00Z") -> str:
    usage = {"input_tokens": tokens_in, "output_tokens": tokens_out, "cache_read_input_tokens": read,
             "cache_creation_input_tokens": write_5m,
             "cache_creation": {"ephemeral_5m_input_tokens": write_5m, "ephemeral_1h_input_tokens": 0}}
    return line(type="assistant", requestId="r" + mid, timestamp=stamp, message={"id": mid, "model": model, "usage": usage})


class CostTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        project = ROOT / "C--Users-x-Project"
        (project / "s1" / "subagents").mkdir(parents=True, exist_ok=True)
        # the same message repeats on three lines (split into content blocks); it must count once
        (project / "s1.jsonl").write_text(
            line(type="custom-title", customTitle="Trial chat")
            + message("m1", "claude-opus-5-5", 1_000_000, 0) * 3
            + message("m2", "claude-opus-5-5", 0, 100_000, read=1_000_000, write_5m=1_000_000)
            + message("m3", "unknown-model", 10, 10)
            + message("m4", "claude-opus-5-5", 0, 50_000, stamp=EARLIER + "T09:00:00Z"), encoding="utf-8")   # an earlier day of the same session
        (project / "s1" / "subagents" / "agent-a1.jsonl").write_text(message("k1", "claude-opus-5-5", 500_000, 0), encoding="utf-8")
        (project / "s1" / "subagents" / "agent-a1.meta.json").write_text(json.dumps({"agentType": "scout"}), encoding="utf-8")
        # a session running today: not among the finished rows (it changes with every message)
        (project / "s2.jsonl").write_text(message("b1", "claude-opus-5-5", 1, 1, stamp=date.today().isoformat() + "T23:00:00"), encoding="utf-8")
        # an unrecorded (temporary) chat: its title and folder enter no row
        (project / "s3.jsonl").write_text(line(type="custom-title", customTitle="Hidden chat")
                                          + message("g1", "claude-opus-5-5", 10, 10), encoding="utf-8")
        cls.old_mode = sm.FILE
        sm.FILE = OUTPUT / "test_cost" / "session_mode.json"
        sm.set_mode("s3", sm.UNRECORDED)
        cls.rows = cost.rows(ROOT, PRICES)

    @classmethod
    def tearDownClass(cls):
        sm.FILE = cls.old_mode

    def find(self, kind, key_part):
        return [r for r in self.rows if r["kind"] == kind and key_part in r["key"]]

    def test_unrecorded_chat_stays_out_of_cost(self):
        self.assertFalse(any(":s3:" in r["key"] or r["chat"] == "Hidden chat" for r in self.rows))

    def test_repeated_message_counts_once_and_price_is_right(self):
        session = self.find("session", "s1:" + YESTERDAY)[0]
        self.assertEqual(session["input"], 1_000_010)
        self.assertEqual(session["chat"], "Trial chat")
        # 1M input × $4 + 100K output × $20/M + 1M read × $0.20 + 1M write (5 min) × $4 × 1.25 = 4 + 2 + 0.2 + 5
        self.assertAlmostEqual(session["cost_usd"], 11.2, places=6)

    def test_unknown_model_cost_is_not_invented(self):
        session = self.find("session", "s1:" + YESTERDAY)[0]
        self.assertEqual(session["unpriced_models"], "unknown-model")

    def test_subagent_is_a_separate_row_with_its_type(self):
        agent = self.find("agent", "a1")[0]
        self.assertEqual((agent["agent"], agent["input"]), ("scout", 500_000))
        self.assertAlmostEqual(agent["cost_usd"], 2.0, places=6)

    def test_multi_day_session_is_split_by_day(self):
        # Regression: the whole cost of a session that ran for three weeks went to its last day
        earlier = self.find("session", "s1:" + EARLIER)[0]
        self.assertEqual((earlier["output"], earlier["date"]), (50_000, EARLIER))
        self.assertAlmostEqual(earlier["cost_usd"], 1.0, places=6)

    def test_session_of_today_is_not_finished(self):
        finished = cost.finished_rows(self.rows)
        self.assertTrue(any("s1" in r["key"] for r in finished))
        self.assertTrue(all(r["folder"] == "Project" for r in finished))   # the full path is never shown
        self.assertFalse(any("s2" in r["key"] for r in finished))

    def test_prices_are_read_from_config(self):
        prices = cost.read_prices(CONFIG_FILE)
        self.assertTrue(prices)
        self.assertTrue(all({"input", "output", "cache_read"} <= set(p) for p in prices.values()))

    def test_summary_prints_days_and_agents(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            cost.print_summary(self.rows, 7)
        text = out.getvalue()
        self.assertIn("Last 7 days", text)
        self.assertIn("agent scout", text)
        self.assertIn("Trial chat", text)
        self.assertNotIn("Hidden chat", text)

    def test_projects_folder_is_under_home(self):
        self.assertEqual(cost.PROJECTS, Path.home() / ".claude" / "projects")


class FolderNameTest(unittest.TestCase):
    """The transcript folder name starts with the encoded home folder; the user name must never stay in it."""

    def test_linux_home(self):
        self.assertEqual(cost.folder_name("-home-alice-notes", home=Path("/home/alice")), "notes")

    def test_macos_home_and_desktop(self):
        self.assertEqual(cost.folder_name("-Users-alice-Desktop-proj", home=Path("/Users/alice")), "proj")

    def test_windows_user_name_with_a_dash(self):
        self.assertEqual(cost.folder_name("C--Users-john-doe-Desktop-proj", home=Path("C:/Users/john-doe")), "proj")

    def test_the_home_folder_itself(self):
        self.assertEqual(cost.folder_name("C--Users-john-doe", home=Path("C:/Users/john-doe")), "~")

    def test_another_home_on_the_same_computer(self):
        self.assertEqual(cost.folder_name("-home-bob-Desktop-proj", home=Path("/home/alice")), "proj")


if __name__ == "__main__":
    unittest.main(verbosity=1)
