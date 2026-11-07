"""Tests of the attention line of session_log.py: repeated rule violations and topics on hold."""
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import OUTPUT  # noqa: E402

SESSION_LOG = importlib.util.find_spec("session_log") is not None
# One form, as in the core instructions ("[Second brain: …]"): English or Turkish by the install language
HEADERS = ("[Second brain: attention]", "[İkinci beyin: dikkat]")
VIOLATIONS = """| Date | Rule | What happened | Why it happened | What was done | Noticed by | Chat |
|---|---|---|---|---|---|---|
| 2026-09-20 | #22 | old | old reason | x | y | z |
| 2026-10-13 | #22 | deleted | habit | x | y | z |
| 2026-10-14 | #22 | again | cleanup habit | x | y | z |
| 2026-10-14 | #24 | once | speed | x | y | z |
"""
PENDING = ("- [ ] P-030 | on-hold | 2026-10-13 | External advisor feature | [[x]]\n"
           "- [ ] P-031 | decision | 2026-10-13 | Something else | [[y]]\n")


@unittest.skipUnless(SESSION_LOG, "session_log.py is written by another part and is not present yet")
class AttentionTest(unittest.TestCase):
    def setUp(self):
        import session_log
        self.sl = session_log
        OUTPUT.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=OUTPUT)
        root = Path(self.temporary.name)
        self.old = (session_log.VIOLATIONS, session_log.PENDING)
        session_log.VIOLATIONS, session_log.PENDING = root / "violations.md", root / "pending.md"
        session_log.VIOLATIONS.write_text(VIOLATIONS, encoding="utf-8")
        session_log.PENDING.write_text(PENDING, encoding="utf-8")

    def tearDown(self):
        self.sl.VIOLATIONS, self.sl.PENDING = self.old
        self.temporary.cleanup()

    def test_only_rules_broken_twice_in_recent_days(self):
        self.assertEqual(self.sl.repeated_violations(14, "2026-10-14"), [("#22", 2, "cleanup habit")])

    def test_topics_on_hold(self):
        self.assertEqual(self.sl.on_hold_topics(), ["P-030 External advisor feature"])

    def test_attention_line_holds_both(self):
        line = self.sl.attention_line()
        self.assertIn("P-030", line)
        self.assertTrue(line.startswith(HEADERS))


if __name__ == "__main__":
    unittest.main()
