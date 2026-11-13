"""Turns a timestamped transcript into an edit decision list: long pauses, filler-only cues, restarts.

    python -I dead_air.py transcript.srt            # .srt, .vtt or Whisper-style .json
    python -I dead_air.py transcript.vtt --floor 0.8 --json

It prints the cuts; it never touches the video. The percentage is measured on speech time only, so a
long silent demo in the video makes it look bigger than it is.
"""
import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lang  # noqa: E402

DEFAULT_FLOOR = 0.6     # seconds of silence before a pause is worth cutting; our default, tune per speaker
BREATH = 0.15           # kept on each side of a cut pause so speech does not sound clipped
MIN_RESTART_WORDS = 2
RESTART_GAP = 0.05      # a restart has a pause before it; rolling captions that touch end to end do not
TIMESTAMP = re.compile(r"(?:(\d+):)?(\d{1,2}):(\d{2})[.,](\d{3})")
CUE_LINE = re.compile(TIMESTAMP.pattern + r"\s*-->\s*" + TIMESTAMP.pattern)
TAG = re.compile(r"<[^>]*>")


@dataclass(frozen=True)
class Cue:
    start: float
    end: float
    text: str


def seconds(hours, minutes, secs, millis):
    return int(hours or 0) * 3600 + int(minutes) * 60 + int(secs) + int(millis) / 1000


def parse_whisper(text):
    """Whisper-style JSON: {"segments": [{"start", "end", "text"}]} or the bare list of segments."""
    data = json.loads(text)
    segments = data.get("segments") if isinstance(data, dict) else data
    if not isinstance(segments, list):
        raise ValueError("JSON transcript: expected a list of segments")
    try:
        return [Cue(float(s["start"]), float(s["end"]), str(s["text"]).strip()) for s in segments]
    except (KeyError, TypeError) as missing:
        raise ValueError(f"JSON transcript: every segment needs start, end and text ({missing})") from None


def parse_timed_text(text):
    """SRT and WebVTT. A timing line opens a cue; an empty line or the next timing line closes it."""
    cues, current, lines = [], None, []

    def close():
        if current:
            cues.append(Cue(seconds(*current[:4]), seconds(*current[4:]), " ".join(lines)))

    for line in text.splitlines():
        timing = CUE_LINE.search(line)
        if timing:
            if lines and lines[-1].isdigit():
                lines.pop()          # the SRT index of this cue, read while the previous cue was open
            close()
            current, lines = timing.groups(), []
        elif not line:
            close()
            current, lines = None, []
        elif current and line.strip():
            lines.append(TAG.sub("", line).strip())
    close()
    return cues


def parse_cues(text):
    text = text.lstrip("﻿")
    if text.lstrip().startswith(("{", "[")):
        return parse_whisper(text)
    return parse_timed_text(text)


def is_filler(cue, code, filler_words):
    words = lang.tokens(cue.text, code)
    return bool(words) and all(w in filler_words for w in words)


def is_restart(earlier, later, code):
    if later.start - earlier.end < RESTART_GAP:
        return False
    first, second = lang.tokens(earlier.text, code), lang.tokens(later.text, code)
    return len(first) >= MIN_RESTART_WORDS and len(second) > len(first) and second[:len(first)] == first


def cut(kind, start, end, text=""):
    return {"kind": kind, "start": round(start, 3), "end": round(end, 3),
            "duration": round(end - start, 3), "text": text}


def find_cuts(cues, pack, floor=DEFAULT_FLOOR):
    code = pack["code"]
    filler_words = set(pack["filler_cue"])
    cuts, last_speech = [], None
    for cue in cues:
        if is_filler(cue, code, filler_words):
            cuts.append(cut("filler", cue.start, cue.end, cue.text))
            continue
        if last_speech and is_restart(last_speech, cue, code):
            cuts.append(cut("repeat", last_speech.start, last_speech.end, last_speech.text))
        last_speech = cue
    for before, after in zip(cues, cues[1:]):
        if after.start - before.end > floor:
            cuts.append(cut("dead", before.end + BREATH, after.start - BREATH))
    return sorted(cuts, key=lambda c: c["start"])


def clock(value):
    hundredths = round(value * 100)
    hours, rest = divmod(hundredths, 360000)
    minutes, rest = divmod(rest, 6000)
    secs = rest / 100
    return f"{hours}:{minutes:02}:{secs:05.2f}" if hours else f"{minutes:02}:{secs:05.2f}"


def summary(cues, cuts):
    span = cues[-1].end - cues[0].start if cues else 0.0
    removed = sum(c["duration"] for c in cuts)
    return {"removed": round(removed, 2), "remaining": round(span - removed, 2),
            "percent": round(removed / span * 100, 1) if span else 0.0}


def floor_value(text):
    value = float(text)
    if value < 2 * BREATH:
        raise argparse.ArgumentTypeError(f"must be at least {2 * BREATH} seconds (two breaths)")
    return value


def main():
    parser = argparse.ArgumentParser(description="Edit decision list from a timestamped transcript.")
    parser.add_argument("file", help=".srt, .vtt or Whisper-style .json transcript")
    parser.add_argument("--floor", type=floor_value, default=DEFAULT_FLOOR, help="pause length in seconds worth cutting")
    parser.add_argument("--lang", choices=("auto", *lang.LANGUAGES), default="auto")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    cues = parse_cues(lang.read_text(args.file))
    if not cues:
        raise ValueError(f"{args.file}: {lang.both('no_cues')}")
    code = lang.resolve(args.lang, " ".join(c.text for c in cues))
    if code == lang.UNKNOWN:
        raise ValueError(lang.both("lang_unknown"))
    cuts = find_cuts(cues, lang.load_pack(code), args.floor)
    totals = summary(cues, cuts)
    if args.json:
        print(json.dumps({"lang": code, "cuts": cuts, **totals}, ensure_ascii=False, indent=1))
        return
    msg = lang.load_pack(code)["messages"]
    print(f"  [{code}]")
    for c in cuts:
        label = msg["cut_kinds"][c["kind"]]
        print(f"  {label:<8} {clock(c['start'])} -> {clock(c['end'])}  {c['duration']:5.2f}s  {c['text']}")
    print(f"\n  {len(cuts)} {msg['cuts']} · {msg['removed']} {totals['removed']}s · "
          f"{msg['remaining']} {totals['remaining']}s · {msg['percent'].format(p=totals['percent'])} {msg['shorter']}\n")


if __name__ == "__main__":
    lang.run(main)
