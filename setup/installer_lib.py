"""Shared logic of the Mindgate installer and uninstaller (standard library only).

Rules this code keeps:
- Nothing is written until the person confirms the summary; the plan is built in memory first.
- No file is ever deleted. A new file is opened with mode "x" (it fails instead of overwriting); a changed file is
  first copied to a time-stamped backup; the uninstaller moves files with `os.rename` (never copy-and-delete).
- Folder and file names of a Turkish install come from `locales/tr/names.json`; `.py` files and everything inside a
  skill's `scripts/` folder keep their English names (they are code and import each other by name).
"""
from __future__ import annotations  # lets an old Python reach the version check

import copy
import getpass
import hashlib
import json
import locale
import os
import re
import shutil
import socket
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the -I flag does not add the script folder to the path
import installer_messages as msg  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
VAULT_SOURCE = REPO / "vault"
LOCALES = REPO / "locales"
HOOKS_TEMPLATE = REPO / "setup" / "hooks.template.json"
TASKS_SOURCE = REPO / "setup" / "tasks"
TASKS = ("daily", "weekly")

CLAUDE_DIR = ".claude"
MINDGATE_DIR = "mindgate"
MANIFEST_NAME = "install-manifest.json"
CORE_NAME = "CLAUDE.md"
IMPORT_TARGET = "@~/.claude/mindgate/CLAUDE.md"
IMPORT_MARK = "<!-- mindgate -->"
IMPORT_LINE = f"{IMPORT_TARGET} {IMPORT_MARK}"
BLOCK_START = "<!-- mindgate:start -->"
BLOCK_END = "<!-- mindgate:end -->"
REMOVED_PREFIX = "mindgate-removed-"

PLACEHOLDERS = ("VAULT", "PY", "HOME", "LANG", "USER")
MASTER_COPY = ("_system", "instructions", "global-CLAUDE.md")   # stays a template: install_instructions.py fills it
SKIPPED_DIRS = {"__pycache__", ".git"}
SKIPPED_PATHS = {("_system", "output")}                          # test and lock output of the source repo
FILLED_SUFFIXES = {".md", ".json", ".base", ".txt"}
MIN_PYTHON = (3, 10)
OPTIONAL_HEADING = re.compile(r"(?m)^## (?:Optional rules|İsteğe bağlı kurallar)[ \t]*$")
RULE_ROW = re.compile(r"(?m)^\|\s*(\d+)\s*\|\s*\*\*(.+?)\*\*(.*)$")
TEMPLATE_SCRIPT = re.compile(r"/_system/(\w+)\.py\"?\s*(.*)$")
FRONTMATTER_NAME = re.compile(r"(?m)^name:[ \t]*.*$")
TOML_NAME = re.compile(r"(?m)^name[ \t]*=[ \t]*.*$")
FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.S)


class InstallerError(Exception):
    """A stop with a message for the person; nothing is written after it is raised."""


# ---------- names ----------
def load_names(language: str) -> dict:
    """The English -> local name map of `language`; empty for English."""
    if language == "en":
        return {}
    return json.loads((LOCALES / language / "names.json").read_text(encoding="utf-8"))


def mapped(names: dict, table: str, key: str) -> str:
    return (names.get(table) or {}).get(key, key)


def translate_dir(segment: str, parents: tuple, names: dict) -> str:
    if parents == ("_system", "skills"):
        return mapped(names, "skills", segment)
    return mapped(names, "folders", segment)


def translate_file(segment: str, parents: tuple, names: dict) -> str:
    stem, dot, suffix = segment.rpartition(".")
    if not dot:
        stem, suffix = segment, ""
    if suffix == "py" or not names:
        return segment
    if parents == ("_system", "agents"):
        local = mapped(names, "agents", stem)
    elif parents == ("_templates",):
        local = mapped(names, "templates", stem)
    elif len(parents) >= 3 and parents[:2] == ("_system", "skills"):
        local = (names.get("skill_files") or {}).get(stem) or mapped(names, "files", stem)
    else:
        local = mapped(names, "files", stem)
    return f"{local}.{suffix}" if dot else local


def translate_parts(parts: tuple, names: dict) -> tuple:
    """English relative file path (as parts) -> path in the install language."""
    if not names:
        return tuple(parts)
    out = []
    for i, segment in enumerate(parts):
        parents = tuple(parts[:i])
        if "scripts" in parts[:i + 1]:
            out.append(segment)
        elif i == len(parts) - 1:
            out.append(translate_file(segment, parents, names))
        else:
            out.append(translate_dir(segment, parents, names))
    return tuple(out)


def local_name(key: str, names: dict) -> str:
    """Like the vault's common.name(): a folder or file stem in the install language."""
    return (names.get("folders") or {}).get(key) or (names.get("files") or {}).get(key) or key


# ---------- placeholders ----------
@dataclass
class Values:
    vault: Path
    python: str
    home: Path
    language: str
    user_word: str

    def table(self) -> dict:
        return {"VAULT": self.vault.as_posix(), "PY": self.python, "HOME": self.home.as_posix(),
                "LANG": self.language, "USER": self.user_word}


def fill(text: str, values: Values) -> str:
    for key, value in values.table().items():
        text = text.replace("{{" + key + "}}", value)
    return text


# ---------- vault content ----------
@dataclass
class VaultFile:
    source: tuple      # English relative path parts
    target: tuple      # relative path parts in the install language
    data: bytes


def source_files(root: Path = VAULT_SOURCE) -> list:
    """Relative path parts of every file of the English vault, sorted; caches and test output left out."""
    found = []
    for path in sorted(root.rglob("*")):
        parts = path.relative_to(root).parts
        if not path.is_file() or set(parts) & SKIPPED_DIRS or path.suffix == ".pyc":
            continue
        if any(parts[:len(skip)] == skip for skip in SKIPPED_PATHS):
            continue
        found.append(parts)
    return found


def is_code(parts: tuple) -> bool:
    return parts[-1].endswith(".py") or "scripts" in parts


def locale_only_files(language: str) -> list:
    """Files that exist only in the locale (such as `.obsidian/`); code and config are never taken from a locale."""
    root = LOCALES / "tr" / "vault"
    base = set(source_files())
    extra = []
    for parts in source_files(root):
        if parts in base or is_code(parts) or parts == ("_system", "config.json"):
            continue
        extra.append(parts)
    return extra


def english_obsidian(data: bytes) -> bytes:
    """A Turkish `.obsidian/*.json` with its folder names turned back into the English base names."""
    reverse = {local: base for base, local in (load_names("tr").get("folders") or {}).items()}
    def back(value):
        if isinstance(value, str):
            return "/".join(reverse.get(segment, segment) for segment in value.split("/"))
        if isinstance(value, list):
            return [back(v) for v in value]
        if isinstance(value, dict):
            return {k: back(v) for k, v in value.items()}
        return value
    return (json.dumps(back(json.loads(data.decode("utf-8"))), indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def file_content(parts: tuple, language: str, values: Values) -> bytes:
    """Content of one vault file: code from the English base, text from the locale when it has the file."""
    base = VAULT_SOURCE / Path(*parts)
    localized = LOCALES / language / "vault" / Path(*parts)
    use_locale = language != "en" and not is_code(parts) and localized.is_file()
    data = (localized if use_locale else base).read_bytes()
    if is_code(parts) or parts == MASTER_COPY or base.suffix not in FILLED_SUFFIXES:
        return data
    return fill(data.decode("utf-8"), values).encode("utf-8")


def build_vault(language: str, values: Values, config: dict, today: str) -> list:
    """Every file of a new vault, in memory. Raises InstallerError when two files would get the same name."""
    names = load_names(language)
    files = []
    for parts in source_files():
        if parts == ("_system", "config.json"):
            data = config_bytes(config)
        else:
            data = file_content(parts, language, values)
        files.append(VaultFile(parts, translate_parts(parts, names), data))
    for parts in locale_only_files(language):
        data = (LOCALES / "tr" / "vault" / Path(*parts)).read_bytes()
        if language == "en":
            if parts[0] != ".obsidian":
                continue
            data = english_obsidian(data)
        files.append(VaultFile(parts, translate_parts(parts, names), data))
    files.extend(starter_files(language, names, today))
    targets = [f.target for f in files]
    double = sorted({"/".join(t) for t in targets if targets.count(t) > 1})
    if double:
        raise InstallerError(f"two files would get the same name: {', '.join(double)}")
    return files


def page(kind: str, title: str, description: str, body: str, today: str) -> bytes:
    head = f"---\ntype: {kind}\nstatus: active\ntags: []\ncreated: {today}\nupdated: {today}\n---\n\n"
    text = f"{head}# {title}\n\n> {description}\n" + (f"\n{body}" if body else "")
    return text.encode("utf-8")


def starter_files(language: str, names: dict, today: str) -> list:
    """Empty starting pages, folder entry pages, index.md and log.md in the install language."""
    files, links = [], {"rules": [local_name("general-rules", names)], "inbox": [], "folders": []}
    for key, (kind, title, description, body) in msg.STARTER_PAGES[language].items():
        place = msg.STARTER_FOLDERS[key]
        folders = place if isinstance(place, tuple) else (place,)
        folder = folders[0]
        stem = mapped(names, "files", key)
        target = (*(local_name(f, names) for f in folders), f"{stem}.md")
        files.append(VaultFile((*folders, f"{key}.md"), target, page(kind, title, description, body, today)))
        links["inbox" if folder == "inbox" else "rules" if folder == "rules" else "folders"].append(stem)
    for folder, (title, description) in msg.ENTRY_PAGES[language].items():
        local = local_name(folder, names)
        base = msg.ENTRY_STEMS.get(folder, folder)            # a page named after its folder unless that is a template
        stem = mapped(names, "files", base) if base != folder else local
        files.append(VaultFile((folder, f"{base}.md"), (local, f"{stem}.md"),
                               page("entry", title, description, "", today)))
        links["folders"].append(stem)
    title, description, sections = msg.INDEX_PAGE[language]
    lines = [f"# {title}", "", f"> {description}", ""]
    for section in ("rules", "inbox", "folders"):
        lines += [f"## {sections[section]}", ""] + [f"- [[{stem}]]" for stem in links[section]] + [""]
    files.append(VaultFile(("index.md",), ("index.md",), "\n".join(lines).encode("utf-8")))
    log_title, log_description = msg.LOG_PAGE[language]
    files.append(VaultFile(("log.md",), ("log.md",), f"# {log_title}\n\n> {log_description}\n".encode("utf-8")))
    return files


# ---------- vault config ----------
def base_config() -> dict:
    return json.loads((VAULT_SOURCE / "_system" / "config.json").read_text(encoding="utf-8"))


def config_bytes(config: dict) -> bytes:
    return (json.dumps(config, indent=1, ensure_ascii=False) + "\n").encode("utf-8")


@dataclass
class ConfigChoices:
    language: str
    python: str
    scan_all_projects: bool = False
    git_push: bool = False
    weekly_trending: bool | None = None     # None: not asked (no weekly task installed now); the saved value stays
    optional_rules: list = field(default_factory=list)
    usage_limit: dict = field(default_factory=dict)


def apply_config(config: dict, choices: ConfigChoices) -> dict:
    """A copy of `config` with the install choices written in."""
    new = copy.deepcopy(config)
    names = load_names(choices.language)
    new["language"] = choices.language
    new["python"] = choices.python
    new["names"] = {"folders": dict(names.get("folders") or {}), "files": dict(names.get("files") or {})}
    daily = new.setdefault("daily", {})
    daily["scan_all_projects"] = choices.scan_all_projects
    daily["git_push"] = choices.git_push
    weekly = new.setdefault("weekly", {})
    if choices.weekly_trending is None:
        weekly.setdefault("trending", False)
    else:
        weekly["trending"] = choices.weekly_trending
    rules = new.setdefault("optional_rules", {})
    rules["enabled"] = sorted(choices.optional_rules)
    rules["single_machine"] = 17 in choices.optional_rules
    rules["machine_sha256"] = machine_fingerprint() if 17 in choices.optional_rules else ""
    if 9 in choices.optional_rules:
        rules["usage_limit"] = dict(choices.usage_limit)
    return new


def machine_fingerprint() -> str:
    """The same fingerprint as the vault's session_log.py: SHA-256 of the lower-cased computer name."""
    return hashlib.sha256(socket.gethostname().lower().encode()).hexdigest()


def existing_vault_language(folder: Path) -> str | None:
    """The language of a Mindgate vault in `folder`, or None when the folder holds no Mindgate vault."""
    for system in ("_system", "_sistem"):
        path = folder / system / "config.json"
        if path.is_file():
            try:
                language = json.loads(path.read_text(encoding="utf-8")).get("language")
            except (OSError, ValueError, AttributeError):
                return None
            return language if isinstance(language, str) else None
    return None


def config_path(vault: Path, language: str) -> Path:
    return vault / local_name("_system", load_names(language)) / "config.json"


# ---------- optional rules ----------
@dataclass
class OptionalRule:
    number: int
    title: str


def optional_rules(rules_text: str) -> list:
    parts = OPTIONAL_HEADING.split(rules_text, maxsplit=1)
    if len(parts) < 2:
        return []
    section = re.split(r"(?m)^## ", parts[1], maxsplit=1)[0]
    found = []
    for m in RULE_ROW.finditer(section):
        title = m.group(2).strip().rstrip(":.").strip()
        found.append(OptionalRule(int(m.group(1)), title))
    return found


# ---------- environment (read only) ----------
def python_ok(version=sys.version_info) -> bool:
    return tuple(version[:2]) >= MIN_PYTHON


def suggested_python() -> str:
    return "py -3" if os.name == "nt" else "python3"


def detect_git() -> str | None:
    return shutil.which("git")


def detect_claude_command() -> str | None:
    return shutil.which("claude")


@dataclass
class ObsidianInfo:
    found: bool
    where: str = ""
    config: Path | None = None


def obsidian_places(home: Path) -> tuple:
    """(program paths, settings files) where Obsidian is usually installed. Windows folders are taken from the
    environment only for the real home; with another --home they are looked for inside that folder."""
    real = same_path(home, Path.home())
    if os.name == "nt":
        local = Path(os.environ["LOCALAPPDATA"]) if real and os.environ.get("LOCALAPPDATA") else home / "AppData" / "Local"
        roaming = Path(os.environ["APPDATA"]) if real and os.environ.get("APPDATA") else home / "AppData" / "Roaming"
        programs = [local / "Programs" / "Obsidian" / "Obsidian.exe"]
        if real:
            programs += [Path(os.environ[v]) / "Obsidian" / "Obsidian.exe"
                         for v in ("ProgramFiles", "ProgramFiles(x86)") if os.environ.get(v)]
        return programs, [roaming / "obsidian" / "obsidian.json"]
    if sys.platform == "darwin":
        programs = [home / "Applications" / "Obsidian.app"] + ([Path("/Applications/Obsidian.app")] if real else [])
        return programs, [home / "Library" / "Application Support" / "obsidian" / "obsidian.json"]
    programs = [Path(p) for p in (shutil.which("obsidian"),) if p and real] + [home / "Applications" / "Obsidian.AppImage"]
    configs = [home / ".config" / "obsidian" / "obsidian.json",
               home / ".var" / "app" / "md.obsidian.Obsidian" / "config" / "obsidian" / "obsidian.json",
               home / "snap" / "obsidian" / "current" / ".config" / "obsidian" / "obsidian.json"]
    return programs, configs


def detect_obsidian(home: Path) -> ObsidianInfo:
    programs, configs = obsidian_places(home)
    config = next((c for c in configs if c.is_file()), None)
    program = next((p for p in programs if p.exists()), None)
    if program or config:
        return ObsidianInfo(True, str(program or config), config)
    return ObsidianInfo(False)


def obsidian_language(config: Path | None) -> str | None:
    """A language code from Obsidian's obsidian.json, only when the file has a plain `language` value. Obsidian may
    keep its interface language elsewhere (not in this file); then None is returned and the person is asked."""
    if not config:
        return None
    try:
        value = json.loads(config.read_text(encoding="utf-8")).get("language")
    except (OSError, ValueError, AttributeError):
        return None
    return value.lower()[:2] if isinstance(value, str) and len(value) >= 2 else None


def detect_os_language() -> str:
    """'tr' when the system interface or locale is Turkish, 'en' otherwise."""
    if os.name == "nt":
        try:
            import ctypes
            if ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF == 0x1F:   # LANG_TURKISH
                return "tr"
        except (AttributeError, OSError):
            pass
    candidates = [os.environ.get(v, "") for v in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE")]
    try:
        candidates.append(locale.getlocale()[0] or "")
    except ValueError:
        pass
    return "tr" if any(c.lower().startswith(("tr", "turkish")) for c in candidates) else "en"


def same_path(a: Path, b: Path) -> bool:
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


def real_homes() -> list:
    """Every path that may be the person's real home folder, independent of the HOME/USERPROFILE variables."""
    homes = [Path.home()]
    if os.name == "nt":
        drive = os.environ.get("SystemDrive", "C:")
        try:
            homes.append(Path(drive + "\\") / "Users" / getpass.getuser())
        except (OSError, KeyError):
            pass
    else:
        try:
            import pwd
            homes.append(Path(pwd.getpwuid(os.getuid()).pw_dir))
        except (ImportError, KeyError):
            pass
    return homes


def is_real_home(home: Path) -> bool:
    return any(same_path(home, real) for real in real_homes())


# ---------- settings.json and hooks ----------
@dataclass
class HookSpec:
    id: str
    event: str
    matcher: str | None
    entry: dict

    @property
    def command(self) -> str:
        return self.entry["command"]


def hook_id(event: str, template_command: str) -> str:
    m = TEMPLATE_SCRIPT.search(template_command)
    return f"{event}:{m.group(1)}" + (f" {m.group(2).strip()}" if m and m.group(2).strip() else "") if m else event


def hook_specs(values: Values, system_folder: str, language: str, template_path: Path = HOOKS_TEMPLATE) -> list:
    """The template hooks filled for this install, one spec per command."""
    template = json.loads(template_path.read_text(encoding="utf-8"))
    specs = []
    for event, groups in template["hooks"].items():
        for group in groups:
            for hook in group["hooks"]:
                entry = dict(hook)
                command = hook["command"].replace("/_system/", f"/{system_folder}/")
                entry["command"] = fill(command, values)
                if language == "tr" and "statusMessage" in entry:
                    entry["statusMessage"] = msg.HOOK_STATUS_TR.get(entry["statusMessage"], entry["statusMessage"])
                specs.append(HookSpec(hook_id(event, hook["command"]), event, group.get("matcher"), entry))
    return specs


def parse_settings(raw: bytes | None) -> dict:
    """settings.json as a dict ({} when there is no file). Raises ValueError for invalid JSON and TypeError when
    the content does not have the shape Claude Code uses."""
    if raw is None:
        return {}
    data = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(data, dict):
        raise TypeError("settings.json is not an object")
    hooks = data.get("hooks", {})
    if not isinstance(hooks, dict) or not all(isinstance(g, list) for g in hooks.values()):
        raise TypeError("hooks is not an object of lists")
    for groups in hooks.values():
        if not all(isinstance(g, dict) and isinstance(g.get("hooks", []), list) for g in groups):
            raise TypeError("a hook group is not an object")
    return data


def installed_commands(settings: dict, event: str) -> set:
    return {h.get("command") for g in settings.get("hooks", {}).get(event, []) for h in g.get("hooks", [])
            if isinstance(h, dict)}


def split_present(settings: dict, specs: list) -> tuple:
    """(already installed, not installed) by exact command under the same event."""
    present = [s for s in specs if s.command in installed_commands(settings, s.event)]
    return present, [s for s in specs if s not in present]


def add_hooks(settings: dict, specs: list) -> dict:
    """A copy of `settings` with `specs` added as new groups at the end of each event; nothing else changes."""
    new = copy.deepcopy(settings)
    hooks = new.setdefault("hooks", {})
    groups: dict = {}
    for spec in specs:
        groups.setdefault((spec.event, spec.matcher), []).append(dict(spec.entry))
    for (event, matcher), entries in groups.items():
        group = {"matcher": matcher, "hooks": entries} if matcher is not None else {"hooks": entries}
        hooks.setdefault(event, []).append(group)
    return new


def remove_hooks(settings: dict, commands: dict) -> dict:
    """A copy of `settings` without the hook entries whose command is in commands[event]; a group or event left
    empty by this is taken out too."""
    new = copy.deepcopy(settings)
    hooks = new.get("hooks", {})
    for event, ours in commands.items():
        groups = hooks.get(event)
        if not isinstance(groups, list):
            continue
        kept = []
        for group in groups:
            before = group.get("hooks", [])
            after = [h for h in before if not (isinstance(h, dict) and h.get("command") in ours)]
            if after or len(after) == len(before):
                kept.append({**group, "hooks": after} if len(after) != len(before) else group)
        if kept:
            hooks[event] = kept
        else:
            hooks.pop(event, None)
    if "hooks" in new and not new["hooks"]:
        new.pop("hooks")
    return new


def settings_bytes(settings: dict) -> bytes:
    return (json.dumps(settings, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


# ---------- global instructions ----------
def decode(raw: bytes) -> str:
    return raw.decode("utf-8", errors="surrogateescape")


def encode(text: str) -> bytes:
    return text.encode("utf-8", errors="surrogateescape")


def summarize(text: str) -> dict:
    lines = text.splitlines()
    return {"size": len(encode(text)), "lines": len(lines),
            "headings": [l.lstrip("#").strip() for l in lines if re.match(r"^#{1,3} ", l)][:8],
            "first": [l for l in lines if l.strip()][:5]}


def newline_of(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def has_import(text: str) -> bool:
    return IMPORT_TARGET in text


def has_block(text: str) -> bool:
    return BLOCK_START in text and BLOCK_END in text


def add_import(text: str) -> str:
    nl = newline_of(text)
    if text and not text.endswith(("\n", "\r")):
        text += nl
    return text + (nl if text else "") + IMPORT_LINE + nl


def block(core: str, nl: str) -> str:
    return nl.join([BLOCK_START, core.replace("\r\n", "\n").rstrip("\n").replace("\n", nl), BLOCK_END]) + nl


def add_block(text: str, core: str) -> str:
    nl = newline_of(text)
    if text and not text.endswith(("\n", "\r")):
        text += nl
    return text + (nl if text else "") + block(core, nl)


def replace_block(text: str, core: str) -> str:
    start, end = text.index(BLOCK_START), text.index(BLOCK_END) + len(BLOCK_END)
    rest = text[end:]
    rest = rest[2:] if rest.startswith("\r\n") else rest[1:] if rest.startswith("\n") else rest
    return text[:start] + block(core, newline_of(text)) + rest


def remove_mindgate(text: str) -> str:
    """The text without the Mindgate import line and block (used when the file changed after the install)."""
    if has_block(text):
        start, end = text.index(BLOCK_START), text.index(BLOCK_END) + len(BLOCK_END)
        text = text[:start] + text[end:].lstrip("\r\n")
    lines = text.splitlines(keepends=True)
    return "".join(l for l in lines if not (IMPORT_TARGET in l and IMPORT_MARK in l))


# ---------- skills, agents, tasks ----------
@dataclass
class Bundle:
    """A skill folder or an agent file ready to copy: its name and its files (relative path parts -> bytes)."""
    name: str
    files: dict
    suffix: str = ".md"   # an agent file's extension (Codex agents are .toml)


def skill_bundles(vault_files: list) -> list:
    bundles: dict = {}
    for f in vault_files:
        if f.source[:2] == ("_system", "skills") and len(f.source) >= 4:
            bundles.setdefault(f.target[2], {})[f.target[3:]] = f.data
    return [Bundle(name, files) for name, files in sorted(bundles.items())]


def agent_bundles(vault_files: list) -> list:
    return sorted((Bundle(f.target[2][:-3], {(f.target[2],): f.data}) for f in vault_files
                   if f.source[:2] == ("_system", "agents") and len(f.source) == 3 and f.source[2].endswith(".md")),
                  key=lambda b: b.name)


def rename_bundle(bundle: Bundle, new_name: str, kind: str) -> Bundle:
    """The bundle under a new name: the folder or file name and the name line (frontmatter or TOML) change."""
    files = {}
    for parts, data in bundle.files.items():
        if kind == "agent":
            parts = (f"{new_name}{bundle.suffix}",)
        if parts[-1] == f"{new_name}.toml":
            data = encode(TOML_NAME.sub(f"name = {json.dumps(new_name)}", decode(data), count=1))
        elif parts[-1] in ("SKILL.md", f"{new_name}.md"):
            data = encode(FRONTMATTER_NAME.sub(f"name: {new_name}", decode(data), count=1))
        files[parts] = data
    return Bundle(new_name, files, bundle.suffix)


def split_frontmatter(text: str, what: str) -> tuple:
    """(frontmatter lines, body) of a Markdown file; InstallerError when it has no frontmatter."""
    match = FRONTMATTER.match(text)
    if not match:
        raise InstallerError(f"{what}: no frontmatter")
    return match.group(1).splitlines(), text[match.end():]


def mapped_tools(claude_tools: str, tools: dict, client: str, agent: str) -> list:
    """Claude tool names (comma list) → the client's tool names; an unknown tool stops the install."""
    mapped = []
    for name in (t.strip() for t in claude_tools.split(",") if t.strip()):
        if name not in tools:
            raise InstallerError(f"agent {agent}: no {client} tool for {name}")
        mapped += [t for t in tools[name] if t not in mapped]
    return mapped


def convert_agent_frontmatter(bundle: Bundle, client: str, tools: dict, models: dict | None, dropped: set) -> Bundle:
    """A Claude agent file with the client's frontmatter: `tools` translated, `model` translated (or dropped when
    `models` is None), keys in `dropped` removed with their indented lines. Without a tools line every tool stays."""
    (parts, data), = bundle.files.items()
    frontmatter, body = split_frontmatter(decode(data), f"agent {bundle.name}")
    lines, skipping = [], False
    for line in frontmatter:
        if line[:1] in (" ", "\t", "-"):          # a list item of the previous key
            if not skipping:
                lines.append(line)
            continue
        key, _, value = line.partition(":")
        skipping = key in dropped or (key == "model" and models is None)
        if skipping:
            continue
        if key == "tools":
            line = "tools: [" + ", ".join(mapped_tools(value, tools, client, bundle.name)) + "]"
        elif key == "model":
            line = f"model: {models.get(value.strip(), 'inherit')}"
        lines.append(line)
    return Bundle(bundle.name, {parts: encode("---\n" + "\n".join(lines) + "\n---\n" + body)})


def marked_instructions(current: str | None, body: str, limit: int, label: str) -> str:
    """`current` with Mindgate's marked block added or refreshed; refused when the file would pass `limit` bytes."""
    text = current or ""
    new = replace_block(text, body) if has_block(text) else add_block(text, body)
    size = len(encode(new))
    if size > limit:
        raise InstallerError(f"{label} would be {size} bytes; the assistant cuts files over {limit} bytes, so it was "
                             "not written")
    return new


def task_content(task: str, language: str, values: Values) -> bytes:
    source = (TASKS_SOURCE if language == "en" else LOCALES / language / "setup" / "tasks") / task / "SKILL.md"
    return fill(source.read_text(encoding="utf-8"), values).encode("utf-8")


# ---------- plan and execution ----------
@dataclass
class Write:
    """A new file; fails if the file appears in the meantime (never overwrites)."""
    path: Path
    data: bytes


@dataclass
class Change:
    """Replace an existing file whose content is `before`; a copy of `before` is written to `backup` first."""
    path: Path
    data: bytes
    before: bytes
    backup: Path | None


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def free_path(path: Path) -> Path:
    """`path`, or `path-2`, `path-3` … when it is taken."""
    candidate, n = path, 2
    while candidate.exists():
        candidate, n = path.with_name(f"{path.name}-{n}"), n + 1
    return candidate


def write_new(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "xb") as f:
        f.write(data)


def replace_file(path: Path, data: bytes) -> None:
    """Atomic replace: a temporary file next to the target is moved over it."""
    temporary = free_path(path.with_name(f".{path.name}.mindgate-tmp"))
    with open(temporary, "xb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporary, path)


def execute(actions: list) -> list:
    """Runs the plan in order; returns the paths written. Stops at the first error (raised)."""
    done = []
    for action in actions:
        if isinstance(action, Write):
            write_new(action.path, action.data)
            done.append(action.path)
        else:
            current = action.path.read_bytes() if action.path.exists() else None
            if current != action.before:
                raise InstallerError(f"{action.path} changed while the installer was running; it was not touched")
            if action.backup is not None:
                write_new(action.backup, action.before)
                done.append(action.backup)
            replace_file(action.path, action.data)
            done.append(action.path)
    return done


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------- manifest ----------
def claude_dir(home: Path) -> Path:
    return home / CLAUDE_DIR


def mindgate_dir(home: Path) -> Path:
    return claude_dir(home) / MINDGATE_DIR


def manifest_path(home: Path) -> Path:
    return mindgate_dir(home) / MANIFEST_NAME


def read_manifest(home: Path) -> dict | None:
    path = manifest_path(home)
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("installs"), list):
        raise ValueError("unexpected manifest shape")
    return data


def manifest_bytes(data: dict) -> bytes:
    return (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def inside(path: Path, folder: Path) -> bool:
    try:
        Path(os.path.abspath(path)).relative_to(os.path.abspath(folder))
    except ValueError:
        return False
    return True


# ---------- questions ----------
class ConsoleAsker:
    """Asks on the terminal. `language` is set after the first question."""
    interactive = True

    def __init__(self, output=print, read=input):
        self.language = "en"
        self.output = output
        self.read = read

    def _read(self, prompt: str) -> str:
        try:
            return self.read(prompt + " ").strip()
        except EOFError:
            raise InstallerError(msg.text(self.language, "stopped")) from None

    def yes_no(self, key: str, prompt: str, default: bool) -> bool:
        yes = msg.text(self.language, "yes_words").split(",")
        no = msg.text(self.language, "no_words").split(",")
        hint = msg.text(self.language, "yes_no")
        shown = yes[0] if default else no[0]
        while True:
            answer = self._read(f"{prompt} {hint} ({msg.text(self.language, 'default')}: {shown})").lower()
            if not answer:
                return default
            if answer in yes:
                return True
            if answer in no:
                return False
            self.output(msg.text(self.language, "invalid_choice", options=f"{yes[0]} / {no[0]}"))

    def choose(self, key: str, prompt: str, options: list, default: str, aliases: dict | None = None) -> str:
        while True:
            answer = self._read(f"{prompt} [{' / '.join(options)}] ({msg.text(self.language, 'default')}: {default})")
            answer = answer.lower() or default
            if answer in options:
                return answer
            self.output(msg.text(self.language, "invalid_choice", options=" / ".join(options)))

    def text(self, key: str, prompt: str, default: str, once: bool = False) -> str:
        return self._read(f"{prompt} ({msg.text(self.language, 'default')}: {default})") or default

    def pick(self, key: str, items: list, prompt_of, allowed: list | None = None, default: bool = True) -> list:
        """Asks yes/no for each item id; returns the ones answered yes."""
        return [item for item in items if self.yes_no(key, prompt_of(item), default)]


class FileAsker:
    """Takes every answer from a JSON object (for tests and unattended runs). A missing or invalid answer stops the
    installer before anything is written."""
    interactive = False

    def __init__(self, answers: dict):
        self.language = "en"
        self.answers = answers
        self.asked: set = set()

    def _value(self, key: str, once: bool = False):
        if key not in self.answers:
            raise InstallerError(msg.text(self.language, "answer_missing", key=key))
        if once and key in self.asked:   # the same answer was refused once; asking again would loop
            self._invalid(key)
        self.asked.add(key)
        return self.answers[key]

    def _invalid(self, key: str):
        raise InstallerError(msg.text(self.language, "answer_invalid", key=key, value=json.dumps(self.answers.get(key))))

    def yes_no(self, key: str, prompt: str, default: bool) -> bool:
        value = self._value(key)
        if not isinstance(value, bool):
            self._invalid(key)
        return value

    def choose(self, key: str, prompt: str, options: list, default: str, aliases: dict | None = None) -> str:
        value = self._value(key)
        value = (aliases or {}).get(value, value)
        if value not in options:
            self._invalid(key)
        return value

    def text(self, key: str, prompt: str, default: str, once: bool = False) -> str:
        value = self._value(key, once)
        if isinstance(value, int) and not isinstance(value, bool):
            value = str(value)
        if not isinstance(value, str) or not value.strip():
            self._invalid(key)
        return value.strip()

    def pick(self, key: str, items: list, prompt_of, allowed: list | None = None, default: bool = True) -> list:
        """The listed ids that are among `items`; ids in `allowed` (such as hooks already installed) are accepted
        and ignored."""
        value = self._value(key)
        if not isinstance(value, list) or any(v not in items and v not in (allowed or []) for v in value):
            self._invalid(key)
        return [item for item in items if item in value]


def load_answers(path: str) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise InstallerError(msg.text("en", "answers_unreadable", error=error)) from None
    if not isinstance(data, dict):
        raise InstallerError(msg.text("en", "answers_unreadable", error="not a JSON object"))
    return data


def make_asker(answers_file: str | None, home: Path, output=print):
    """The question source; refuses a test-like run (--answers) against the real home folder."""
    if not answers_file:
        return ConsoleAsker(output)
    answers = load_answers(answers_file)
    if is_real_home(home):
        raise InstallerError(msg.text(str(answers.get("language", "en")), "refuse_real_home", home=home))
    asker = FileAsker(answers)
    asker.language = answers.get("language") if answers.get("language") in msg.LANGUAGES else "en"
    return asker
