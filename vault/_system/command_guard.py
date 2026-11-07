"""PreToolUse guard: checks Bash and PowerShell commands before they run.

Claude Code calls this script before every shell command (global ~/.claude/settings.json → hooks.PreToolUse).
Other assistants call it with `--client codex|gemini|antigravity`; hook_io.py reads their payload and answers in
their format (a recursive delete is denied where the client cannot ask the user).
The script reads the hook JSON from stdin, compares the command with patterns and gives one of three decisions:

  deny     — not run, Claude is told why (deleting the home folder / drive root, formatting a disk, changing a
             security setting, killing processes by name, port-freeing tools, deleting the vault/.claude ...)
  ask      — the user is asked (EVERY deletion, even of a single file — rule #22; killing by PID, irreversible git
             operations, stopping a service ...)
  (silent) — the permission flow continues as usual

Why: Claude Code's sandbox does not exist on native Windows; users' home folders and drive roots were deleted by a
wrong path expansion (`rm -rf ... ~/`, `$HOME` left empty, through a junction); `pkill node` / `taskkill /IM`
killed other people's applications and Claude itself.

Design principles:
- Deterministic (no LLM): the same command always gets the same decision.
- It tries to look at the target the command touches, not its "shape": if the target is home/root/vault/.claude,
  deny; every other recursive deletion, ask.
- False positives are accepted, false negatives are not: when unsure, ask.
- The hook must never crash: every error is swallowed and the decision becomes "ask".
- The vault is recognised by its own absolute path (all spellings: C:\\..., C:/..., /c/..., 8.3 short names,
  ~ / $HOME / %USERPROFILE%), not by a fixed folder name.
"""
import json
import os
import re
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the -I flag does not add the script folder to the path
import common  # noqa: E402
import hook_io  # noqa: E402
import session_mode as sm  # noqa: E402
from common import VAULT, name, vault_path  # noqa: E402

CLIENT = "claude"   # set from --client in main(); decides the answer format (hook_io.py)


def localized(pair: tuple[str, str]) -> str:
    """(English, Turkish) → the text in the install language (config.json `language`)."""
    return pair[1] if common.LANGUAGE == "tr" else pair[0]


# --- Vault path -----------------------------------------------------------
SEP = r"[\\/]+"
END = r"(?=[\\/\s\"'`;&|)>]|$)"     # the path ends here or continues with a separator
HOME_FORMS = r"(?:~|\$home\b|\$\{home\}|\$env:userprofile|\$\{env:userprofile\}|%userprofile%|\$env:home)"


def segment_pattern(segment: str) -> str:
    """One path segment; a name that is not 8.3 also matches its Windows short name (LONGNA~1)."""
    full = re.escape(segment)
    if re.fullmatch(r"[^\s.]{1,8}(?:\.[^\s.]{1,3})?", segment):
        return full
    stem = segment.rsplit(".", 1)[0] if "." in segment.strip(".") else segment
    short = re.sub(r"[\s.]", "", stem)[:6]
    return rf"(?:{full}|{re.escape(short)}~\d+(?:\.[^\\/\s]*)?)" if short else full


def path_pattern(path: Path, home: Path | None = None) -> str:
    """Regex (use with re.I) for an absolute folder in the spellings commands use: C:\\a\\b, C:/a/b, /c/a/b,
    8.3 short names, and ~ / $HOME / %USERPROFILE% forms when the folder is inside the home folder."""
    absolute = Path(os.path.abspath(path))
    rest = SEP.join(segment_pattern(s) for s in absolute.parts[1:])
    drive = absolute.drive.rstrip(":")
    root = rf"(?:{re.escape(drive)}:|/{re.escape(drive)})" if drive else ""
    forms = [root + SEP + rest]
    home = Path(os.path.abspath(home or Path.home()))
    if absolute != home and absolute.is_relative_to(home):
        forms.append(HOME_FORMS + SEP + SEP.join(segment_pattern(s) for s in absolute.relative_to(home).parts))
    return "(?:" + "|".join(forms) + ")"


VAULT_AT = path_pattern(VAULT) + END
CLIENT_HOMES = "|".join(segment_pattern(home) for home in hook_io.CLIENT_HOMES)   # ~/.claude … ~/.agents, 8.3 names too
VAULT_NORMAL = os.path.normcase(os.path.abspath(VAULT))

# --- Path patterns ----------------------------------------------------------
# The home folder itself (not a subfolder): ~ , ~/ , $HOME , %USERPROFILE% ,
# C:\Users\name , /c/Users/name , /home/name  (followed by a separator, space, quote, * or end of line)
HOME = re.compile(
    r"""(?ix)
    (?<![\w./\\-])
    (?: ~ | \$home\b | \$\{home\} | \$env:userprofile | \$\{env:userprofile\} | %userprofile% | \$env:home
      | [a-z]:[\\/]+users[\\/]+[^\\/\s"'*]+ | /c/users/[^/\s"'*]+ | /home/[^/\s"'*]+ | /users/[^/\s"'*]+ )
    [\\/]* \*? (?= [\s"'`;&|)>] | $ )
    """
)
# Drive root / root folder: / , /* , C:\ , C:/ , C:\* , \ , .. (parent folder)
ROOT = re.compile(
    r"""(?ix)
    (?<![\w./\\-])
    (?: [a-z]:[\\/]*\*? | / \*? | \\ \*? | \.\.(?:[\\/]\.\.)*[\\/]* | /\* )
    (?= [\s"'`;&|)>] | $ )
    """
)
# The main folders of the home folder (Desktop, Documents ...): deleting one of them whole is a disaster
HOME_SUB = re.compile(
    r"""(?ix)
    (?<![\w./\\-])
    (?: ~ | \$home\b | \$env:userprofile | %userprofile% | [a-z]:[\\/]+users[\\/]+[^\\/\s"'*]+ | /c/users/[^/\s"'*]+ | /home/[^/\s"'*]+ )
    [\\/]+ (?: desktop | documents | downloads | pictures | videos | music | onedrive | belgeler | masaustu | masaüstü | indirilenler | resimler | videolar | muzik | müzik | appdata | \.ssh | \.claude )
    [\\/]* \*? (?= [\s"'`;&|)>] | $ )
    """
)
PROTECTED = re.compile(rf"(?i){VAULT_AT}|(?:[\\/]|(?<![\w.~-]))(?:{CLIENT_HOMES})(?:[\\/]|\b)|\.obsidian|\.git(?:[\\/]|\b)|\.ssh|appdata|program files"
                       r"|windows[\\/]system32")

# --- Command patterns -------------------------------------------------------
DELETE = [  # (pattern, has a target capture group)
    re.compile(r"(?i)(?<![\w-])rm\s+(?:-[a-z]*r[a-z]*\s+|-[a-z]*\s+)*(?:-[a-z]*r[a-z]*)?\s*([^;&|\n]*)"),  # rm -r* ...
    re.compile(r"(?i)(?<![\w-])(?:rmdir|rd)\s+/s\b([^;&|\n]*)"),
    re.compile(r"(?i)(?<![\w-])(?:del|erase)\s+(?:/\w\s+)*/s\b([^;&|\n]*)"),
    re.compile(r"(?i)(?<![\w-])(?:remove-item|ri|rm|del|erase|rd|rmdir)\b[^|\n]*-recurse\b([^;&|\n]*)"),
    re.compile(r"(?i)(?<![\w-])(?:remove-item|ri)\s+[^|\n]*-force\b([^;&|\n]*)"),
    re.compile(r"(?i)(?<![\w-])rimraf\s+([^;&|\n]*)"),
    re.compile(r"(?i)shutil\.rmtree\s*\(\s*(.*)"),
    re.compile(r"(?i)(?<![\w-])git\s+clean\b([^;&|\n]*)"),
    re.compile(r"(?i)(?<![\w-])(?:robocopy)\b[^|\n]*\s/mir\b([^;&|\n]*)"),
]
RM_R = re.compile(r"(?i)(?<![\w-])rm\s+(?:-\w*\s+)*-\w*r")  # whether rm is recursive

# Rule #22: EVERY deletion is asked, even of a single file (the reason is explained in the chat first).
# del/erase/rd only at the start of a command: a line start does not count, because a Python `del x` in a heredoc deletes no file
COMMAND_START = r"(?:^|[;&|(]\s*|\bcmd(?:\.exe)?\s+/c\s+)"
DELETE_SHELL = [  # searched outside quotes (text such as grep 'rm x' is not a command)
    r"(?i)(?<![\w.-])(?:rm|unlink|shred)\s+\S",
    r"(?i)\bxargs\s+(?:-\S+\s+)*(?:rm|del|unlink|shred)\b",
    r"(?i)(?<![\w.-])rmdir\s+\S",
    COMMAND_START + r"(?i:del|erase|rd)\s+\S",
    r"(?i)(?<![\w-])(?:remove-item|ri)\b",
    r"(?i)(?<![\w-])git\s+(?:rm|clean)\b",
    r"(?i)(?<![\w-])find\b[^|\n]*\s-delete\b",
]
DELETE_CODE = [  # inside a script (py -c "...", heredoc) caught even when quoted
    r"(?i)\bos\.(?:remove|unlink|rmdir|removedirs)\s*\(",
    r"(?i)\.unlink\s*\(",
    r"(?i)\.rmdir\s*\(",
    r"(?i)\bshutil\.rmtree\b",
    r"(?i)\bfs\.(?:rm|rmSync|unlink|unlinkSync|rmdir|rmdirSync)\b",
    r"(?i)\.(?:unlink|rm|rmdir)Sync\s*\(",
    r"(?i)\[(?:system\.)?io\.(?:file|directory)\]::delete\b",
    r"(?i)\bsend2trash\b",
]
DELETE_REASON = (
    "Deletion (rule #22). The part of the command that counts as deletion: `{part}`. No file on this computer is deleted "
    "without the user's explicit permission. Claude must first write clearly in the chat what it wants to delete and WHY; "
    "if it did not, do not allow it and ask why. Without permission this command is not run.",
    "Silme işlemi (kural #22). Komutun silme sayılan kısmı: `{part}`. Bilgisayarda hiçbir dosya kullanıcının açık izni "
    "olmadan silinmez. Claude önce sohbette neyi ve NEDEN silmek istediğini açıkça yazmalı; yazmadıysa izin verme, "
    "nedenini sor. İzin yoksa bu komut çalıştırılmaz.")
# The start of a long command hid the deleting part; the reason shows the matching part
PART_LENGTH = 120

# A backtick inside a double-quoted `-c "…"` or an unquoted heredoc runs as a command in the shell; text was run as a
# command this way more than once
DOUBLE_QUOTED_C = re.compile(r'(?<![\w-])-c\s+"((?:[^"\\]|\\.)*)"')
UNQUOTED_HEREDOC = re.compile(r"<<-?\s*([A-Za-z_]\w*)[^\n]*\n(.*?)\n\1\b", re.S)
UNESCAPED_BACKTICK = re.compile(r"(?<!\\)`")
BACKTICK_REASON = (
    "A backtick runs as a command in the shell: the text inside a double-quoted `-c \"…\"` or an unquoted heredoc "
    "changes. Write the content to a file with Write and run it, or quote the heredoc with <<'EOF'. If it is used on "
    "purpose, approve. Part: `{part}`",
    "Ters tırnak (backtick) kabukta komut olarak çalışır: çift tırnaklı `-c \"…\"` ya da tırnaksız heredoc içindeki "
    "metin değişir. İçeriği Write ile dosyaya yazıp çalıştır ya da heredoc'u <<'EOF' ile tırnakla. Bilerek "
    "kullanılıyorsa onayla. Parça: `{part}`")

DESTRUCTIVE = [  # deny in every case: (pattern, (English, Turkish))
    (r"(?i)(?<![\w-])(?:diskpart|format-volume|clear-disk|initialize-disk|remove-partition|mkfs\.?\w*|dd\s+if=)\b",
     ("disk formatting / partition operation", "disk biçimlendirme / bölüm işlemi")),
    # not the word 'format' alone: uses such as --date=format: are allowed
    (r"(?i)(?:^|[;&|(]\s*|\bcmd(?:\.exe)?\s+/c\s+)format(?:\.com|\.exe)?\s+[a-z]:",
     ("disk formatting (format <drive>:)", "disk biçimlendirme (format <sürücü>:)")),
    (r"(?i)(?<![\w-])(?:cipher\s+/w|bcdedit|bootrec|bootsect)\b", ("boot / disk wiping tool", "önyükleme / disk silme aracı")),
    (r"(?i)(?<![\w-])(?:shutdown|stop-computer|restart-computer|logoff|rundll32\s+user32\.dll,lockworkstation)\b",
     ("shutting down / restarting the computer", "bilgisayarı kapatma / yeniden başlatma")),
    (r"(?i)(?<![\w-])reg\s+(?:delete|add)\s+hk(?:lm|ey_local_machine)", ("HKLM registry change", "HKLM kayıt defteri değişikliği")),
    (r"(?i)(?<![\w-])(?:remove-itemproperty|set-itemproperty|new-itemproperty)\b[^|\n]*hklm",
     ("HKLM registry change", "HKLM kayıt defteri değişikliği")),
    (r"(?i)(?<![\w-])(?:netsh\s+(?:advfirewall|firewall|interface)|set-netfirewall|new-netfirewall|remove-netfirewall|disable-netadapter)\b",
     ("firewall / network setting", "güvenlik duvarı / ağ ayarı")),
    (r"(?i)(?<![\w-])(?:set-mppreference|add-mppreference|remove-mppreference|set-executionpolicy\s+unrestricted)\b",
     ("Defender / execution policy", "Defender / yürütme politikası")),
    (r"(?i)(?<![\w-])(?:vssadmin\s+delete|wmic\s+shadowcopy\s+delete|wbadmin\s+delete)\b",
     ("deleting backups / shadow copies", "yedek / gölge kopya silme")),
    (r"(?i)(?<![\w-])(?:clear-recyclebin|rd\s+/s\s+/q\s+[a-z]:\\\$recycle\.bin)\b",
     ("emptying the Recycle Bin (permanent deletion; the user does it)",
      "Geri Dönüşüm Kutusu'nu boşaltma (kalıcı silme; kullanıcı kendisi yapar)")),
    (r"(?i)(?<![\w-])(?:schtasks\s+/delete|unregister-scheduledtask|sc\s+delete|remove-service)\b",
     ("deleting a scheduled task / service", "zamanlanmış görev / servis silme")),
    (r"(?i)(?<![\w-])(?:takeown|icacls\s+[^|\n]*/(?:grant|deny|reset))\b",
     ("file ownership / permission change", "dosya sahipliği / izin değişikliği")),
    (r"(?i)(?:curl|wget|iwr|invoke-webrequest)\b[^|\n]*\|\s*(?:sudo\s+)?(?:bash|sh|zsh|iex|invoke-expression|powershell|pwsh|python)\b",
     ("downloading from the internet and running it directly", "internetten indirip doğrudan çalıştırma")),
    (r"(?i)(?<![\w-])(?:iex|invoke-expression)\s*\(?\s*(?:\(?\s*)?(?:iwr|invoke-webrequest|new-object\s+net\.webclient|\[system\.net)",
     ("downloading from the internet and running it directly", "internetten indirip doğrudan çalıştırma")),
    (r"(?i)(?<![\w-])powershell(?:\.exe)?\s+[^|\n]*-(?:enc|encodedcommand)\b",
     ("encoded PowerShell command", "kodlanmış PowerShell komutu")),
    (r":\(\)\s*\{\s*:\|:&\s*\};:", ("fork bomb", "fork bomb")),
    (r"(?i)(?<![\w-])(?:pkill|killall)\b",
     ("killing processes by name (may close someone else's application or Claude itself)",
      "isme göre süreç öldürme (başkasının uygulamasını ya da Claude'un kendisini kapatabilir)")),
    (r"(?i)(?<![\w-])taskkill\b(?![^|\n]*/pid\b)",
     ("killing processes by name (/IM); only with /PID and after asking",
      "isme göre süreç öldürme (/IM); yalnızca /PID ile ve sorarak")),
    (r"(?i)(?<![\w-])stop-process\b[^|\n]*-name\b",
     ("killing processes by name (-Name); only with -Id and after asking",
      "isme göre süreç öldürme (-Name); yalnızca -Id ile ve sorarak")),
    (r"(?i)(?<![\w-])get-process\b[^|\n]*\|\s*[^|\n]*stop-process", ("killing processes in bulk", "toplu süreç öldürme")),
    (r"(?i)(?<![\w-])(?:kill-port|port-killer|freethenport|fuser\s+-k|fkill)\b",
     ("port-freeing tool; someone else's application closes — use a free port",
      "port boşaltma aracı; başkasının uygulaması kapanır — boş port kullan")),
    (r"(?i)(?<![\w-])kill\s+-9\s+-1\b", ("killing every process", "bütün süreçleri öldürme")),
]
DESTRUCTIVE_SUFFIX = (
    "This command is not run. If the port is busy pick a free port; if a process is needed find its PID with "
    "netstat/Get-NetTCPConnection and ask the user.",
    "Bu komut çalıştırılmaz. Port doluysa boş bir port seç; süreç gerekiyorsa PID'yi netstat/Get-NetTCPConnection ile "
    "bul ve kullanıcıya sor.")

ASK = [  # ask: (pattern, (English, Turkish) or None)
    (r"(?i)(?<![\w-])taskkill\b[^|\n]*/pid\b",
     ("killing a process by PID: make sure the PID is not the user's application / Claude / the editor",
      "PID ile süreç öldürme: PID'nin kullanıcının uygulaması / Claude / editör olmadığından emin ol")),
    (r"(?i)(?<![\w-])stop-process\b", ("killing a process", "süreç öldürme")),
    (r"(?i)(?<![\w-])kill\s+(?:-\w+\s+)*\d+", ("killing a process by PID", "PID ile süreç öldürme")),
    (r"(?i)(?<![\w-])(?:stop-service|restart-service|net\s+stop|sc\s+stop)\b", ("stopping a service", "servis durdurma")),
    (r"(?i)(?<![\w-])git\s+push\b[^|\n]*(?:--force\b|-f\b|--force-with-lease)",
     ("git force push (overwrites the remote history)", "git force push (uzak geçmişi ezer)")),
    (r"(?i)(?<![\w-])git\s+reset\s+--hard", ("git reset --hard (local changes are lost)", "git reset --hard (yerel değişiklikler gider)")),
    (r"(?i)(?<![\w-])git\s+(?:checkout|restore)\s+(?:--\s+)?\.(?:\s|$)",
     ("discarding every change in the working copy", "çalışma kopyasındaki tüm değişiklikleri geri alma")),
    (r"(?i)(?<![\w-])git\s+branch\s+-D\b", ("force-deleting a branch", "dal zorla silme")),
    (r"(?i)(?<![\w-])git\s+(?:filter-repo|filter-branch)\b", ("rewriting git history", "git geçmişini yeniden yazma")),
    (r"(?i)(?<![\w-])git\s+stash\s+(?:drop|clear)\b", ("deleting a stash", "stash silme")),
    (r"(?i)(?<![\w-])(?:reg\s+delete|remove-itemproperty)\b", ("deleting from the registry", "kayıt defteri silme")),
    (r"(?i)(?<![\w-])(?:schtasks\s+/create|register-scheduledtask|new-service|sc\s+create)\b",
     ("creating a scheduled task / service", "zamanlanmış görev / servis oluşturma")),
    (r"(?i)(?<![\w-])(?:pip|npm|npx|uv|pipx|winget|choco|scoop)\s+(?:install|i|add|uninstall|remove)\b[^|\n]*(?:-g\b|--global\b|--user\b)?",
     None),  # for information only: silent
    (r"(?i)(?<![\w-])(?:npx|bunx|pipx\s+run)\s+(?!kill-port)[\w@./-]+",
     ("running a package from the internet with npx", "npx ile internetten paket çalıştırma")),
    (r"(?i)(?<![\w-])(?:chmod\s+-R\s+777|chown\s+-R)\b", ("bulk permission change", "toplu izin değişikliği")),
    (r"(?i)(?<![\w-])(?:mklink|new-item\s+-itemtype\s+(?:symboliclink|junction))\b",
     ("creating a link (symlink/junction)", "bağlantı (symlink/junction) oluşturma")),
    (r"(?i)(?<![\w-])(?:move-item|mv|move)\b[^|\n]*(?:-force|/y)\b", ("moving with overwrite", "üzerine yazarak taşıma")),
]


# Writing to the vault's protected files (sources/, log.md) with the shell → ask. The shell side of write_guard.py.
# The target must follow the write operation in the same command part: a records.py call whose title contains "log.md"
# is not a write.
WRITE_OPERATION = (r"(?i)(?:(?<![<>=&\d-])>{1,2}|(?<![\w-])(?:sed\s+(?:-\w+\s+)*-i\S*|perl\s+(?:-\w+\s+)*-\w*i\w*|set-content|out-file"
                   r"|add-content|tee(?:-object)?|truncate|cp|copy|copy-item|mv|move|move-item)\b)[^|;&\n]*?")
PROTECTED_TAIL = (rf"(?:{re.escape(name('sources'))}[\\/]|log\.md\b"
                  rf"|{re.escape(name('archive'))}[\\/]+(?:log|{re.escape(name('pending'))})[\\/])")
PROTECTED_ABSOLUTE = re.compile(WRITE_OPERATION + path_pattern(VAULT) + SEP + PROTECTED_TAIL)
PROTECTED_RELATIVE = re.compile(WRITE_OPERATION + r"(?<![\w.\\/:-])(?:\.[\\/])?" + PROTECTED_TAIL)

# Secret files: the Read tool is blocked with a settings.json deny rule, reading them with the shell is asked too.
# Example files (.env.example, .env.sample, .env.template) carry no secrets and are allowed.
SECRET_FILE = re.compile(r"(?i)(?:^|[\s'\"=/\\])(?:\.env(?:\.(?:local|development|production|test|staging))?(?:\.local)?"
                         r"|id_(?:rsa|ed25519|ecdsa|dsa)(?:\.pub)?|[\w.-]+\.(?:pem|key|pfx|p12)|\.git-credentials|\.credentials\.json"
                         r"|\.ssh[\\/][^\s'\"]*)(?=$|[\s'\"|;&)<>])")


def in_vault(cwd: str) -> bool:
    if not cwd:
        return False
    if re.search(rf"(?i){VAULT_AT}", cwd):
        return True
    folder = os.path.normcase(os.path.abspath(cwd))
    return folder == VAULT_NORMAL or folder.startswith(VAULT_NORMAL + os.sep)


def path_tokens(text: str) -> list[str]:
    return [t.strip("\"'`") for t in re.split(r"[\s;&|<>()=,]+", text) if t.strip("\"'`") and not t.startswith("-")
            and "://" not in t]


def resolves_to_vault_or_parent(text: str, cwd: str) -> bool:
    """A relative target (`rm -rf vault` one level above it) that is the vault itself or one of its parent folders."""
    if not cwd:
        return False
    for token in path_tokens(text):
        target = os.path.normcase(os.path.abspath(os.path.join(cwd, token)))
        if target == VAULT_NORMAL or VAULT_NORMAL.startswith(target.rstrip("\\/") + os.sep):
            return True
    return False


def resolves_into_vault(text: str, cwd: str) -> bool:
    """A relative path in the command that lands in the vault (`echo x > vault/a.md` from the folder above it)."""
    return bool(cwd) and any(in_vault(os.path.join(cwd, token)) for token in path_tokens(text))


# Unrecorded (temporary) chat (#43): the shell side of write_guard.py. A deny list left a hole with every new writer
# (ni, robocopy, curl -o, dozens of git sub-commands). Allow list: a command that touches the record area (vault,
# ~/.claude) passes only if every part of it only reads. Limit: a path built by string joining or a script in Temp
# is not seen.
RECORD_AREA = re.compile(rf"(?i){VAULT_AT}|(?:{CLIENT_HOMES})(?:[\\/]|\b)")
CHANGE_DIR = re.compile(r"(?i)(?<![\w-])(?:cd|pushd|set-location|sl|chdir)\s+(\"[^\"]+\"|'[^']+'|[^\s;&|]+)")
PART_SEPARATOR = re.compile(r"&&|\|\||[;&|\n]")
NULL_REDIRECT = re.compile(r"(?i)\d?>{1,2}\s*(?:/dev/null|\$null|nul)\b|\d>&\d")
REDIRECT = re.compile(r"(?<![<>=&\d-])>{1,2}")
READING_COMMANDS = {"cat", "head", "tail", "grep", "egrep", "fgrep", "rg", "ls", "dir", "find", "wc", "sort", "uniq", "cut", "echo",
                    "printf", "pwd", "cd", "pushd", "popd", "set-location", "sl", "chdir", "get-content", "gc", "select-string", "sls",
                    "get-childitem", "gci", "test-path", "type", "which", "stat", "file", "diff", "jq", "tree", "sha256sum", "md5sum",
                    "date", "basename", "dirname", "realpath", "sed", "git", "py", "python", "python3"}
READING_GIT = {"status", "log", "diff", "show", "blame", "grep", "ls-files", "rev-parse", "shortlog", "describe"}
GIT_VALUE_OPTIONS = {"-c", "-C", "--git-dir", "--work-tree", "--namespace"}
READING_SCRIPTS = {"search", "graph", "code_map", "health", "security_scan", "secret_scan", "cost", "session_mode"}
WRITING_FLAGS = {"--save-baseline", "--install"}   # health.py writes the tracked baseline, secret_scan.py the vault git hook
FIND_WRITES = re.compile(r"(?i)-(?:delete|exec|execdir|ok|okdir|fprint\w*|fls)\b")
MODE_SET = re.compile(r"(?i)session_mode\.py[\"']?\s+set\s+(\S+)")
UNRECORDED_REASON = (
    "This chat is unrecorded or its record question is not answered yet (#43): only commands that read may touch the "
    "vault and ~/.claude. Blocked part: `{part}`. Recording is turned on only by the user's explicit answer.",
    "Bu sohbet kayıtsız ya da kayıt sorusu cevaplanmadı (#43): vault'a ve ~/.claude'a yalnızca okuyan komutlar girer. "
    "Engellenen kısım: `{part}`. Kayıt yalnızca kullanıcının açık cevabıyla açılır.")


def touches_record_area(text: str, cwd: str) -> bool:
    targets = [cwd, *(m.group(1).strip("\"'") for m in CHANGE_DIR.finditer(text))]
    return (any(in_vault(t) or RECORD_AREA.search(t) or resolves_into_vault(t, cwd) for t in targets if t)
            or bool(RECORD_AREA.search(text)) or resolves_into_vault(text, cwd))


def git_reads(words: list[str]) -> bool:
    i = 1
    while i < len(words) and words[i].startswith("-"):
        i += 1 if "=" in words[i] or words[i] not in GIT_VALUE_OPTIONS else 2
    return i < len(words) and words[i].lower() in READING_GIT


def python_reads(words: list[str]) -> bool:
    if any(w in ("-c", "-m") or w.lower() in WRITING_FLAGS for w in words):
        return False
    script = next((w.strip("\"'") for w in words[1:] if w.strip("\"'").lower().endswith(".py")), "")
    return Path(script.replace("\\", "/")).stem.lower() in READING_SCRIPTS


def part_reads(part: str) -> bool:
    words = part.split()
    if not words:
        return True
    first = words[0].strip("\"'").lower()
    if first not in READING_COMMANDS:
        return False
    if first == "git":
        return git_reads(words)
    if first in ("py", "python", "python3"):
        return python_reads(words)
    if first == "sed":
        return not any(w.startswith("-") and "i" in w.lstrip("-") for w in words[1:])
    return not (first == "find" and FIND_WRITES.search(part))


def unrecorded_denied_part(text: str, cwd: str, sid: str) -> str:
    """The part of the command to deny in an unrecorded chat; empty if it may pass."""
    for m in MODE_SET.finditer(text):
        if m.group(1).strip("\"'") != sid:
            return m.group(0)   # another chat's recording mode is not changed
    if not touches_record_area(text, cwd):
        return ""
    clean = NULL_REDIRECT.sub("", text)
    redirect = REDIRECT.search(clean)
    if redirect:
        return part_of(clean, redirect.start())
    return next((p.strip() for p in PART_SEPARATOR.split(clean) if not part_reads(p)), "")


@lru_cache(maxsize=8)
def quote_map(text: str) -> bytes:
    """For every position: 1 if it is inside quotes. One pass; a ' inside "…" is a plain character, and a backslash
    escapes the next character outside single quotes (audit 7 November 2026: the old count was O(n²) and treated
    "'" as an open quote)."""
    flags, state, escaped = bytearray(len(text) + 1), "", False
    for i, char in enumerate(text):
        flags[i] = 1 if state else 0
        if escaped:
            escaped = False
        elif char == "\\" and state != "'":
            escaped = True
        elif state == "" and char in "'\"":
            state = char
        elif char == state:
            state = ""
    flags[len(text)] = 1 if state else 0
    return bytes(flags)


def inside_quotes(text: str, position: int) -> bool:
    """Is `position` inside an open quote? (text searches such as grep 'rm -rf' are not commands)"""
    return quote_map(text)[position] == 1


WRAPPER = re.compile(
    r"""(?ix) (?<![\w-]) (?: bash | sh | zsh | dash | ksh | cmd (?:\.exe)? | powershell (?:\.exe)? | pwsh (?:\.exe)? ) \b
    [^\n;&|"']*? \s (?: -c | /c | /k | -command | -cmd ) \s+ (?: "((?:[^"\\]|\\.)*)" | '([^']*)' )""")
WRAPPER_DEPTH = 3


def with_inner_commands(text: str) -> str:
    """The command plus, on lines of their own, the commands wrapped in `bash -c "…"`, `cmd /c "…"`,
    `powershell -Command "…"` (audit 7 November 2026: a wrapped deletion was read as quoted text)."""
    found, layer = [], text
    for _ in range(WRAPPER_DEPTH):
        inner = [m.group(1) if m.group(1) is not None else m.group(2) for m in WRAPPER.finditer(layer)]
        if not inner:
            break
        found += inner
        layer = "\n".join(inner)
    return "\n".join([text, *found])


def find_unquoted(pattern, text: str):
    """The first match outside quotes."""
    for m in re.finditer(pattern, text):
        if not inside_quotes(text, m.start()):
            return m
    return None


def decide(decision: str, reason: str) -> None:
    hook_io.emit(CLIENT, decision, f"{localized(('[Command guard]', '[Koruma kapısı]'))} {reason}")


def part_of(text: str, position: int) -> str:
    """The command from `position` to the end of the line, as long as the reason shows."""
    line = text[position:].split("\n", 1)[0].strip()
    return line if len(line) <= PART_LENGTH else line[:PART_LENGTH - 1] + "…"


def recursive_deletions(command: str) -> list[tuple[str, str]]:
    """Recursive/forced deletion commands: a list of (target part, part shown in the reason)."""
    deletions = []
    for pattern in DELETE:
        for m in pattern.finditer(command):
            if inside_quotes(command, m.start()):
                continue
            if pattern is DELETE[0] and not RM_R.search(m.group(0)):
                continue  # rm is not recursive
            deletions.append((m.group(1) if m.lastindex else "", part_of(command, m.start())))
    return deletions


def simple_deletion_part(text: str) -> str:
    """The part of a single-file deletion or an in-script deletion, or empty text."""
    for pattern in DELETE_SHELL:
        m = find_unquoted(pattern, text)
        if m:
            return part_of(text, m.start())
    for pattern in DELETE_CODE:
        m = re.search(pattern, text)
        if m:
            return part_of(text, m.start())
    return ""


def backtick_part(text: str) -> str:
    """The part with an unescaped backtick in a double-quoted -c argument or an unquoted heredoc body."""
    for m in DOUBLE_QUOTED_C.finditer(text):
        if not inside_quotes(text, m.start()) and UNESCAPED_BACKTICK.search(m.group(1)):
            return part_of(text, m.start())
    for m in UNQUOTED_HEREDOC.finditer(text):
        if UNESCAPED_BACKTICK.search(m.group(2)):
            return part_of(text, m.start())
    return ""


BLOCKLIST = vault_path("knowledge", "security", "blocked-sites.md")


def blocklist_label() -> str:
    return BLOCKLIST.relative_to(VAULT).as_posix()


DOWNLOAD_TOOL = re.compile(r"(?i)(?<![\w-])(?:curl|wget|iwr|irm|invoke-webrequest|invoke-restmethod|start-bitstransfer|certutil)\b")


def blocked_address(text: str) -> str:
    """Does a URL in the command go to a site on the blocklist? (rule #27; the list is shared with site_guard.py)"""
    fetches = DOWNLOAD_TOOL.search(text)
    if not BLOCKLIST.is_file() or not (fetches or re.search(r"(?i)https?://", text)):
        return ""
    domains = re.findall(r"(?m)^\|\s*`?([a-z0-9.-]+\.[a-z]{2,})`?\s*\|", BLOCKLIST.read_text(encoding="utf-8").lower())
    hosts = re.findall(r"(?i)https?://(?:[^/\s'\"@]*@)?([a-z0-9.-]+)", text)
    if fetches:   # curl example.com/x, curl //example.com: no scheme
        hosts += re.findall(r"(?i)(?<![\w.@-])(?://)?((?:[a-z0-9-]+\.)+[a-z]{2,})(?=[/:\s'\"]|$)", text)
    for host in hosts:
        host = host.lower()
        for domain in domains:
            if host == domain or host.endswith("." + domain):
                return domain
    return ""


def check(command: str, cwd: str, sid: str = "") -> None:
    text = with_inner_commands(command.strip())
    if not text:
        return

    if sm.is_unrecorded(sid):
        denied = unrecorded_denied_part(text, cwd, sid)
        if denied:
            decide("deny", localized(UNRECORDED_REASON).format(part=denied[:PART_LENGTH]))
            return

    blocked = blocked_address(text)
    if blocked:
        decide("deny", localized((
            f"The command goes to a site on the blocklist ({blocked}; {blocklist_label()}). This site is not visited (rule #27).",
            f"Komut kara listedeki bir siteye gidiyor ({blocked}; {blocklist_label()}). Bu siteye girilmez (kural #27).")))
        return

    for pattern, reason in DESTRUCTIVE:
        if find_unquoted(pattern, text):
            decide("deny", f"{localized(reason)}. {localized(DESTRUCTIVE_SUFFIX)}")
            return

    deletions = recursive_deletions(text)
    if deletions:
        target_text = " ".join(target for target, _ in deletions) or text
        shown = " · ".join(p for _, p in deletions)
        if (HOME.search(target_text) or HOME_SUB.search(target_text) or ROOT.search(target_text) or PROTECTED.search(target_text)
                or resolves_to_vault_or_parent(target_text, cwd)):
            decide("deny", localized((
                "The recursive deletion target is the home folder, a drive root, a parent folder or a protected folder "
                f"(vault, .claude, .git, .ssh, AppData): `{shown}`. This command is not run; rewrite the target inside the "
                "project with a full path.",
                "Özyinelemeli silme hedefi ev dizini, sürücü kökü, üst dizin ya da korunan bir klasör (vault, .claude, .git, "
                f".ssh, AppData): `{shown}`. Bu komut çalıştırılmaz; hedefi proje içinde tam yolla yeniden yaz.")))
            return
        # If $HOME / a variable is empty the target may be the root: targets built with variables are denied
        if re.search(r"\$\{?\w+\}?\s*[\\/]|%\w+%[\\/]|\$env:\w+[\\/]", target_text) and not re.search(r"\$\{?(?:pwd|cwd)\}?", target_text, re.I):
            decide("deny", localized((
                f"The deletion target is built with an environment variable: `{shown}`. If the variable is empty, the root "
                "or the home folder is deleted (this has happened). Use a full, fixed path.",
                f"Silme hedefi bir ortam değişkeniyle kuruluyor: `{shown}`. Değişken boş kalırsa kök/ev dizini silinir "
                "(yaşanmış olay). Tam, sabit yol kullan.")))
            return
        decide(hook_io.ASK_OR_DENY, localized(DELETE_REASON).format(part=shown) + " " + localized((
            "A recursive/forced deletion cannot be undone; if possible send it to the Recycle Bin.",
            "Özyinelemeli/zorlamalı silme geri alınamaz; mümkünse Geri Dönüşüm Kutusu'na gönder.")))
        return

    deletion_part = simple_deletion_part(text)
    if deletion_part:
        decide(hook_io.ASK_OR_CLIENT, localized(DELETE_REASON).format(part=deletion_part))
        return

    # Writing/moving to the home or root folder (not deletion) — full path check
    if re.search(r"(?i)(?<![\w-])(?:mv|move|move-item|cp\s+-r|copy-item\s+[^|\n]*-recurse|robocopy|xcopy)\b", text) and (ROOT.search(text) or HOME.search(text)):
        decide("ask", localized(("Bulk move/copy into a drive root or the home folder.",
                                 "Sürücü kökü ya da ev dizinine toplu taşıma/kopyalama.")))
        return

    if find_unquoted(PROTECTED_ABSOLUTE, text) or (in_vault(cwd) and find_unquoted(PROTECTED_RELATIVE, text)):
        sources = name("sources")
        decide("ask", localized((
            f"Writing to a protected vault file with the shell: the raw sources under {sources}/ are not changed, log.md is "
            f"only appended to with `records.py log` (CLAUDE.md §2, §10). `{text[:160]}`",
            f"Vault'un korunan dosyasına kabukla yazma: {sources}/ altındaki ham kaynaklar değiştirilmez, log.md'ye yalnızca "
            f"`records.py log` ile eklenir (CLAUDE.md §2, §10). `{text[:160]}`")))
        return

    if SECRET_FILE.search(text):
        decide("ask", localized((
            "The command touches a secret file (.env, SSH key, .pem/.key, credentials; rule #18). Claude should not see "
            "the content of these files; if a value is needed, only where it is stored is written. If the command does not "
            f"print the content and is needed, approve: `{text[:160]}`",
            "Komut bir sır dosyasına dokunuyor (.env, SSH anahtarı, .pem/.key, kimlik bilgisi; kural #18). Claude bu "
            "dosyaların içeriğini görmemeli; değer gerekiyorsa yalnızca nerede durduğu yazılır. Komut içeriği ekrana "
            f"basmıyorsa ve gerekliyse onayla: `{text[:160]}`")))
        return

    for pattern, reason in ASK:
        if reason and find_unquoted(pattern, text):
            decide("ask", f"{localized(reason)}: `{text[:160]}`")
            return

    backtick = backtick_part(text)
    if backtick:
        decide("ask", localized(BACKTICK_REASON).format(part=backtick))


def main() -> None:
    global CLIENT
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")
        try:
            CLIENT = hook_io.client_from_args(sys.argv[1:])
        except hook_io.UnknownCall as error:   # a wrong --client in a hook file: deny in every client's format
            print(hook_io.deny_for_every_client(f"[Command guard] {error}"))
            CLIENT = ""
            return
        call = hook_io.read_call(CLIENT, json.loads(sys.stdin.read() or "{}"), hook_io.SHELL)
        if call is not None:
            check(call.command, call.cwd, call.session_id)
    except Exception as error:  # the guard must never crash; Claude asks, the other clients deny (hook_io.FAIL)
        decide(hook_io.FAIL, localized((f"The command guard could not parse the command ({type(error).__name__}); the user "
                                 "should approve.",
                                 f"Koruma kapısı komutu çözümleyemedi ({type(error).__name__}); kullanıcı onaylasın.")))
    finally:
        if CLIENT:
            hook_io.finish(CLIENT)


if __name__ == "__main__":
    main()
