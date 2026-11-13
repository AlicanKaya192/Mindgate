"""Shared language support for the YouTube tools: Turkish and English.

Word lists live in lang_tr.json and lang_en.json, so the logic stays the same for every language.
The tools only read the files they are given and print to the screen. They write nothing: each tool
turns off Python's bytecode cache before importing this module, so no __pycache__ folder appears.
"""
import json
import re
import sys
import unicodedata
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
LANGUAGES = ("tr", "en")
UNKNOWN = "unknown"
TURKISH_LETTERS = set("çğışöüÇĞİŞÖÜ")
MIN_DETECTION_HITS = 2
TITLE_CASE_SHARE = 0.6
SUFFIX = r"(?:'[^\W\d_]+)*"
WORD = re.compile(r"[^\W\d_]+" + SUFFIX + r"|\d+(?:[.,]\d+)*" + SUFFIX)
ENCODINGS = ("utf-8-sig", "cp1254")
UTF16_BOMS = (b"\xff\xfe", b"\xfe\xff")
COMBINING_DOT = "̇"


@lru_cache(maxsize=None)
def load_pack(code):
    if code not in LANGUAGES:
        raise ValueError(f"unsupported language: {code}")
    return json.loads((HERE / f"lang_{code}.json").read_text(encoding="utf-8"))


def normalize(text, code):
    """Lowercases with the language's own rules (Turkish I/İ) and unifies apostrophes.

    İ becomes i in every language: in English it only appears in Turkish words, and the default
    lowercasing would leave a stray combining dot that splits the word.
    """
    text = unicodedata.normalize("NFC", text).replace("’", "'").replace("İ", "i")
    if code == "tr":
        text = text.replace("I", "ı")
    return text.lower().replace(COMBINING_DOT, "")


def capitalize(word, code):
    """First letter upper with the language's own rules (Turkish i -> İ, ı -> I)."""
    if not word:
        return word
    first = word[0]
    if code == "tr" and first in "iı":
        first = "İ" if first == "i" else "I"
    return first.upper() + word[1:]


def tokens(text, code):
    """Words and numbers; a suffix after an apostrophe (YouTube'da, %97'si) is dropped."""
    return [w.split("'")[0] for w in WORD.findall(normalize(text, code))]


def detect(text):
    """Returns 'tr', 'en' or 'unknown'. Short or mixed text is unknown rather than guessed."""
    hits = {}
    for code in LANGUAGES:
        common = set(load_pack(code)["common"])
        hits[code] = sum(1 for w in tokens(text, code) if w in common)
    if any(ch in TURKISH_LETTERS for ch in text):
        hits["tr"] += MIN_DETECTION_HITS
    best = max(LANGUAGES, key=hits.get)
    others = [hits[c] for c in LANGUAGES if c != best]
    if hits[best] < MIN_DETECTION_HITS or hits[best] in others:
        return UNKNOWN
    return best


def resolve(choice, text):
    return detect(text) if choice == "auto" else choice


@lru_cache(maxsize=None)
def entry_regex(entry):
    """A list entry becomes a word-bounded pattern; a trailing '*' means 'starts with'."""
    stem = entry[:-1] if entry.endswith("*") else entry
    tail = r"\w*" if entry.endswith("*") else r"\b"
    return re.compile(r"(?<!\w)" + re.escape(stem) + tail)


def count_entries(normalized_text, entries):
    return sum(len(entry_regex(e).findall(normalized_text)) for e in entries)


def matched_entries(normalized_text, entries):
    return [m for e in entries for m in entry_regex(e).findall(normalized_text)]


def count_numbers(text):
    return len(re.findall(r"\d+(?:[.,]\d+)*", text))


def count_names(text):
    """Capitalised words that do not start a sentence read as named things.

    Title Case text (most words capitalised) says nothing about names, so it counts as none.
    """
    words = [w.strip("\"'“”‘’()[]") for w in text.split()]
    words = [w for w in words if w and w[0].isalpha()]
    capitalised = [w[0].isupper() for w in words]
    if len(words) > 2 and sum(capitalised) / len(words) >= TITLE_CASE_SHARE:
        return 0
    names, sentence_start = 0, True
    for word, is_capital in zip(words, capitalised):
        names += is_capital and not sentence_start
        sentence_start = word.endswith((".", "!", "?", ":"))
    return names


def read_text(path):
    """Reads UTF-8 (with or without BOM) or Windows Turkish; fails loudly instead of guessing."""
    raw = Path(path).read_bytes()
    if raw.startswith(UTF16_BOMS) or b"\x00" in raw:
        raise ValueError(f"{path}: looks like UTF-16; save it as UTF-8")
    for encoding in ENCODINGS:
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"{path}: not UTF-8 or Windows-1254 text")


def use_utf8_output():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def message(code, *keys):
    value = load_pack(code)["messages"]
    for key in keys:
        value = value[key]
    return value


def both(*keys):
    """A message in both languages, for when the language is not known yet."""
    return f"{message('en', *keys)} / {message('tr', *keys)}"


def run(main):
    """Runs a tool; a missing, unreadable or malformed input file ends in one line, not a traceback."""
    use_utf8_output()
    try:
        main()
    except (OSError, ValueError) as error:
        sys.exit(f"error: {error}")
