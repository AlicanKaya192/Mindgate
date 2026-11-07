"""What the installer writes for Google Gemini CLI (experimental; tried only with sample payloads, not the real CLI).

Places (geminicli.com docs, read 7 November 2026; the site says Antigravity CLI replaced Gemini CLI for unpaid and
Google One users on 18 June 2026):
- hooks:        ~/.gemini/settings.json, only its "hooks" key — {"hooks": {"BeforeTool": [matcher groups]}}, the same
                shape as Claude's settings.json; Antigravity does not load hooks from this file
- instructions: ~/.gemini/GEMINI.md — Antigravity reads this file too, so when both are chosen it holds the one shared
                block and AGENTS.md gets none
- skills:       ~/.agents/skills (Gemini CLI reads it as an alias of ~/.gemini/skills; shared with Codex)
- agents:       ~/.gemini/agents/<name>.md (name, description, tools, model …; no `skills` or `effort` field)

Gemini CLI's documents show no "ask" decision, so what Claude would ask (an unlisted site, a single delete) is denied.
"""
from __future__ import annotations

from pathlib import Path

import antigravity as ag
import installer_lib as lib

HOOKS_TEMPLATE = lib.REPO / "setup" / "gemini" / "hooks.template.json"
TOOLS = {   # Claude tool → Gemini CLI tools (geminicli.com docs/reference/tools)
    "Read": ["read_file", "read_many_files"], "Grep": ["grep_search"], "Glob": ["glob", "list_directory"],
    "Bash": ["run_shell_command"], "WebSearch": ["google_web_search"], "WebFetch": ["web_fetch"],
    "Write": ["write_file"], "Edit": ["replace"], "Skill": [],
}
HEADER = {
    "en": "Mindgate rules for Gemini CLI. They were written for Claude Code: read \"Claude\" as yourself. Here the "
          "command, write and site guards run (what Claude would ask is refused); session records, the context check "
          "and the scheduled tasks do not.",
    "tr": "Gemini CLI için Mindgate kuralları. Claude Code için yazıldılar: \"Claude\" geçen yeri kendin diye oku. Burada "
          "komut, yazma ve site kapıları çalışır (Claude'un soracağı şey reddedilir); oturum kayıtları, bağlam ölçümü ve "
          "zamanlanmış görevler çalışmaz.",
}
SHARED_HEADER = {
    "en": "Mindgate rules for Gemini CLI and Antigravity (both read this file). They were written for Claude Code: read "
          "\"Claude\" as yourself. The command, write and site guards run in both (Gemini CLI refuses what Claude would "
          "ask); session records, the context check and the scheduled tasks do not.",
    "tr": "Gemini CLI ve Antigravity için Mindgate kuralları (ikisi de bu dosyayı okur). Claude Code için yazıldılar: "
          "\"Claude\" geçen yeri kendin diye oku. Komut, yazma ve site kapıları ikisinde de çalışır (Gemini CLI, Claude'un "
          "soracağı şeyi reddeder); oturum kayıtları, bağlam ölçümü ve zamanlanmış görevler çalışmaz.",
}


def settings_path(home: Path) -> Path:
    return ag.gemini_dir(home) / "settings.json"


def instructions_path(home: Path) -> Path:
    return ag.gemini_dir(home) / "GEMINI.md"


def agents_dir(home: Path) -> Path:
    return ag.gemini_dir(home) / "agents"


def hook_specs(values: lib.Values, system_folder: str, language: str) -> list:
    return lib.hook_specs(values, system_folder, language, HOOKS_TEMPLATE)


def instructions_text(current: str | None, core: str, language: str, shared: bool) -> str:
    """Antigravity may read GEMINI.md too, so its 24,000-byte limit applies."""
    header = (SHARED_HEADER if shared else HEADER)[language]
    return lib.marked_instructions(current, f"{header}\n\n{core}", ag.INSTRUCTIONS_LIMIT, "~/.gemini/GEMINI.md")


def convert_agent(bundle: lib.Bundle) -> lib.Bundle:
    """Gemini CLI frontmatter: tools translated; model dropped (it inherits the session's); effort and skills dropped."""
    return lib.convert_agent_frontmatter(bundle, "Gemini CLI", TOOLS, None, {"effort", "skills"})
