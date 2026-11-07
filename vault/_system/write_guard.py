"""PreToolUse write guard: stops Claude's file-writing tools from changing the vault's protected files.

Why: the rules for `sources/` (raw sources are not changed, CLAUDE.md §2, §7.4) and `log.md` (only appended to, §10)
were only written down; there was no guard for the Write/Edit tools. A written rule is enforced with a tool (#37).

Decisions (Write, Edit, MultiEdit, NotebookEdit):
  deny     — writing to the vault or under ~/.claude (memory, instructions, skills, tasks) in a chat that is unrecorded
             or whose record question is not answered; junctions and 8.3 short names are resolved to the real path
             (#43; project files outside the vault are allowed)
  deny     — changing an EXISTING file under the vault's `sources/` (adding a new source file is allowed)
  deny     — writing to or editing the vault's `log.md` directly (to append: `records.py log`, locked, #36)
  (silent) — everything else
  ask      — if the guard cannot parse the input (when unsure, ask)

Writing to the same files with shell commands is asked by `command_guard.py`.
Other assistants call it with `--client codex|gemini|antigravity` (hook_io.py): their write tools, every path of a
Codex patch, and the homes of every client (~/.codex, ~/.gemini, ~/.agents) are checked the same way.
"""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the -I flag does not add the script folder to the path
import common  # noqa: E402
import hook_io  # noqa: E402
import session_mode as sm  # noqa: E402
from common import VAULT, name, vault_path  # noqa: E402

CLIENT = "claude"   # set from --client in main(); decides the answer format (hook_io.py)
# Every assistant's home: memory, instructions, skills, hooks and scheduled tasks (~/.claude, ~/.codex, ~/.gemini, ~/.agents)
CLIENT_ROOTS = tuple(Path.home() / home for home in hook_io.CLIENT_HOMES)
# The hook files of the other assistants: writing one can switch the guards off (audit 7 November 2026)
CLIENT_HOOK_FILES = (Path.home() / ".codex" / "hooks.json", Path.home() / ".codex" / "config.toml",
                     Path.home() / ".gemini" / "settings.json", Path.home() / ".gemini" / "config" / "hooks.json")
DEVICE_PREFIX = re.compile(r"^(?:[\\/]{2}[?.][\\/])")   # \\?\C:\…, //?/C:/…, \\.\C:\…
DRIVE = re.compile(r"^[a-zA-Z]:")
SOURCES = vault_path("sources")
LOG = vault_path("log.md")
ARCHIVES = (vault_path("archive", "log"), vault_path("archive", "pending"))   # monthly rotation archives


def localized(en: str, tr: str) -> str:
    """Text the user sees directly (permissionDecisionReason), in the install language (config.json `language`)."""
    return tr if common.LANGUAGE == "tr" else en


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
    return False


def check_stream(raw: str) -> bool:
    """Denies a path that names an alternate data stream (`log.md::$DATA` writes log.md itself); True if it denied."""
    if ":" not in DRIVE.sub("", raw, count=1):   # a colon after the drive letter: file.md::$DATA
        return False
    decide("deny", localized(f"A path with a data stream name is not written: {raw}. Use the plain file name.",
                             f"Veri akışı adı taşıyan yola yazılmaz: {raw}. Dosyanın düz adını kullan."))
    return True


def check_hook_file(path: Path) -> bool:
    """Asks (or denies where the client cannot ask) before an assistant's hook file is changed; True if it decided."""
    target = real(path)
    if not any(target == real(hook_file) for hook_file in CLIENT_HOOK_FILES):
        return False
    decide(hook_io.ASK_OR_DENY, localized(
        f"This is an assistant's hook file ({path.name}); changing it can switch the guards off. The user decides.",
        f"Bu bir asistanın hook dosyası ({path.name}); değiştirmek kapıları kapatabilir. Kararı kullanıcı verir."))
    return True


def check_call(call: hook_io.Call) -> None:
    """Every target path of the call (a Codex patch can hold several); stops at the first denial."""
    for raw in call.paths:
        raw = DEVICE_PREFIX.sub("", raw.strip())
        if check_stream(raw):
            return
        path = resolve(raw, call.cwd)
        if check_recording_mode(path, call.session_id) or check_hook_file(path) or check(path):
            return


def main() -> None:
    global CLIENT
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")
        CLIENT = hook_io.client_from_args(sys.argv[1:])
        call = hook_io.read_call(CLIENT, json.loads(sys.stdin.read() or "{}"), hook_io.WRITE)
        if call is not None:
            check_call(call)
    except Exception as error:  # the guard must never crash; Claude asks, the other clients deny (hook_io.FAIL)
        decide(hook_io.FAIL, localized(f"The write guard could not parse the input ({type(error).__name__}); the user should approve.",
                                f"Yazma kapısı girdiyi çözümleyemedi ({type(error).__name__}); kullanıcı onaylasın."))
    finally:
        hook_io.finish(CLIENT)


if __name__ == "__main__":
    main()
