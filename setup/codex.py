"""What the installer writes for OpenAI Codex CLI (experimental; tried only with sample payloads, not the real CLI).

Places (Codex docs on learn.chatgpt.com, read 7 November 2026):
- hooks:        ~/.codex/hooks.json — {"hooks": {event: [matcher groups]}}, the same shape as Claude's settings.json,
                so Mindgate's groups are added and removed by their command, like Claude's hooks
- instructions: ~/.codex/AGENTS.md — Mindgate's text between marked lines; Codex stops reading instructions at 32 KiB
- skills:       ~/.agents/skills/<name>/SKILL.md (name, description)
- agents:       ~/.codex/agents/<name>.toml (name, description, developer_instructions)

Codex runs a new or changed hook only after the user reviews it with /hooks. Codex has no "ask": a single delete is
left to Codex's own approval, a recursive or protected delete is denied. Hosted web tools do not reach hooks, so the
site guard is not installed. An agent file cannot limit tools, so read-only agents rely on their instructions.
"""
from __future__ import annotations

import json
from pathlib import Path

import installer_lib as lib

INSTRUCTIONS_LIMIT = 32 * 1024   # bytes: Codex stops reading instructions here (project files count too)
HOOKS_TEMPLATE = lib.REPO / "setup" / "codex" / "hooks.template.json"
HEADER = {
    "en": "Mindgate rules for Codex. They were written for Claude Code: read \"Claude\" as yourself. Here the command "
          "and write guards run; the site guard, session records, the context check and the scheduled tasks do not.",
    "tr": "Codex için Mindgate kuralları. Claude Code için yazıldılar: \"Claude\" geçen yeri kendin diye oku. Burada "
          "komut ve yazma kapıları çalışır; site kapısı, oturum kayıtları, bağlam ölçümü ve zamanlanmış görevler çalışmaz.",
}


def codex_dir(home: Path) -> Path:
    return home / ".codex"


def hooks_path(home: Path) -> Path:
    return codex_dir(home) / "hooks.json"


def instructions_path(home: Path) -> Path:
    return codex_dir(home) / "AGENTS.md"


def agents_dir(home: Path) -> Path:
    return codex_dir(home) / "agents"


def skills_dir(home: Path) -> Path:
    return home / ".agents" / "skills"


def hook_specs(values: lib.Values, system_folder: str, language: str) -> list:
    return lib.hook_specs(values, system_folder, language, HOOKS_TEMPLATE)


def instructions_text(current: str | None, core: str, language: str) -> str:
    return lib.marked_instructions(current, f"{HEADER[language]}\n\n{core}", INSTRUCTIONS_LIMIT, "~/.codex/AGENTS.md")


def toml_multiline(text: str) -> str:
    """A TOML multi-line literal string (no escapes needed); a basic string when the text holds three quotes."""
    if "'''" in text:
        return json.dumps(text, ensure_ascii=False)
    return "'''\n" + text + "'''"


def convert_agent(bundle: lib.Bundle) -> lib.Bundle:
    """A Claude agent file as a Codex TOML agent: the Markdown body becomes developer_instructions."""
    (_, data), = bundle.files.items()
    frontmatter, body = lib.split_frontmatter(lib.decode(data), f"agent {bundle.name}")
    fields = dict(line.partition(":")[::2] for line in frontmatter if ":" in line and not line.startswith(" "))
    description = fields.get("description", "").strip()
    if not description:
        raise lib.InstallerError(f"agent {bundle.name}: no description")
    toml = (f"name = {json.dumps(bundle.name)}\n"
            f"description = {json.dumps(description, ensure_ascii=False)}\n"
            f"developer_instructions = {toml_multiline(body.lstrip())}\n")
    return lib.Bundle(bundle.name, {(f"{bundle.name}.toml",): lib.encode(toml)}, ".toml")
