"""Builds the chat app pack: instructions and knowledge files for ChatGPT, Gemini and similar chat apps.

Chat apps run no hooks and no scripts, so the pack is text only: a short and a long instruction text, a guide for
the person, and three knowledge files (rules, schema, templates) taken from the vault sources of the chosen language.
Every file is secret-scanned in memory first; if anything is found, nothing is written. The target folder must be new
or empty, and every file is opened with mode "x", so nothing is ever overwritten.

Run (from setup/): py -3 -I chat_pack.py --language en --out <new folder>
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # the -I flag does not add the script folder to the path
import installer_lib as lib  # noqa: E402
import installer_messages as msg  # noqa: E402

sys.path.insert(0, str(lib.VAULT_SOURCE / "_system"))
import secret_scan  # noqa: E402

SHORT_LIMIT = 1500   # the smaller custom instruction field of chat apps
LONG_LIMIT = 5000    # the larger one (project or custom assistant instructions)
NO_GATES_LINE = {
    "en": "Guards, automatic records and scripts do not work in chat apps.",
    "tr": "Kapılar, otomatik kayıt ve betikler sohbet uygulamalarında çalışmaz.",
}
STATIC_FILES = {"instructions-short": "txt", "instructions-long": "txt", "README": "md"}
KNOWLEDGE_FILES = {"rules": "md", "schema": "md", "templates": "md"}
OUTPUTS = tuple(STATIC_FILES.items()) + tuple(KNOWLEDGE_FILES.items())
TEMPLATE_HEADING = {"en": "# Note templates", "tr": "# Not şablonları"}


def check_language(language: str) -> None:
    if language not in msg.LANGUAGES:
        raise lib.InstallerError(f"Unknown language: {language} (known: {', '.join(msg.LANGUAGES)})")


def output_name(stem: str, suffix: str, names: dict) -> str:
    return f"{lib.mapped(names, 'chat_pack', stem)}.{suffix}"


def static_text(language: str, stem: str) -> str:
    """A hand-written pack text: English in `chat-pack/`, other languages in `locales/<language>/chat-pack/`."""
    root = lib.REPO / "chat-pack" if language == "en" else lib.LOCALES / language / "chat-pack"
    return (root / f"{stem}.{STATIC_FILES[stem]}").read_text(encoding="utf-8")


def chat_values(language: str) -> lib.Values:
    """Install placeholders have no real value in a chat app; they become plain words."""
    return lib.Values(Path("<vault>"), "python", Path("~"), language, msg.USER_WORD[language])


def vault_text(parts: tuple, language: str) -> str:
    return lib.file_content(parts, language, chat_values(language)).decode("utf-8")


def rules_text(language: str) -> str:
    return vault_text(("rules", "general-rules.md"), language)


def schema_text(language: str) -> str:
    return vault_text(("CLAUDE.md",), language)


def templates_text(language: str) -> str:
    """All note templates in one file; each one fenced, so its frontmatter is not read as the file's own."""
    names = lib.load_names(language)
    sections = [TEMPLATE_HEADING[language]]
    for template in sorted((lib.VAULT_SOURCE / "_templates").glob("*.md")):
        local = lib.translate_parts(("_templates", template.name), names)[-1]
        body = vault_text(("_templates", template.name), language).rstrip("\n")
        sections.append(f"## {local}\n\n````markdown\n{body}\n````")
    return "\n\n".join(sections) + "\n"


def pack_contents(language: str) -> dict:
    """{output file name: text}, built in memory."""
    names = lib.load_names(language)
    knowledge = {"rules": rules_text, "schema": schema_text, "templates": templates_text}
    contents = {output_name(stem, suffix, names): static_text(language, stem) for stem, suffix in STATIC_FILES.items()}
    contents |= {output_name(stem, suffix, names): knowledge[stem](language) for stem, suffix in KNOWLEDGE_FILES.items()}
    return contents


def secret_findings(contents: dict) -> list:
    return [f"{file}:{number}: {kind} {value}"
            for file, text in contents.items()
            for number, line in enumerate(text.splitlines(), 1)
            for kind, value in secret_scan.scan_line(line)]


def check_target(out: Path) -> None:
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise lib.InstallerError(f"The target must be a new or empty folder: {out}")


def build(language: str, out: Path) -> list:
    """Writes the pack into `out`; returns the written paths."""
    check_language(language)
    check_target(out)
    contents = pack_contents(language)
    findings = secret_findings(contents)
    if findings:
        raise lib.InstallerError("Secret scan found something; nothing was written:\n" + "\n".join(findings))
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for file, text in contents.items():
        path = out / file
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        written.append(path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the chat app pack (ChatGPT, Gemini and similar)")
    parser.add_argument("--language", required=True, choices=list(msg.LANGUAGES))
    parser.add_argument("--out", required=True, type=Path, help="a new or empty folder")
    args = parser.parse_args()
    try:
        written = build(args.language, args.out.expanduser().resolve())
    except lib.InstallerError as error:
        print(error, file=sys.stderr)
        return 1
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
