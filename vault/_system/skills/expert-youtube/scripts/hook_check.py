"""Checks spoken YouTube hooks (the first seconds of a video) in Turkish or English.

    python -I hook_check.py --hook "one line"
    python -I hook_check.py hooks.txt              # one hook per line, strongest first
    python -I hook_check.py --lang tr --json hooks.txt

Each hook gets five features marked missing / weak / present, a fix for each weak spot and the
hook pattern its words match. There is no score: the checks are heuristics, not a view prediction.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lang  # noqa: E402

MISSING, WEAK, PRESENT = 0, 1, 2
ADDRESS_WINDOW = 6
LENGTH_TOLERANCE = 3
PATTERN_CHARS = 300        # a hook is one or two sentences; longer text is cut before pattern matching
FEATURES = ("specificity", "address", "stakes", "curiosity", "length")
PATTERNS = json.loads((lang.HERE / "hook_patterns.json").read_text(encoding="utf-8"))["patterns"]


def specificity(text, norm, pack):
    concrete = lang.count_numbers(text) + lang.count_names(text)
    vague = lang.count_entries(norm, pack["vague"])
    filler = lang.count_entries(norm, pack["filler"])
    if concrete and not vague:
        return PRESENT
    if concrete or (not vague and filler < 2):
        return WEAK
    return MISSING


def is_address(word, position, pack):
    if word in pack["address_words"]:
        return True
    if position == 0 and word in pack["imperatives"]:
        return True
    suffix = pack["address_suffix"]
    return bool(suffix and len(word) >= pack["address_suffix_min_length"]
                and word not in pack["address_exclude"] and re.search(suffix, word))


def address(words, pack):
    hits = [i for i, w in enumerate(words) if is_address(w, i, pack)]
    if not hits:
        return MISSING
    return PRESENT if hits[0] < ADDRESS_WINDOW else WEAK


def stakes(text, norm, pack):
    found = lang.count_entries(norm, pack["stakes"])
    concrete = lang.count_numbers(text)
    if found >= 2 or (found and concrete):
        return PRESENT
    return WEAK if found else MISSING


def curiosity(text, norm, pack):
    opened = lang.count_entries(norm, pack["curiosity"]) + text.rstrip().endswith("?")
    if not opened:
        return MISSING
    return WEAK if lang.count_entries(norm, pack["closers"]) else PRESENT


def length(words, pack):
    band = pack["hook_words"]
    if band["min"] <= len(words) <= band["max"]:
        return PRESENT
    if band["min"] - LENGTH_TOLERANCE <= len(words) <= band["max"] + LENGTH_TOLERANCE:
        return WEAK
    return MISSING


def classify(norm, code):
    """The pattern with the most matching expressions; on a tie, the one matching earliest."""
    best, best_key = None, None
    norm = norm[:PATTERN_CHARS]
    for order, pattern in enumerate(PATTERNS):
        found = [m for m in (re.search(rx, norm) for rx in pattern["match"][code]) if m]
        if not found:
            continue
        key = (-len(found), min(m.start() for m in found), order)
        if best_key is None or key < best_key:
            best, best_key = pattern, key
    return best


def analyze(text, code):
    pack = lang.load_pack(code)
    text = text.strip()
    norm = lang.normalize(text, code)
    words = lang.tokens(text, code)
    levels = {
        "specificity": specificity(text, norm, pack),
        "address": address(words, pack),
        "stakes": stakes(text, norm, pack),
        "curiosity": curiosity(text, norm, pack),
        "length": length(words, pack),
    }
    pattern = classify(norm, code)
    return {
        "text": text,
        "lang": code,
        "words": len(words),
        "features": {f: {"level": lv, "fix": None if lv == PRESENT else pack["messages"]["fixes"][f]}
                     for f, lv in levels.items()},
        "pattern": pattern["id"] if pattern else None,
        "pattern_name": pattern["name"][code] if pattern else None,
    }


def rank(results):
    """Strongest first: the weakest feature decides, then how many features are present."""
    def strength(result):
        levels = [f["level"] for f in result["features"].values()]
        return (min(levels), levels.count(PRESENT))
    return sorted(results, key=strength, reverse=True)


def check_line(line, choice):
    code = lang.resolve(choice, line)
    if code == lang.UNKNOWN:
        return {"text": line.strip(), "lang": lang.UNKNOWN}
    return analyze(line, code)


def print_result(result):
    print(f"\n  {result['text']}")
    if result["lang"] == lang.UNKNOWN:
        print(f"    {lang.both('lang_unknown')}")
        return
    msg = lang.load_pack(result["lang"])["messages"]
    name = result["pattern_name"] or msg["no_pattern"]
    print(f"    [{result['lang']}] {msg['pattern']}: {name} · {result['words']} {msg['words']}")
    for feature, info in result["features"].items():
        line = f"    {msg['features'][feature]:<12} {msg['levels'][info['level']]}"
        print(line + (f"  -> {info['fix']}" if info["fix"] else ""))


def read_lines(args):
    if args.hook:
        return [args.hook]
    lines = [line for line in lang.read_text(args.file).splitlines() if line.strip()]
    if not lines:
        raise ValueError(f"{args.file}: {lang.both('no_lines')}")
    return lines


def main():
    parser = argparse.ArgumentParser(description="Check spoken YouTube hooks (Turkish or English).")
    parser.add_argument("file", nargs="?", help="text file, one hook per line")
    parser.add_argument("--hook", help="a single hook")
    parser.add_argument("--lang", choices=("auto", *lang.LANGUAGES), default="auto")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not args.hook and not args.file:
        parser.error("give --hook or a file")
    results = [check_line(line, args.lang) for line in read_lines(args)]
    known = rank([r for r in results if r["lang"] != lang.UNKNOWN])
    ordered = known + [r for r in results if r["lang"] == lang.UNKNOWN]
    if args.json:
        print(json.dumps(ordered, ensure_ascii=False, indent=1))
        return
    for result in ordered:
        print_result(result)
    footer_lang = known[0]["lang"] if known else "en"
    if len(known) > 1:
        print(f"\n  {lang.message(footer_lang, 'best')}: {known[0]['text']}")
    print(f"\n  ({lang.message(footer_lang, 'heuristic')})\n")


if __name__ == "__main__":
    lang.run(main)
