"""Keeps the dashboard in step with the vault: the end-of-chat reminder, the publish record and the dashboard address.

Only Claude can publish the dashboard (with the Artifact tools, /dashboard skill); a script cannot. So the update has
to happen in the chat, and this script makes sure it is not forgotten (rule #29).

Commands:
  check          Stop hook. When this chat wrote to the vault and the vault changed since the last publish, it adds a
                 reminder to the chat: "update the dashboard", or, while the dashboard has never been published, a
                 one-line note that /dashboard publishes it. The same vault state is reminded once per chat, so a chat
                 without the Artifact tools (CLI, other assistants) is not reminded after every answer. Silent in an
                 unrecorded chat (#43) and while another Stop hook already continues the chat. It builds no data and
                 needs no git: it compares file sizes and change times, so it ends well within the hook time limit.
                 It never breaks the session: every error is swallowed and written to the hook error log.
  save           The last step of /dashboard, only after the upload succeeded: records the vault state as published.
  url            Prints the dashboard address, or nothing while it has not been published.
  set-url <url>  The first /dashboard run writes the address of the new dashboard to config.json.

Run (from the vault root):  python -I _system/dashboard_check.py save
"""
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I does not put the script folder on the path
import common  # noqa: E402
import session_mode as sm  # noqa: E402
from common import atomic_write, vault_path  # noqa: E402
from session_log import this_machine  # noqa: E402

CONFIG_FILE = common.CONFIG_FILE
STATE_NAME = "dashboard_state.json"
OUT_OF_VAULT = {".obsidian", ".git", ".trash", ".claude"}
SIGNED_SUFFIXES = {".md", ".html"}           # notes, agent and skill files, and the dashboard page
KEPT_SESSIONS = 200
DASHBOARD_URL = re.compile(r"https://claude\.ai/(?:code/)?artifact/[A-Za-z0-9_-]+")   # always used with fullmatch
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
SHELL_TOOLS = {"Bash", "PowerShell"}
SHELL_WRITE = re.compile(r"(?i)\bgit(?:\s+-C\s+(?:\"[^\"]*\"|'[^']*'|\S+))?\s+(?:commit|add|mv)\b|>>|\bout-file\b"
                         r"|\bset-content\b|\badd-content\b|\bmv\b|\bmove-item\b|\bcp\b|\bcopy-item\b|records\.py"
                         r"|session_log\.py\s+process")
GIT_BASH_DRIVE = re.compile(r"(?<![\w:/])/([a-z])/")   # /c/Users/... -> c:/Users/...
LOCK_WAIT_S = 5                                         # well within the hook time limit

MESSAGES = {
    "en": {
        "not_published": ("[Second brain — dashboard] This chat wrote to the vault, and the dashboard has not been "
                          "published yet. Tell the user in one line: typing /dashboard publishes it to their own "
                          "claude.ai account (the vault data it shows goes to claude.ai). Do not publish it unasked."),
        "out_of_date": ("[Second brain — dashboard] This chat wrote to the vault and the dashboard is out of date. "
                        "Update it now with the /dashboard skill (it uploads only the data sets that changed); commit "
                        "the vault first if it has uncommitted changes. Where the Artifact tools are missing (CLI, IDE "
                        "terminal, other assistants), do not run `dashboard_check.py save`; say in one line that the "
                        "dashboard could not be updated."),
    },
    "tr": {
        "not_published": ("[İkinci beyin — pano] Bu sohbet vault'a yazdı, pano ise henüz yayımlanmadı. Kullanıcıya tek "
                          "satırla söyle: /pano yazınca pano kendi claude.ai hesabında yayımlanır (panonun gösterdiği "
                          "vault verisi claude.ai'ye gider). İstenmeden yayımlama."),
        "out_of_date": ("[İkinci beyin — pano] Bu sohbet vault'a yazdı ve pano güncel değil. Şimdi /pano becerisiyle "
                        "güncelle (yalnızca değişen veri setlerini yükler); vault'ta commit edilmemiş değişiklik varsa "
                        "önce commit et. Artifact araçlarının olmadığı yerde (CLI, IDE terminali, öteki asistanlar) "
                        "`dashboard_check.py save` çalıştırma; panonun güncellenemediğini tek satırla söyle."),
    },
}


# ---------- settings and state ----------
def read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def state_file() -> Path:
    return vault_path("_system", "output") / STATE_NAME


def write_state(state: dict) -> None:
    atomic_write(state_file(), json.dumps(state, indent=1))


def dashboard_url() -> str:
    """The address in config.json, or "" when there is none or it is not a claude.ai artifact address."""
    url = str((read_json(CONFIG_FILE).get("dashboard") or {}).get("url") or "")
    return url if DASHBOARD_URL.fullmatch(url) else ""


def set_url(url: str) -> None:
    """Writes the dashboard address to config.json; any other address than a claude.ai artifact is refused."""
    if not DASHBOARD_URL.fullmatch(url):
        raise ValueError(f"not a claude.ai artifact address: {url!r}")
    config = read_json(CONFIG_FILE)
    if not config:
        raise ValueError(f"{CONFIG_FILE.name} could not be read; the address was not written")
    config.setdefault("dashboard", {})["url"] = url
    atomic_write(CONFIG_FILE, json.dumps(config, indent=1, ensure_ascii=False) + "\n")


# ---------- vault state ----------
def signed_files(vault: Path) -> list[Path]:
    skipped = (vault_path("_system", "output"), vault_path("inbox", "sessions"))
    files = []
    for path in vault.rglob("*"):
        relative = path.relative_to(vault)
        if (path.suffix.lower() not in SIGNED_SUFFIXES or OUT_OF_VAULT & set(relative.parts)
                or any(path.is_relative_to(s) for s in skipped) or not path.is_file()):
            continue
        files.append(path)
    return sorted(files)


def vault_signature() -> str:
    """SHA-256 of every signed file's path, size and change time: cheap, and needs no git."""
    vault = common.VAULT
    digest = hashlib.sha256()
    for path in signed_files(vault):
        info = path.stat()
        digest.update(f"{path.relative_to(vault).as_posix()}\t{info.st_size}\t{info.st_mtime_ns}\n".encode("utf-8"))
    return digest.hexdigest()


def vault_marker() -> str:
    """The vault path as commands are compared: lower case, forward slashes, no trailing slash."""
    return normalized(common.VAULT.as_posix()).rstrip("/")


def normalized(text: str) -> str:
    """Lower case, forward slashes, and a Git Bash path (/c/Users/...) written as c:/Users/..."""
    return GIT_BASH_DRIVE.sub(r"\1:/", text.replace("\\", "/").lower())


def names_vault(text: str, marker: str) -> bool:
    """Does the text name the vault folder itself or a path inside it (not a sibling such as '<vault>-old')?"""
    return re.search(re.escape(marker) + r"(?=[/\"'\s]|$)", normalized(text)) is not None


def wrote_to_vault(transcript: str) -> bool:
    """Did this chat write to the vault (a file tool on a vault file, or a writing command run on the vault)?"""
    path = Path(transcript or "")
    if not path.is_file():
        return False
    marker = vault_marker()
    folder = common.VAULT.name.encode("utf-8")
    with open(path, "rb") as f:
        for raw in f:
            if b'"tool_use"' not in raw or folder not in raw:
                continue
            try:
                entry = json.loads(raw)
            except ValueError:
                continue
            if any(writes(part, marker, str(entry.get("cwd", ""))) for part in (entry.get("message") or {}).get("content") or []):
                return True
    return False


def writes(part, marker: str, cwd: str) -> bool:
    if not isinstance(part, dict) or part.get("type") != "tool_use":
        return False
    fields = part.get("input") or {}
    if part.get("name") in WRITE_TOOLS:
        target = os.path.normpath(str(fields.get("file_path", "")))   # "<vault>/../other" leaves the vault
        return normalized(target).startswith(marker + "/")
    if part.get("name") in SHELL_TOOLS:
        command = str(fields.get("command", ""))
        return (names_vault(command, marker) or names_vault(cwd, marker)) and bool(SHELL_WRITE.search(command))
    return False


# ---------- commands ----------
def check(event: dict) -> None:
    sid = str(event.get("session_id", ""))
    config = read_json(CONFIG_FILE)
    if event.get("stop_hook_active") or sm.is_unrecorded(sid) or not this_machine(config):
        return   # an unrecorded chat (#43) or another computer (#17) leaves no trace in the state file either
    with common.locked("dashboard", wait_s=LOCK_WAIT_S):
        text = reminder(sid, str(event.get("transcript_path", "")), config)
    if text:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": text}}, ensure_ascii=False))


def reminder(sid: str, transcript: str, config: dict) -> str:
    """The reminder for this chat, or "" when there is nothing to say; records what it decided."""
    state = read_json(state_file())
    writers = state.get("writers", [])
    if sid not in writers:
        if not wrote_to_vault(transcript):
            return ""   # this chat did not touch the vault: the dashboard is not its job
        writers = (writers + [sid])[-KEPT_SESSIONS:]
    signature = vault_signature()
    reminded = state.get("reminded", {})
    if signature == state.get("published") or reminded.get(sid) == signature:
        write_state({**state, "writers": writers})
        return ""
    reminded[sid] = signature
    write_state({**state, "writers": writers, "reminded": dict(list(reminded.items())[-KEPT_SESSIONS:])})
    language = "tr" if config.get("language") == "tr" else "en"
    return MESSAGES[language]["out_of_date" if dashboard_url() else "not_published"]


def save() -> None:
    with common.locked("dashboard", wait_s=LOCK_WAIT_S):
        state = read_json(state_file())
        state.update(published=vault_signature(), published_at=datetime.now().isoformat(timespec="seconds"))
        write_state(state)


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    command = argv[0] if argv else ""
    if command == "check":
        try:
            sys.stdin.reconfigure(encoding="utf-8")
            check(json.loads(sys.stdin.read() or "{}"))
        except Exception as error:   # a hook must never break the session
            common.log_error("dashboard_check check", error)
        return 0
    if command == "save":
        save()
        print("dashboard publish recorded")
        return 0
    if command == "url":
        print(dashboard_url())
        return 0
    if command == "set-url" and len(argv) == 2:
        try:
            set_url(argv[1])
        except ValueError as error:
            print(error, file=sys.stderr)
            return 1
        print(f"dashboard address written to {CONFIG_FILE.name}")
        return 0
    print(__doc__.strip(), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
