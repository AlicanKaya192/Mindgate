"""Checks a YouTube title and its thumbnail text as one pair, in Turkish or English.

    python -I title_check.py --title "..." --thumb "3 AYDA"
    python -I title_check.py titles.txt              # one title per line, fewest issues first
    python -I title_check.py --lang tr --json titles.txt

Errors break a YouTube rule; warnings and notes are craft heuristics.
"""
import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lang  # noqa: E402

YOUTUBE_TITLE_LIMIT = 100      # YouTube Help, "Edit video settings", checked 2026-11-13
SEARCH_CUT = 60                # observation, not an official limit
MOBILE_CUT = 40                # observation, not an official limit
MAX_CAPS_WORDS = 2
MIN_CAPS_LENGTH = 4            # shorter all-caps words are usually acronyms (SQL, API)
MAX_THUMB_WORDS = 3
MIN_STEM = 4
SOFTENING = {("p", "b"), ("ç", "c"), ("t", "d"), ("k", "ğ"), ("k", "g")}   # kitap -> kitabı
SEVERITY_ORDER = {"error": 0, "warning": 1, "note": 2}


def issue(code, severity, pack, **values):
    return {"code": code, "severity": severity,
            "text": pack["messages"]["title_issues"][code].format(**values)}


def length_issues(title, pack):
    n = len(title)
    if n > YOUTUBE_TITLE_LIMIT:
        return [issue("over_limit", "error", pack, n=n)]
    if n > SEARCH_CUT:
        return [issue("search_cut", "warning", pack, n=n)]
    if n > MOBILE_CUT:
        return [issue("mobile_cut", "note", pack, n=n)]
    return []


def caps_issues(title, pack):
    words = [w.replace("’", "'").split("'")[0].strip(".,!?:;\"()") for w in title.split()]
    caps = [w for w in words if len(w) >= MIN_CAPS_LENGTH and w.isalpha() and w.isupper()]
    return [issue("caps", "warning", pack, n=len(caps))] if len(caps) > MAX_CAPS_WORDS else []


def content_issues(title, norm, pack):
    found = []
    if not lang.count_numbers(title) and not lang.count_names(title):
        found.append(issue("no_concrete", "warning", pack))
    vague = lang.matched_entries(norm, pack["vague"])
    if vague:
        found.append(issue("vague", "warning", pack, w=", ".join(vague)))
    return found


def same_word(a, b):
    """The same word with another ending: one starts with the other (kanal/kanalı, thumbnail/thumbnails),
    or only a softened last consonant differs (kitap/kitabı). Look-alikes such as model/modern are not."""
    short, long_ = sorted((a, b), key=len)
    if short == long_:
        return True
    if len(short) < MIN_STEM:
        return False
    if long_.startswith(short):
        return True
    return long_.startswith(short[:-1]) and (short[-1], long_[len(short) - 1]) in SOFTENING


def content_words(text, code, pack):
    common = set(pack["common"])
    return [w for w in lang.tokens(text, code) if w not in common]


def thumb_issues(title, thumb, code, pack):
    words = lang.tokens(thumb, code)
    found = []
    if len(words) > MAX_THUMB_WORDS:
        found.append(issue("thumb_words", "warning", pack, n=len(words)))
    thumb_words = content_words(thumb, code, pack)
    title_words = content_words(title, code, pack)
    shared = [w for w in thumb_words if any(same_word(w, t) for t in title_words)]
    if shared and len(shared) == len(thumb_words):
        found.append(issue("thumb_repeats", "warning", pack, w=", ".join(shared)))
    elif shared:
        found.append(issue("thumb_partial", "note", pack, w=", ".join(shared)))
    return found


def check(title, thumb, code):
    pack = lang.load_pack(code)
    title, thumb = title.strip(), thumb.strip()
    if not title:
        return [issue("empty", "error", pack)]
    norm = lang.normalize(title, code)
    found = length_issues(title, pack) + caps_issues(title, pack) + content_issues(title, norm, pack)
    if thumb:
        found += thumb_issues(title, thumb, code, pack)
    return found


def check_pair(title, thumb, choice):
    code = lang.resolve(choice, f"{title} {thumb}")
    row = {"title": title.strip(), "thumb": thumb.strip(), "lang": code}
    if code != lang.UNKNOWN:
        row["issues"] = check(title, thumb, code)
    return row


def weight(row):
    severities = [i["severity"] for i in row.get("issues", [])]
    return tuple(severities.count(s) for s in SEVERITY_ORDER)


def print_row(row):
    thumb = f"   ({row['thumb']})" if row["thumb"] else ""
    print(f"\n  [{row['lang']}] {row['title']}{thumb}")
    if row["lang"] == lang.UNKNOWN:
        print(f"    {lang.both('lang_unknown')}")
        return
    if not row["issues"]:
        print(f"    {lang.message(row['lang'], 'ok')}")
    labels = lang.message(row["lang"], "severity")
    for found in sorted(row["issues"], key=lambda i: SEVERITY_ORDER[i["severity"]]):
        print(f"    {labels[found['severity']]:<8} {found['text']}")


def main():
    parser = argparse.ArgumentParser(description="Check a YouTube title and thumbnail text as one pair.")
    parser.add_argument("file", nargs="?", help="text file, one title per line")
    parser.add_argument("--title")
    parser.add_argument("--thumb", default="", help="thumbnail text, checked against every title")
    parser.add_argument("--lang", choices=("auto", *lang.LANGUAGES), default="auto")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not args.title and not args.file:
        parser.error("give --title or a file")
    titles = [args.title] if args.title else [t for t in lang.read_text(args.file).splitlines() if t.strip()]
    if not titles:
        raise ValueError(f"{args.file}: {lang.both('no_lines')}")
    rows = sorted((check_pair(t, args.thumb, args.lang) for t in titles),
                  key=lambda r: (r["lang"] == lang.UNKNOWN, weight(r)))
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return
    for row in rows:
        print_row(row)
    print()


if __name__ == "__main__":
    lang.run(main)
