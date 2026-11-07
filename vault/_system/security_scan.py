"""Looks for hidden instructions and leak traces in content that enters the vault (rule #27).

Against memory poisoning: if web/PDF content is written into the vault for good, it can affect every
later session. The script only REPORTS; it never changes or deletes a file (rule #22).

Looked for:
  hidden       - invisible Unicode: tag characters (U+E0000-E007F, "ASCII smuggling"), zero-width
                 characters, direction (bidi) controls
  image        - markdown image pointing to an external address (can leak data when loaded)
  instruction  - injection patterns addressed to the model ("ignore previous instructions" etc.). Notes that
                 DESCRIBE security (tags: security), the rules and the schema are exempt from this check; the
                 hidden character check applies to everyone.

Run (from the vault root):
  python _system/security_scan.py                    # the whole vault
  python _system/security_scan.py sources/x.md ...   # only the given files
Exit code: 0 with no findings, 1 otherwise.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the -I flag does not add the script folder to the path
from common import VAULT, name  # noqa: E402

EXCLUDED = {".git", ".obsidian", ".trash", name("output")}
EXEMPT_FOLDERS = {name("rules"), name("_system"), name("_templates")}
EXEMPT_FILES = {"CLAUDE.md"}
SECURITY_TAGS = ("security", "guvenlik")   # tags are written in the vault language

HIDDEN = re.compile("[\U000E0000-\U000E007F\u200b-\u200f\u202a-\u202e\u2060-\u2064\u2066-\u2069\u00ad]")
EXTERNAL_IMAGE = re.compile(r"!\[[^\]]*\]\(\s*<?https?://[^)\s]+")
# The Turkish alternatives stay: a Turkish source can carry a Turkish injection
INSTRUCTION = re.compile(
    r"(?i)(?:ignore|disregard|forget)\s+(?:all\s+|any\s+|the\s+)?(?:previous|prior|above|earlier)\s+(?:instructions|prompts|rules)"
    r"|(?:önceki|yukarıdaki)\s+(?:talimat|kural|komut)\w*\s+(?:yok\s+say|unut|görmezden\s+gel)"
    r"|(?:talimatları|kuralları)\s+(?:yok\s+say|unut|görmezden\s+gel)"
    r"|\byou\s+are\s+now\b|\bnew\s+instructions\s*:|\bsystem\s+prompt\s*:|<\s*/?\s*(?:system|instructions?)\s*>"
    r"|\b(?:to|dear)\s+(?:the\s+)?(?:ai|assistant|claude|llm|agent)\b"
)
SECURITY_TAG = re.compile(rf"^tags:\s*\[[^\]]*\b(?:{'|'.join(SECURITY_TAGS)})\b", re.M)


def is_security_note(text: str) -> bool:
    return bool(SECURITY_TAG.search(text[:600]))


def scan(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as error:
        return [f"{path}: could not be read ({type(error).__name__})"]
    relative = path.relative_to(VAULT) if path.is_relative_to(VAULT) else path
    exempt = (relative.parts[0] in EXEMPT_FOLDERS or relative.name in EXEMPT_FILES or is_security_note(text)) \
        if isinstance(relative, Path) else False
    findings = []
    for no, line in enumerate(text.splitlines(), 1):
        if no == 1:
            line = line.lstrip("\ufeff")  # a BOM at the start of the file is harmless
        hidden = HIDDEN.findall(line)
        if hidden:
            codes = sorted({f"U+{ord(c):04X}" for c in hidden})
            decoded = "".join(chr(ord(c) - 0xE0000) for c in hidden if 0xE0020 <= ord(c) <= 0xE007E)
            extra = f"; decoded hidden text: {decoded[:80]!r}" if decoded else ""
            findings.append(f"{relative}:{no}: hidden - {len(hidden)} invisible characters ({', '.join(codes[:6])}){extra}")
        codeless = re.sub(r"`[^`]*`", "", line)  # examples in inline code are not findings
        if EXTERNAL_IMAGE.search(codeless):
            findings.append(f"{relative}:{no}: image - image pointing to an external address: "
                            f"{EXTERNAL_IMAGE.search(codeless).group(0)[:120]}")
        if not exempt:
            m = INSTRUCTION.search(codeless)
            if m:
                findings.append(f"{relative}:{no}: instruction - pattern addressed to the model: {m.group(0)!r}")
    return findings


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) > 1:
        files = [Path(a) if Path(a).is_absolute() else (Path.cwd() / a) for a in sys.argv[1:]]
    else:
        files = [p for p in sorted(VAULT.rglob("*.md")) if not set(p.relative_to(VAULT).parts) & EXCLUDED]
    findings = [f for path in files for f in scan(path.resolve())]
    for f in findings:
        print(f)
    print(f"\n{len(files)} files scanned, {len(findings)} findings.")
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
