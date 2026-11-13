"""YouTube chapters: suggests them from a transcript, or checks a list you wrote against YouTube's rules.

    python -I chapters.py transcript.srt --target 6          # suggest
    python -I chapters.py --check list.txt --duration 612     # check "00:00 Title" lines

YouTube's rules (YouTube Help, "Video Chapters", checked 2026-11-13): the first timestamp is 00:00,
at least three timestamps in ascending order, each chapter at least 10 seconds. A list that breaks
one is not shown as chapters. Lines without a timestamp are skipped and reported, not counted.
Suggested titles are topic words: drafts to rewrite, not titles.
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dead_air  # noqa: E402
import lang  # noqa: E402

MIN_CHAPTERS = 3
MIN_CHAPTER_SECONDS = 10.0
WINDOW_SECONDS = 30.0      # how much speech on each side is compared for a topic shift
STEM_LENGTH = 5            # words sharing their first five letters count as one topic word
MIN_WORD_LENGTH = 3
TITLE_WORDS = 3
PAUSE_BIAS = 0.1           # keeps a topic shift without a pause in the running
LIST_LINE = re.compile(r"^\s*((?:\d+:[0-5]\d|\d{1,3}):[0-5]\d)(?!\d)\s*[-–—:]?\s*(.*)$")


def parse_clock(text):
    value = 0.0
    for part in text.split(":"):
        value = value * 60 + int(part)
    return value


def format_clock(value):
    hours, rest = divmod(int(round(value)), 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours}:{minutes:02}:{secs:02}" if hours else f"{minutes:02}:{secs:02}"


def parse_chapter_list(text):
    """Returns (entries, skipped): timestamped lines as (seconds, title), and every other non-empty line."""
    entries, skipped = [], []
    for line in text.splitlines():
        if not line.strip():
            continue
        match = LIST_LINE.match(line)
        if match:
            entries.append((parse_clock(match.group(1)), match.group(2).strip()))
        else:
            skipped.append(line.strip())
    return entries, skipped


def problem(code, detail=""):
    return {"code": code, "detail": detail}


def validate(entries, duration=None):
    """Problems that stop YouTube from showing the list as chapters; an empty list means valid."""
    found = []
    if not entries or entries[0][0] != 0:
        found.append(problem("first_not_zero"))
    if len(entries) < MIN_CHAPTERS:
        found.append(problem("too_few", str(len(entries))))
    starts = [start for start, _ in entries]
    for i, start in enumerate(starts):
        is_last = i == len(starts) - 1
        end = duration if is_last else starts[i + 1]
        if end is None:
            continue
        if end <= start:
            found.append(problem("duration_short" if is_last else "not_ascending",
                                 format_clock(start if is_last else end)))
        elif end - start < MIN_CHAPTER_SECONDS:
            found.append(problem("too_short", format_clock(start)))
    return found


def content_words(cues, code, common):
    return [w for cue in cues for w in lang.tokens(cue.text, code)
            if len(w) >= MIN_WORD_LENGTH and w not in common and not w.isdigit()]


def topic_words(cues, code, common):
    return [w[:STEM_LENGTH] for w in content_words(cues, code, common)]


def shift(cues, index, code, common):
    """How different the speech is just before and just after a cue start (0 same, 1 unrelated)."""
    at = cues[index].start
    before = set(topic_words([c for c in cues[:index] if c.start >= at - WINDOW_SECONDS], code, common))
    after = set(topic_words([c for c in cues[index:] if c.start < at + WINDOW_SECONDS], code, common))
    if not before or not after:
        return 0.0
    return 1 - len(before & after) / len(before | after)


def boundary_scores(cues, code, common):
    scores = []
    for i in range(1, len(cues)):
        pause = max(0.0, cues[i].start - cues[i - 1].end)
        scores.append(((pause + PAUSE_BIAS) * shift(cues, i, code, common), cues[i].start))
    return sorted(scores, reverse=True)


def pick_boundaries(scores, total, count):
    chosen = []
    for _, start in scores:
        if len(chosen) == count:
            break
        edges = [0.0, total] + chosen
        if all(abs(start - e) >= MIN_CHAPTER_SECONDS for e in edges):
            chosen.append(start)
    return sorted(chosen)


def draft_title(cues, code, common):
    """The most frequent topics, each shown as its most frequent whole word."""
    forms = {}
    for word in content_words(cues, code, common):
        forms.setdefault(word[:STEM_LENGTH], Counter())[word] += 1
    ranked = sorted(forms.values(), key=lambda c: sum(c.values()), reverse=True)[:TITLE_WORDS]
    return " ".join(lang.capitalize(c.most_common(1)[0][0], code) for c in ranked)


def suggest(cues, pack, target):
    if not cues:
        return []
    code, common = pack["code"], set(pack["common"])
    starts = [0.0] + pick_boundaries(boundary_scores(cues, code, common), cues[-1].end, target - 1)
    ends = starts[1:] + [cues[-1].end]
    return [(start, draft_title([c for c in cues if start <= c.start < end], code, common))
            for start, end in zip(starts, ends)]


def print_result(entries, problems, skipped, code, suggested):
    msg = lang.load_pack(code)["messages"]
    print(f"[{code}]")
    for start, title in entries:
        print(f"{format_clock(start)} {title}")
    print()
    for line in skipped:
        print("  " + msg["chapter_skipped"].format(t=line))
    if problems:
        print(msg["chapters_invalid"])
        for p in problems:
            print("  - " + msg["chapter_problems"][p["code"]].format(n=p["detail"], t=p["detail"]))
    else:
        print(msg["chapters_valid"])
    if suggested:
        print(msg["draft_titles"])


def target_value(text):
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return value


def main():
    parser = argparse.ArgumentParser(description="Suggest or check YouTube chapters.")
    parser.add_argument("transcript", nargs="?", help=".srt, .vtt or Whisper-style .json transcript")
    parser.add_argument("--check", help="a chapter list to check, one '00:00 Title' per line")
    parser.add_argument("--duration", type=float, help="video length in seconds (checks the last chapter)")
    parser.add_argument("--target", type=target_value, default=6, help="how many chapters to suggest")
    parser.add_argument("--lang", choices=("auto", *lang.LANGUAGES), default="auto")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if bool(args.transcript) == bool(args.check):
        parser.error("give a transcript or --check, not both")
    if args.check:
        text = lang.read_text(args.check)
        entries, skipped = parse_chapter_list(text)
        duration, suggested = args.duration, False
    else:
        cues = dead_air.parse_cues(lang.read_text(args.transcript))
        if not cues:
            raise ValueError(f"{args.transcript}: {lang.both('no_cues')}")
        text = " ".join(c.text for c in cues)
    code = lang.resolve(args.lang, text)
    if code == lang.UNKNOWN:
        raise ValueError(lang.both("lang_unknown"))
    if not args.check:
        entries, skipped = suggest(cues, lang.load_pack(code), args.target), []
        duration, suggested = cues[-1].end, True
    problems = validate(entries, duration)
    if args.json:
        print(json.dumps({"lang": code, "chapters": [{"start": format_clock(s), "title": t} for s, t in entries],
                          "skipped": skipped, "problems": problems}, ensure_ascii=False, indent=1))
    else:
        print_result(entries, problems, skipped, code, suggested)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    lang.run(main)
