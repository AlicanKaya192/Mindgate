"""Shared helpers for the vault scripts: name map, file lock, atomic write, simple frontmatter reading.

Why: several Claude chats can write to the vault at the same time (two chats once took the same pending
number). Scripts that write shared files (pending, log, handoff) read-modify-write inside `locked()`;
`atomic_write()` never leaves a half-written file. Rule #36.

Folder and file names are never hard-coded: `name()` and `vault_path()` turn an English base name into the
name used by the active install (read from `config.json` next to this file).
"""
import json
import os
import re
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

SYSTEM_DIR = Path(__file__).resolve().parent
VAULT = SYSTEM_DIR.parent
CONFIG_FILE = SYSTEM_DIR / "config.json"   # bootstrap file: holds the name map, so its own name is fixed


def load_config(path: Path = CONFIG_FILE) -> tuple[dict, str]:
    """(settings, error). A missing or unreadable file gives empty settings (English names), so the guards keep
    working; the error text is kept for health checks."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, ""
    except (OSError, ValueError) as error:
        return {}, f"{path.name} could not be read ({type(error).__name__}: {error})"
    return (data, "") if isinstance(data, dict) else ({}, f"{path.name} is not a JSON object")


def load_names(config: dict) -> dict[str, dict[str, str]]:
    names = config.get("names") or {}
    return {kind: dict(names.get(kind) or {}) for kind in ("folders", "files")}


CONFIG, CONFIG_ERROR = load_config()
LANGUAGE = str(CONFIG.get("language") or "en")
NAMES = load_names(CONFIG)


def name(key: str) -> str:
    """English base name -> name in the active install; the key itself when there is no mapping.

    A key with an extension ("pending.md") is looked up by its stem among files and keeps the extension;
    a key without one is looked up among folders, then files ("pending" as a wiki link target)."""
    stem, dot, ext = key.rpartition(".") if "." in key.lstrip(".") else (key, "", "")
    if dot:
        mapped = NAMES["files"].get(stem)
        return f"{mapped}.{ext}" if mapped else key
    return NAMES["folders"].get(key) or NAMES["files"].get(key) or key


def vault_path(*parts: str) -> Path:
    """VAULT / name(part) / ...; a part may also hold several segments separated by '/'."""
    path = VAULT
    for part in parts:
        for segment in part.replace("\\", "/").split("/"):
            if segment:
                path = path / name(segment)
    return path


OUTPUT = vault_path("_system", "output")       # outside git
LOCK_DIR = OUTPUT / "locks"
LOCK_WAIT_S = 30
LOCK_STEP_S = 0.1
REPLACE_TRIES = 5          # Windows: os.replace raises PermissionError if the target is held open for a moment (Obsidian, antivirus)
REPLACE_STEP_S = 0.2
HOOK_ERRORS = OUTPUT / "hook_errors.log"
TR_LOWER = str.maketrans({"I": "ı", "İ": "i"})
TR_ASCII = str.maketrans("çğıöşüâîû", "cgiosuaiu")
# Folders and files whose name contains one of these stay out of the dashboard and automatic context
# (extra safety net; secrets are never written anyway, #18). Turkish words are kept so Turkish vaults are covered.
SENSITIVE_PATH = re.compile(r"sifre|parola|gizli|kasa|private|secret|password|credential")


def ascii_lower(text: str) -> str:
    """Lower-cases with Turkish casing rules and folds to ASCII ("İŞ" -> "is")."""
    return text.translate(TR_LOWER).lower().translate(TR_ASCII)


def sensitive_path(relative: str) -> bool:
    return bool(SENSITIVE_PATH.search(ascii_lower(relative.replace("\\", "/"))))


def log_error(source: str, error: BaseException) -> None:
    """Hooks swallow errors so the session is not broken; one line is written so a trace remains (health.py reads it)."""
    try:
        HOOK_ERRORS.parent.mkdir(parents=True, exist_ok=True)
        with open(HOOK_ERRORS, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}\t{source}\t{type(error).__name__}: {str(error)[:200]}\n")
    except OSError:
        pass  # if the error log cannot be written either, there is nothing to do; the hook still does not break


class LockUnavailable(RuntimeError):
    pass


def _lock(handle) -> bool:
    try:
        handle.seek(0)  # the Windows lock depends on the position: lock and release the same byte
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


def _release(handle) -> None:
    if os.name == "nt":
        import msvcrt
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@contextmanager
def locked(lock_name: str, wait_s: float = LOCK_WAIT_S):
    """Exclusive lock across processes for the same `lock_name`. Raises LockUnavailable when time runs out."""
    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOCK_DIR / f"{lock_name}.lock", "a+") as handle:
        deadline = time.monotonic() + wait_s
        while not _lock(handle):
            if time.monotonic() >= deadline:
                raise LockUnavailable(f"lock '{lock_name}' not taken within {wait_s} s; another chat may be writing")
            time.sleep(LOCK_STEP_S)
        try:
            yield
        finally:
            _release(handle)


def atomic_write(path: Path, text: str) -> None:
    """Writes to a temporary file and moves it into place: an interruption never leaves a half file. LF line endings."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # On error the temporary file is not deleted (#22); health.py reports leftover `.*.tmp` files.
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    replace_with_retry(temporary, path)


def replace_with_retry(temporary: str, path: Path) -> None:
    """os.replace; if the target is locked for a moment, retries at short intervals (seen as WinError 5 on log.md)."""
    for attempt in range(REPLACE_TRIES):
        try:
            os.replace(temporary, path)
            return
        except PermissionError:
            if attempt == REPLACE_TRIES - 1:
                raise
            time.sleep(REPLACE_STEP_S)


def frontmatter(text: str) -> tuple[dict, str]:
    """Flat YAML frontmatter (key: value, list [a, b]); nested fields are not supported (vault §5)."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("\n---", 1)
    if len(parts) < 2:
        return {}, text
    fields = {}
    for line in parts[0].splitlines()[1:]:
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if not m:
            continue
        value = m.group(2).strip()
        if value.startswith("[") and value.endswith("]"):
            fields[m.group(1)] = [p.strip().strip("\"'") for p in value[1:-1].split(",") if p.strip()]
        else:
            fields[m.group(1)] = value.strip("\"'")
    return fields, parts[1].split("\n", 1)[1] if "\n" in parts[1] else ""
