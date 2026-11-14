"""PreToolUse write guard: stops Claude's file-writing tools from changing the vault's protected files.

Why: the rules for `sources/` (raw sources are not changed, CLAUDE.md §2, §7.4) and `log.md` (only appended to, §10)
were only written down; there was no guard for the Write/Edit tools. A written rule is enforced with a tool (#37).

Decisions (Write, Edit, MultiEdit, NotebookEdit):
  deny     — writing to the vault or under ~/.claude (memory, instructions, skills, tasks) in a chat that is unrecorded
             or whose record question is not answered; junctions and 8.3 short names are resolved to the real path
             (#43; project files outside the vault are allowed)
  deny     — changing an EXISTING file under the vault's `sources/` (adding a new source file is allowed)
  deny     — writing to or editing the vault's `log.md` directly (to append: `records.py log`, locked, #36)
  deny     — writing a file named after a standard library module (`json.py`, `re.pyc` …) or such a package folder
             under the vault's `_system/`: it could shadow a module the guards import
  ask      — changing a defense (common.DEFENSE_SET: hook and permission settings of every assistant, guard scripts,
             agent definitions, git hooks, blocklist, preview command, rules, instructions, vault schema …); the reason
             names the defense. Where the client cannot ask, it is denied (Antigravity asks every time)
  ask      — text that goes into a text file (.json, .py, .md …) holds an invisible control character (Claude only)
  (silent) — everything else
  ask      — if the guard cannot parse the input or load its helpers (common, session_mode): when unsure, ask

Writing to the same files with shell commands is asked by `command_guard.py`.
Other assistants call it with `--client codex|gemini|antigravity` (hook_io.py): their write tools, every path of a
Codex patch, and the homes of every client (~/.codex, ~/.gemini, ~/.agents) are checked the same way.
"""
import fnmatch
import json
import os
import re
import sys
from pathlib import Path

# The -I flag does not add the script folder to the path. It goes to the END: a file such as `json.py` in the folder
# must not shadow the standard library. hook_io needs only the standard library and answers even when the others fail.
sys.path.append(str(Path(__file__).resolve().parent))
import hook_io  # noqa: E402
try:
    import common  # noqa: E402
    import session_mode as sm  # noqa: E402
    from common import DEFENSE_SET, STDLIB, VAULT, name, stdlib_shadow, vault_path  # noqa: E402
    IMPORT_ERROR = ""
except Exception as _error:  # whatever the error, the decision must be "ask" (main)
    common = sm = None
    IMPORT_ERROR = f"{type(_error).__name__}: {_error}"
    VAULT, DEFENSE_SET = Path(__file__).resolve().parent.parent, ()

    def name(key: str) -> str:
        return key

    def vault_path(*parts: str) -> Path:
        return VAULT.joinpath(*parts)

CLIENT = "claude"   # set from --client in main(); decides the answer format (hook_io.py)
# Every assistant's home: memory, instructions, skills, hooks and scheduled tasks (~/.claude, ~/.codex, ~/.gemini, ~/.agents)
CLIENT_ROOTS = tuple(Path.home() / home for home in hook_io.CLIENT_HOMES)
SYSTEM = vault_path("_system")
DEVICE_PREFIX = re.compile(r"^(?:[\\/]{2}[?.][\\/])")   # \\?\C:\…, //?/C:/…, \\.\C:\…
DRIVE = re.compile(r"^[a-zA-Z]:")
SOURCES = vault_path("sources")
LOG = vault_path("log.md")
ARCHIVES = (vault_path("archive", "log"), vault_path("archive", "pending"))   # monthly rotation archives
# A mangled escape sequence (`\b` became U+0008) went into a text file as an invisible character
CONTROL_CHARACTER = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")   # tab, line feed and carriage return are fine
TEXT_EXTENSIONS = {".json", ".py", ".md", ".txt", ".yaml", ".yml", ".csv", ".srt", ".vtt"}
CONTENT_FIELDS = ("content", "new_string")


def localized(en: str, tr: str) -> str:
    """Text the user sees directly (permissionDecisionReason), in the install language (config.json `language`)."""
    return tr if common and common.LANGUAGE == "tr" else en


def normal(path: Path) -> str:
    """On Windows case and separator differences must not break the comparison; `..` is resolved."""
    return os.path.normcase(os.path.abspath(path))


def decide(decision: str, reason: str) -> None:
    hook_io.emit(CLIENT, decision, f"{localized('[Write guard]', '[Yazma kapısı]')} {reason}")


def resolve(raw: str, cwd: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else Path(cwd or ".") / path


def target_path(data: dict) -> Path | None:
    """The target of a Claude payload (kept for callers that hold the raw payload)."""
    tool_input = data.get("tool_input") or {}
    raw = tool_input.get("file_path") or tool_input.get("notebook_path")
    return resolve(str(raw), str(data.get("cwd") or "")) if raw else None


def real(path: Path) -> Path:
    """Junctions (~/.claude/skills → vault) and 8.3 short names (LONGNA~1) are resolved; a plain path comparison
    missed them."""
    return Path(os.path.normcase(os.path.realpath(path)))


def in_record_area(path: Path) -> bool:
    """The vault and ~/.claude (memory, instructions, skills, scheduled tasks): where an unrecorded chat must leave no trace."""
    target = real(path)
    return any(target.is_relative_to(real(area)) for area in (VAULT, *CLIENT_ROOTS))


def check_recording_mode(path: Path, sid: str) -> bool:
    """Denies writing to the record area in an unrecorded or unanswered chat; True if it denied."""
    current = sm.mode(sid)
    if current == sm.RECORDED or not in_record_area(path):
        return False
    if current == sm.WAITING:
        decide("deny", localized(
            "This chat's record question is not answered yet (#43): until the answer, nothing is written to the vault or "
            "to ~/.claude. First ask the user \"Should this chat be recorded in the vault?\".",
            "Bu sohbetin kayıt sorusu henüz cevaplanmadı (#43): cevap gelene kadar vault'a ve ~/.claude'a yazılmaz. Önce "
            "kullanıcıya \"Bu sohbetin vault'ta kaydı olsun mu?\" diye sor."))
    else:
        decide("deny", localized(
            "This chat is unrecorded (temporary, #43): nothing is written to the vault or to ~/.claude. Recording is "
            "turned on only by the user's explicit answer.",
            "Bu sohbet kayıtsız (geçici, #43): vault'a ve ~/.claude'a yazılmaz. Kayıt yalnızca kullanıcının açık "
            "cevabıyla açılır."))
    return True


def check(path: Path) -> bool:
    """Denies a change to a protected vault file; True if it denied."""
    target = normal(path)
    if target == normal(LOG):
        decide("deny", localized(
            "log.md is only appended to, with the locked tool: `records.py log --operation … --title … --evidence … "
            "--learned …` (rule #36, CLAUDE.md §10).",
            "log.md yalnızca sona eklenir ve kilitli araçla yazılır: `records.py log --operation … --title … --evidence … "
            "--learned …` (kural #36, CLAUDE.md §10)."))
        return True
    if any(target.startswith(normal(a) + os.sep) for a in ARCHIVES) and Path(target).exists():
        decide("deny", localized(
            f"The log and pending archives are not changed: {path.name}. The past month's entries are moved here word for "
            "word; only `records.py` appends.",
            f"Log ve bekleyen arşivleri değiştirilmez: {path.name}. Biten ayın kayıtları buraya kelimesi kelimesine "
            "taşınır; yalnızca `records.py` sona ekler."))
        return True
    if target.startswith(normal(SOURCES) + os.sep) and Path(target).exists():
        sources, knowledge = name("sources"), name("knowledge")
        decide("deny", localized(
            f"The raw sources under {sources}/ are not changed (CLAUDE.md §2, §7.4): {path.name}. A summary or a correction "
            f"goes into a separate note under {knowledge}/; a new source is added under a new file name.",
            f"{sources}/ altındaki ham kaynaklar değiştirilmez (CLAUDE.md §2, §7.4): {path.name}. Özet ya da düzeltme "
            f"{knowledge}/ altında ayrı nota yazılır; yeni kaynak yeni dosya adıyla eklenir."))
        return True
    if shadows_stdlib(path):
        system = name("_system")
        decide("deny", localized(
            f"No file named after a standard library module is written under {system}/: {path.name}. It could shadow a "
            "module the guards import; give the script another name.",
            f"{system}/ altına standart kütüphane modülü adıyla dosya yazılmaz: {path.name}. Kapıların içe aktardığı "
            "modülü gölgeleyebilir; betiğe başka bir ad ver."))
        return True
    return False


def shadows_stdlib(path: Path) -> bool:
    """`_system/json.py` or `_system/json/…`: a name in the script folder that shadows a standard library module."""
    target, system = real(path), real(SYSTEM)
    if target == system or not target.is_relative_to(system):
        return False
    first = target.relative_to(system).parts
    return stdlib_shadow(first[0]) if len(first) == 1 else first[0].lower() in STDLIB


def is_member(member, path: Path) -> bool:
    """Is the path in this defense member? Both sides are resolved to their real path: ~/.claude/agents may be a
    junction. Names are compared in the platform's case rules."""
    target = real(path)
    folder = [os.path.normcase(segment) for segment in member.folder.split("/") if segment]
    pattern = os.path.normcase(member.pattern)
    if member.root == "any":
        for start in range(len(target.parts) - len(folder) + 1):
            if list(target.parts[start:start + len(folder)]) != folder:
                continue
            rest = target.parts[start + len(folder):]
            if pattern == "**" or (len(rest) == 1 and fnmatch.fnmatchcase(rest[0], pattern)):
                return True
        return False
    base = real((Path.home() if member.root == "home" else VAULT).joinpath(*folder))
    if pattern == "**":
        return target == base or target.is_relative_to(base)
    return target.parent == base and fnmatch.fnmatchcase(target.name, pattern)


def defense_of(path: Path):
    """The defense member the path belongs to, or None."""
    return next((member for member in DEFENSE_SET if is_member(member, path)), None)


def check_defense(path: Path) -> bool:
    """Asks before a defense is changed (denies where the client cannot ask); True if it decided."""
    member = defense_of(path)
    if member is None:
        return False
    decide(hook_io.ASK_OR_DENY, localized(
        f"This write changes a defense: {member.about[0]} ({path}). The change can weaken the guards; the user decides.",
        f"Bu yazma bir savunmayı değiştiriyor: {member.about[1]} ({path}). Değişiklik kapıları zayıflatabilir; kararı "
        "kullanıcı verir."))
    return True


def check_stream(raw: str) -> bool:
    """Denies a path that names an alternate data stream (`log.md::$DATA` writes log.md itself); True if it denied."""
    if ":" not in DRIVE.sub("", raw, count=1):   # a colon after the drive letter: file.md::$DATA
        return False
    decide("deny", localized(f"A path with a data stream name is not written: {raw}. Use the plain file name.",
                             f"Veri akışı adı taşıyan yola yazılmaz: {raw}. Dosyanın düz adını kullan."))
    return True


def check_control_characters(path: Path, tool_input: dict) -> None:
    """Asks when the text to be written to a text file holds an invisible control character."""
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        return
    for field in CONTENT_FIELDS:
        content = tool_input.get(field)
        found = CONTROL_CHARACTER.search(content) if isinstance(content, str) else None
        if found:
            decide("ask", localized(
                r"The text to be written holds an invisible control character (e.g. \x08): most likely an escape sequence "
                f"was mangled; check the content. Found: U+{ord(found.group()):04X} ({field}).",
                r"Yazılacak metinde görünmez kontrol karakteri var (ör. \x08): büyük olasılıkla kaçış dizisi bozuldu; "
                f"içeriği kontrol et. Bulunan: U+{ord(found.group()):04X} ({field})."))
            return


def check_call(call: hook_io.Call) -> bool:
    """Every target path of the call (a Codex patch can hold several); stops at the first denial, and returns True then."""
    for raw in call.paths:
        raw = DEVICE_PREFIX.sub("", raw.strip())
        if check_stream(raw):
            return True
        path = resolve(raw, call.cwd)
        if check_recording_mode(path, call.session_id) or check(path) or check_defense(path):
            return True
    return False


def main() -> None:
    global CLIENT
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")
        CLIENT = hook_io.client_from_args(sys.argv[1:])
        if IMPORT_ERROR:
            decide(hook_io.FAIL, f"The write guard could not load its helper modules (common, session_mode: {IMPORT_ERROR}); "
                                 "it cannot check this write, the user should approve.")
            return
        data = json.loads(sys.stdin.read() or "{}")
        call = hook_io.read_call(CLIENT, data, hook_io.WRITE)
        # Only Claude's Write/Edit payload carries the text; the other clients' answers have no "ask" for this
        if call is not None and not check_call(call) and CLIENT == "claude" and call.paths:
            check_control_characters(resolve(call.paths[0], call.cwd), data.get("tool_input") or {})
    except Exception as error:  # the guard must never crash; Claude asks, the other clients deny (hook_io.FAIL)
        decide(hook_io.FAIL, localized(f"The write guard could not parse the input ({type(error).__name__}); the user should approve.",
                                f"Yazma kapısı girdiyi çözümleyemedi ({type(error).__name__}); kullanıcı onaylasın."))
    finally:
        hook_io.finish(CLIENT)


if __name__ == "__main__":
    main()
