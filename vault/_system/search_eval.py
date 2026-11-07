"""Retrieval hit rate of search.py: question -> expected notes; hit@1, @3, @5 and MRR.

Why: after the instructions were shortened, Claude finds details more and more through `search.py` and automatic
context, so the hit rate of the search has to be measured. Method: a small, fixed question set (`search_exam.json`);
the "recall@k in retrieval" principle of `expert-ml` applied to our own tool. Replace the sample questions with
questions about your own notes.

Usage (from the vault root):
  python _system/search_eval.py          manual search (all notes)
  python _system/search_eval.py --auto   automatic context (me, rules, log … excluded)
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the -I flag does not add the script folder to the path
import search  # noqa: E402

EXAM = Path(__file__).resolve().parent / "search_exam.json"
TOP = 5


def find_rank(found: list[str], expected: list[str]) -> int | None:
    """Rank (from 1) of the first expected note in the results; None if none is there."""
    return next((i for i, note in enumerate(found, 1) if note in expected), None)


def summarize(ranks: list[int | None]) -> dict:
    n = len(ranks) or 1
    hit = lambda k: round(sum(1 for r in ranks if r and r <= k) / n, 3)  # noqa: E731
    return {"questions": len(ranks), "hit@1": hit(1), "hit@3": hit(3), "hit@5": hit(5),
            "mrr": round(sum(1 / r for r in ranks if r) / n, 3)}


def measure(automatic: bool = False, exam: Path = EXAM) -> tuple[dict, list[dict]]:
    questions = json.loads(exam.read_text(encoding="utf-8"))["questions"]
    notes = search.update_index()
    details = []
    for q in questions:
        found = [r["id"] for r in search.search(q["question"], notes, count=TOP, automatic=automatic)]
        details.append({**q, "rank": find_rank(found, q["expected"]), "found": found[:3]})
    return summarize([d["rank"] for d in details]), details


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    p.add_argument("--auto", action="store_true")
    summary, details = measure(p.parse_args().auto)
    print(" · ".join(f"{k} {v}" for k, v in summary.items()))
    for d in details:
        if not d["rank"] or d["rank"] > 3:
            print(f"  ✗ {d['question'][:60]} → expected {d['expected'][0]}, rank {d['rank'] or '-'}; top 3: {', '.join(d['found'])}")


if __name__ == "__main__":
    main()
