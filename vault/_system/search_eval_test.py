"""search_eval.py tests: finding the rank and the summary measures (hit@k, MRR)."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import search_eval as se  # noqa: E402


class SearchEvalTest(unittest.TestCase):
    def test_find_rank_of_first_expected(self):
        self.assertEqual(se.find_rank(["a", "b", "c"], ["c", "b"]), 2)
        self.assertIsNone(se.find_rank(["a", "b"], ["x"]))

    def test_summary_hit_and_mrr(self):
        summary = se.summarize([1, 2, 4, None])
        self.assertEqual(summary["hit@1"], 0.25)
        self.assertEqual(summary["hit@3"], 0.5)
        self.assertEqual(summary["hit@5"], 0.75)
        self.assertEqual(summary["mrr"], round((1 + 0.5 + 0.25) / 4, 3))

    def test_exam_file_is_valid(self):
        questions = json.loads(se.EXAM.read_text(encoding="utf-8"))["questions"]
        self.assertGreaterEqual(len(questions), 20)
        self.assertTrue(all(q["question"] and q["expected"] for q in questions))

    def test_expected_notes_exist_in_this_vault(self):
        """The exam names notes by file name in the install language (`general-rules` / `genel-kurallar`)."""
        stems = {p.stem for p in se.search.VAULT.rglob("*.md")}
        expected = {note for q in json.loads(se.EXAM.read_text(encoding="utf-8"))["questions"] for note in q["expected"]}
        self.assertEqual(sorted(expected - stems), [])


if __name__ == "__main__":
    unittest.main()
