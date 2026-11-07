"""What the installer writes for Google Antigravity (experimental; tried only with sample payloads, not the real CLI).

Places (antigravity.google docs, 7 November 2026):
- hooks:        ~/.gemini/config/hooks.json — a map of named hook sets; Mindgate owns the "mindgate" set only
- instructions: ~/.gemini/AGENTS.md — Mindgate's text between marked lines; a rule file is cut at 24,000 bytes
- skills:       ~/.gemini/config/skills/<name>/SKILL.md (name, description)
- agents:       ~/.gemini/config/agents/<name>.md (name, description, tools, model, skills)

Only the guards run in Antigravity (command, write and site guard, PreToolUse). Session records, the context check,
the agent gate and the search context need Claude's hooks and are not installed here.
"""
from __future__ import annotations

import json
from pathlib import Path

import installer_lib as lib

HOOK_SET = "mindgate"
INSTRUCTIONS_LIMIT = 24_000   # bytes: Antigravity cuts a longer rule file
HOOKS_TEMPLATE = lib.REPO / "setup" / "antigravity" / "hooks.template.json"
TOOLS = {   # Claude tool → Antigravity tools (docs/hooks "Supported Tool Names")
    "Read": ["view_file"], "Grep": ["grep_search"], "Glob": ["find_by_name", "list_dir"], "Bash": ["run_command"],
    "WebSearch": ["search_web"], "WebFetch": ["read_url_content"], "Write": ["write_to_file"],
    "Edit": ["replace_file_content", "multi_replace_file_content"], "Skill": [],
}
MODELS = {"haiku": "flash", "sonnet": "inherit", "opus": "pro"}   # Antigravity: inherit | flash | pro
HEADER = {
    "en": "Mindgate rules for Antigravity. They were written for Claude Code: read \"Claude\" as yourself. Here the "
          "command, write and site guards run; session records, the context check and the scheduled tasks do not.",
    "tr": "Antigravity için Mindgate kuralları. Claude Code için yazıldılar: \"Claude\" geçen yeri kendin diye oku. "
          "Burada komut, yazma ve site kapıları çalışır; oturum kayıtları, bağlam ölçümü ve zamanlanmış görevler çalışmaz.",
}


def gemini_dir(home: Path) -> Path:
    return home / ".gemini"


def hooks_path(home: Path) -> Path:
    return gemini_dir(home) / "config" / "hooks.json"


def instructions_path(home: Path) -> Path:
    return gemini_dir(home) / "AGENTS.md"


def skills_dir(home: Path) -> Path:
    return gemini_dir(home) / "config" / "skills"


def agents_dir(home: Path) -> Path:
    return gemini_dir(home) / "config" / "agents"


def hook_set(values: lib.Values, system_folder: str) -> dict:
    """The "mindgate" hook set with the install's Python, vault and script folder filled in."""
    mindgate = json.loads(HOOKS_TEMPLATE.read_text(encoding="utf-8"))[HOOK_SET]
    for group in mindgate["PreToolUse"]:
        for hook in group["hooks"]:
            hook["command"] = lib.fill(hook["command"].replace("/_system/", f"/{system_folder}/"), values)
    return mindgate


def parse_hooks(raw: bytes | None) -> dict:
    if raw is None:
        return {}
    data = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(data, dict):
        raise lib.InstallerError("~/.gemini/config/hooks.json is not a JSON object; it was not touched")
    return data


def hooks_bytes(data: dict) -> bytes:
    return (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def add_hook_set(raw: bytes | None, mindgate: dict) -> bytes:
    """The user's file with the "mindgate" set added or replaced; every other set stays as it was."""
    return hooks_bytes({**parse_hooks(raw), HOOK_SET: mindgate})


def remove_hook_set(raw: bytes) -> bytes:
    data = parse_hooks(raw)
    data.pop(HOOK_SET, None)
    return hooks_bytes(data)


def instructions_text(current: str | None, core: str, language: str) -> str:
    """The user's AGENTS.md with Mindgate's block added (or refreshed); refused when it passes the size limit."""
    return lib.marked_instructions(current, f"{HEADER[language]}\n\n{core}", INSTRUCTIONS_LIMIT, "~/.gemini/AGENTS.md")


def convert_agent(bundle: lib.Bundle) -> lib.Bundle:
    """A Claude agent file in Antigravity's frontmatter: tools and model translated, `effort` dropped (no such field)."""
    return lib.convert_agent_frontmatter(bundle, "Antigravity", TOOLS, MODELS, {"effort"})
