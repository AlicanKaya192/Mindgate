"""PreToolUse guard: checks Bash and PowerShell commands before they run.

Claude Code calls this script before every shell command (global ~/.claude/settings.json → hooks.PreToolUse); the
terminal tool (`mcp__terminal__run_in_terminal`) carries the same `command` field and is checked the same way.
Other assistants call it with `--client codex|gemini|antigravity`; hook_io.py reads their payload and answers in
their format (a recursive delete is denied where the client cannot ask the user).
The script reads the hook JSON from stdin, compares the command with patterns and gives one of three decisions:

  deny     — not run, Claude is told why (deleting the home folder / drive root, formatting a disk, changing a
             security setting, killing processes by name, port-freeing tools, deleting the vault/.claude, piping a
             download into an interpreter ...)
  ask      — the user is asked (EVERY deletion, even of a single file — rule #22; killing by PID, irreversible git
             operations, stopping a service, a network call from the shell, writing to a defense file, a command that
             shows a secret, installing a package, moving a vault file to a temporary folder ...)
  (silent) — the permission flow continues as usual

Why: Claude Code's sandbox does not exist on native Windows; users' home folders and drive roots were deleted by a
wrong path expansion (`rm -rf ... ~/`, `$HOME` left empty, through a junction); `pkill node` / `taskkill /IM`
killed other people's applications and Claude itself.

Design principles:
- Deterministic (no LLM): the same command always gets the same decision.
- It tries to look at the target the command touches, not its "shape": if the target is home/root/vault/.claude,
  deny; every other recursive deletion, ask.
- False positives are accepted, false negatives are not: when unsure, ask.
- The hook must never crash: every error is swallowed and the decision becomes "ask" (outside Claude: deny).
- The vault is recognised by its own absolute path (all spellings: C:\\..., C:/..., /c/..., 8.3 short names,
  ~ / $HOME / %USERPROFILE%), not by a fixed folder name.

Known limits: a script that writes a file indirectly (a Python file run with `py x.py`) is not seen here (health.py
shows the change afterwards); a path or command name built from variables or by joining strings is not resolved.
"""
import bisect
import json
import os
import re
import shlex
import sys
from functools import lru_cache
from pathlib import Path

# The -I flag does not add the script folder to the path. It goes to the END: a file named after a standard library
# module (json.py) in the folder must not shadow a module imported later and take over the guard.
sys.path.append(str(Path(__file__).resolve().parent))
import hook_io  # noqa: E402  (standard library only: it answers in the client's format even when the others fail)
try:
    import common  # noqa: E402
    import session_mode as sm  # noqa: E402
    IMPORT_ERROR = ""
except Exception as _error:  # the guard must not crash on an import; main() answers FAIL (Claude asks, others deny)
    common = sm = None
    IMPORT_ERROR = f"{type(_error).__name__}: {_error}"

if IMPORT_ERROR:   # the patterns below are still built; main() never uses them
    VAULT, DEFENSE_SET = Path(__file__).resolve().parent.parent, ()

    def name(key: str) -> str:
        return key

    def vault_path(*parts: str) -> Path:
        return VAULT.joinpath(*parts)
else:
    from common import DEFENSE_SET, VAULT, name, vault_path  # noqa: E402

CLIENT = "claude"   # set from --client in main(); decides the answer format (hook_io.py)
# The hook times out after 10 s; an 80,000-character command with many redirections took 123 s with the old patterns
MAX_COMMAND = 20_000
LONG_COMMAND_REASON = (
    "The command is {length} characters; above {limit} characters the guard patterns do not run (hook time limit). "
    "Write the content to a file with Write and run it, or split it; approve if it is needed.",
    "Komut {length} karakter; {limit} karakterden uzun komutta kapı desenleri çalıştırılmaz (hook zaman aşımı). "
    "İçeriği Write ile dosyaya yazıp çalıştır ya da böl; gerekliyse onayla.")
LONG_UNRECORDED = (" This chat is unrecorded (#43): a command the guard cannot read is denied.",
                   " Bu sohbet kayıtsız (#43): kapının okuyamadığı komut reddedilir.")


def localized(pair: tuple[str, str]) -> str:
    """(English, Turkish) → the text in the install language (config.json `language`)."""
    return pair[1] if common and common.LANGUAGE == "tr" else pair[0]


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


VAULT_PATH = path_pattern(VAULT)
VAULT_AT = VAULT_PATH + END
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
DELETE = [  # (pattern, has a target capture group); the target ends at a command separator
    re.compile(r"(?i)(?<![\w-])rm\s+(?:-[a-z]*r[a-z]*\s+|-[a-z]*\s+)*(?:-[a-z]*r[a-z]*)?\s*([^;&|\n]*)"),  # rm -r* ...
    re.compile(r"(?i)(?<![\w-])(?:rmdir|rd)\s+/s\b([^;&|\n]*)"),
    re.compile(r"(?i)(?<![\w-])(?:del|erase)\s+(?:/\w\s+)*/s\b([^;&|\n]*)"),
    # the target may come before -Recurse too: `Remove-Item ~ -Recurse -Force`
    re.compile(r"(?i)(?<![\w-])(?:remove-item|ri|rm|del|erase|rd|rmdir)\b([^;&|\n]*-recurse\b[^;&|\n]*)"),
    re.compile(r"(?i)(?<![\w-])(?:remove-item|ri)\s+[^|\n]*-force\b([^;&|\n]*)"),
    re.compile(r"(?i)(?<![\w-])rimraf\s+([^;&|\n]*)"),
    re.compile(r"(?i)shutil\.rmtree\s*\(\s*(.*)"),
    re.compile(r"(?i)(?<![\w-])git\s+clean\b([^;&|\n]*)"),
    re.compile(r"(?i)(?<![\w-])(?:robocopy)\b[^|\n]*\s/mir\b([^;&|\n]*)"),
]
RM_R = re.compile(r"(?i)(?<![\w-])rm\s+(?:-\w*\s+)*-\w*r")  # whether rm is recursive

# Rule #22: EVERY deletion is asked, even of a single file (the reason is explained in the chat first).
# del/erase/rd only at the start of a command: a line start does not count, because a Python `del x` in a heredoc deletes no file.
# `{`: a PowerShell script block `foreach(…){ del $f }`
COMMAND_START = r"(?:^|[;&|({]\s*|\bcmd(?:\.exe)?\s+/c\s+)"
DELETE_SHELL = [  # searched outside quotes (text such as grep 'rm x' is not a command)
    r"(?i)(?<![\w.-])(?:rm|unlink|shred)\s+\S",
    r"(?i)\bxargs\s+(?:-\S+\s+)*(?:rm|del|unlink|shred)\b",
    r"(?i)(?<![\w.-])rmdir\s+\S",
    COMMAND_START + r"(?i:del|erase|rd)\s+\S",
    r"(?i)(?<![\w-])(?:remove-item|ri)\b",
    r"(?i)(?<![\w-])git\s+(?:rm|clean)\b",
    r"(?i)(?<![\w-])find\b[^|\n]*\s-delete\b",
    # commands that empty a file's content
    r"(?i)(?<![\w-])clear-content\b",
    COMMAND_START + r":\s*>(?!>)",
    r"(?i)(?<![\w.-])truncate\s+-",
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
    r"(?i)\.delete\s*\(\s*\)",                       # PowerShell `$_.Delete()`
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
SINGLE_QUOTED_C = re.compile(r"(?<![\w-])-c\s+'([^']*)'")
UNESCAPED_BACKTICK = re.compile(r"(?<!\\)`")
BACKTICK_REASON = (
    "A backtick runs as a command in the shell: the text inside a double-quoted `-c \"…\"` or an unquoted heredoc "
    "changes. Write the content to a file with Write and run it, or quote the heredoc with <<'EOF'. If it is used on "
    "purpose, approve. Part: `{part}`",
    "Ters tırnak (backtick) kabukta komut olarak çalışır: çift tırnaklı `-c \"…\"` ya da tırnaksız heredoc içindeki "
    "metin değişir. İçeriği Write ile dosyaya yazıp çalıştır ya da heredoc'u <<'EOF' ile tırnakla. Bilerek "
    "kullanılıyorsa onayla. Parça: `{part}`")

# Python in a heredoc and a sed expression turn `\b`, `\n` and the like into a control character or a real newline.
# Heredoc: header `<<-?\s*(['"]?)NAME\1`, body after the header line, end at the first line whose first word is NAME
# (may be indented; the backtick check of an unquoted heredoc looks for an unindented end). The old `(.*?)\n…NAME\b`
# pattern scanned from every header without an end to the end of the text; end lines are now indexed once.
HEREDOC_HEADER = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_]\w*)\1")
LINE_FIRST_WORD = re.compile(r"\n([ \t]*)(\w+)")
PYTHON_COMMAND = re.compile(r"(?i)(?<![\w.-])(?:py|python3?)(?:\.exe)?(?![\w.-])")   # script.py is not a command
# A backslash is only consumed as an escape: when two alternatives could eat the same character, backtracking grew
# exponentially (`sed s/x/` and 500 backslashes did not finish in 3 minutes). A single backslash before the
# delimiter is therefore not counted as a plain character.
SED_SUBSTITUTION = re.compile(r"(?<![\w-])sed\b[^|;&\n]*?(?<![\w-])s([^\w\s\\])((?:\\.|(?!\1)[^\\\n])*)\1((?:\\.|(?!\1)[^\\\n])*)\1")
BACKSLASH_ESCAPE = re.compile(r"\\[A-Za-z0-9\\]")
HEREDOC_BACKSLASH_REASON = (
    "Python in a heredoc mangles text with backslashes: write the content with Write as a .py script and use a raw "
    "string. Part: `{part}`",
    "Heredoc'taki Python ters bölülü metni bozar: içeriği Write ile .py betiği olarak yaz, r-dize (raw string) "
    "kullan. Parça: `{part}`")
SED_BACKSLASH_REASON = (
    "A backslash escape in a sed expression mangles the text: write the change with Write as a .py script and use a "
    "raw string. Part: `{part}`",
    "sed ifadesindeki ters bölü kaçışı metni bozar: değişikliği Write ile .py betiği olarak yaz, r-dize (raw string) "
    "kullan. Parça: `{part}`")

# From the download tool to the interpreter: the first stage and the pipes in between (tee, sed, Out-String …). Every
# stage starts with `|`; the possessive `*+` does not backtrack inside a stage.
PIPES_BETWEEN = r"[^|\n]*+(?:\|[^|\n]*+)*?"
DOWNLOADERS = r"(?:curl|wget|iwr|irm|invoke-webrequest|invoke-restmethod)\b"
DOWNLOAD_RUN = ("downloading from the internet and running it directly", "internetten indirip doğrudan çalıştırma")
DESTRUCTIVE = [  # deny in every case: (pattern, (English, Turkish))
    (r"(?i)(?<![\w-])(?:diskpart|format-volume|clear-disk|initialize-disk|remove-partition|mkfs\.?\w*|dd\s+if=)\b",
     ("disk formatting / partition operation", "disk biçimlendirme / bölüm işlemi")),
    # not the word 'format' alone: uses such as --date=format: are allowed
    (r"(?i)(?:^|[;&|(]\s*|\bcmd(?:\.exe)?\s+/c\s+)format(?:\.com|\.exe)?\s+[a-z]:",
     ("disk formatting (format <drive>:)", "disk biçimlendirme (format <sürücü>:)")),
    (r"(?i)(?<![\w-])(?:cipher\s+/w|bcdedit|bootrec|bootsect)\b", ("boot / disk wiping tool", "önyükleme / disk silme aracı")),
    (r"(?i)(?<![\w-])(?:shutdown|stop-computer|restart-computer|logoff|rundll32\s+user32\.dll,lockworkstation)\b",
     ("shutting down / restarting the computer", "bilgisayarı kapatma / yeniden başlatma")),
    (r"(?i)(?<![\w-])reg(?:\.exe)?\s+(?:delete|add)\s+[\"']?hk(?:lm|ey_local_machine)",   # a quoted key too
     ("HKLM registry change", "HKLM kayıt defteri değişikliği")),
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
    # PIPES_BETWEEN: the stream reaches the interpreter even with other commands in between (`curl … | tee a | bash`)
    (r"(?i)" + DOWNLOADERS + PIPES_BETWEEN + r"\|\s*(?:sudo\s+)?(?:bash|sh|zsh|iex|invoke-expression|powershell|pwsh|python)\b",
     DOWNLOAD_RUN),
    (r"(?i)(?<![\w-])(?:iex|invoke-expression)\s*\(?\s*(?:\(?\s*)?(?:iwr|irm|invoke-webrequest|invoke-restmethod|new-object\s+net\.webclient|\[system\.net)",
     DOWNLOAD_RUN),
    # an interpreter that reads its script from stdin (`| py -`), process substitution, decoding base64 and running it
    (r"(?i)" + DOWNLOADERS + PIPES_BETWEEN + r"\|\s*(?:sudo\s+)?(?:py|python3?|node)(?:\.exe)?"
     r"(?:(?:\s+-[\w.]+)*\s+-(?![\w.-])|\s*(?=$|[;&|)\n]))",
     ("downloading from the internet and running it directly (an interpreter reading stdin)",
      "internetten indirip doğrudan çalıştırma (stdin'den yorumlayıcıya)")),
    (r"(?i)(?<![\w-])(?:bash|sh|zsh|dash|ksh|source|\.|py|python3?|node)\s+(?:-\S+\s+)*<\(\s*(?:curl|wget|iwr|irm)\b",
     ("downloading from the internet and running it directly (process substitution)",
      "internetten indirip doğrudan çalıştırma (süreç ikamesi)")),
    (r"(?i)(?<![\w-])base64\s+(?:-\S+\s+)*(?:-d|--decode)\b[^|\n]*\|\s*(?:sudo\s+)?(?:bash|sh|zsh|dash|ksh|iex|invoke-expression|powershell|pwsh|py|python3?|node|perl|ruby)\b",
     ("decoding encoded text and running it directly", "kodlanmış metni çözüp doğrudan çalıştırma")),
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
    # the PID found from a name or a port, PowerShell aliases, .NET and WMI routes
    (r"(?i)(?<![\w-])kill\s+(?:-\w+\s+)*(?:\$\(|`)",
     ("killing a process found by name or port (kill $(pgrep …), kill $(lsof …))",
      "isimden ya da porttan bulunan süreci öldürme (kill $(pgrep …), kill $(lsof …))")),
    (r"(?i)\bxargs\s+(?:-\S+\s+)*kill\b",
     ("killing a process found by name (… | xargs kill)", "isimden bulunan süreci öldürme (… | xargs kill)")),
    (r"(?i)(?<![\w-])(?:kill|spps)\b[^;&|\n]*-(?:name|processname)\b",
     ("killing processes by name (kill/spps -Name)", "isme göre süreç öldürme (kill/spps -Name)")),
    (r"(?i)(?<![\w-])(?:get-process|gps)\b[^|\n]*\|\s*(?:spps|kill)\b", ("killing processes in bulk", "toplu süreç öldürme")),
    # capital K: .NET/PowerShell; Python's .kill() is asked in ASK_CODE
    (r"\.Kill\s*\(", ("killing a process object (.Kill())", "süreç nesnesini öldürme (.Kill())")),
    (r"(?i)(?<![\w-])wmic\b[^;&|\n]*\bprocess\b[^;&|\n]*\b(?:delete|terminate)\b",
     ("killing a process with WMI", "WMI ile süreç öldürme")),
    (r"(?i)(?<![\w-])(?:invoke-cimmethod|invoke-wmimethod)\b[^;&|\n]*\bterminate\b",
     ("killing a process with WMI", "WMI ile süreç öldürme")),
    (r"(?i)(?<![\w-])(?:remove-ciminstance|remove-wmiobject)\b",
     ("removing a CIM/WMI object (on Win32_Process it kills the process)",
      "CIM/WMI nesnesini silme (Win32_Process'te süreci öldürür)")),
]
DESTRUCTIVE_SUFFIX = (
    "This command is not run. If the port is busy pick a free port; if a process is needed find its PID with "
    "netstat/Get-NetTCPConnection and ask the user.",
    "Bu komut çalıştırılmaz. Port doluysa boş bir port seç; süreç gerekiyorsa PID'yi netstat/Get-NetTCPConnection ile "
    "bul ve kullanıcıya sor.")

ASK = [  # ask: (pattern, (English, Turkish))
    (r"(?i)(?<![\w-])taskkill\b[^|\n]*/pid\b",
     ("killing a process by PID: make sure the PID is not the user's application / Claude / the editor",
      "PID ile süreç öldürme: PID'nin kullanıcının uygulaması / Claude / editör olmadığından emin ol")),
    (r"(?i)(?<![\w-])(?:stop-process|spps)\b", ("killing a process", "süreç öldürme")),
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
    (r"(?i)(?<![\w-])(?:reg(?:\.exe)?\s+delete|remove-itemproperty)\b", ("deleting from the registry", "kayıt defteri silme")),
    (r"(?i)(?<![\w-])(?:schtasks\s+/create|register-scheduledtask|new-service|sc\s+create)\b",
     ("creating a scheduled task / service", "zamanlanmış görev / servis oluşturma")),
    # an install script runs code downloaded from the internet
    (r"(?i)(?<![\w-])(?:(?:pip3?|pipx|npm|pnpm|yarn|bun|winget|choco|scoop|uv\s+pip)\s+(?:-\S+\s+)*(?:install|i|add)|uv\s+add)\b",
     ("installing a package (it downloads and runs code from the internet; rules #19, #23: only with the user's approval)",
      "paket kurulumu (internetten kod indirip çalıştırır; kural #19, #23: kullanıcının onayıyla)")),
    (r"(?i)(?<![\w-])(?:npx|bunx|pipx\s+run)\s+(?!kill-port)[\w@./-]+",
     ("running a package from the internet with npx", "npx ile internetten paket çalıştırma")),
    (r"(?i)(?<![\w-])(?:chmod\s+-R\s+777|chown\s+-R)\b", ("bulk permission change", "toplu izin değişikliği")),
    (r"(?i)(?<![\w-])(?:mklink|new-item\s+-itemtype\s+(?:symboliclink|junction))\b",
     ("creating a link (symlink/junction)", "bağlantı (symlink/junction) oluşturma")),
    (r"(?i)(?<![\w-])(?:move-item|mv|move)\b[^|\n]*(?:-force|/y)\b", ("moving with overwrite", "üzerine yazarak taşıma")),
    # a sync that deletes what the source lacks, deleting after archiving, running a string as a command
    (r"(?i)(?<![\w-])robocopy\b[^;&|\n]*\s/purge\b",
     ("robocopy /purge (deletes target files missing from the source, rule #22)",
      "robocopy /purge (kaynakta olmayan dosyaları hedeften siler, kural #22)")),
    (r"(?i)(?<![\w-])rsync\b[^;&|\n]*\s--delete",
     ("rsync --delete (deletes target files missing from the source, rule #22)",
      "rsync --delete (kaynakta olmayan dosyaları hedeften siler, kural #22)")),
    (r"(?i)(?<![\w-])tar\b[^;&|\n]*\s--remove-files\b",
     ("tar --remove-files (deletes the archived files, rule #22)", "tar --remove-files (arşivlenen dosyaları siler, kural #22)")),
    (r"(?i)(?:^|[;&|({\n`]|\$\()\s*eval\s+\S",    # in command position: `grep eval` is text
     ("eval: a string runs as a command and the guard cannot see all of it",
      "eval: dizgi komut olarak çalışır, içi kapıdan tam görülmez")),
    # persistence and execution policy (rules #13, #19)
    (r"(?i)(?<![\w-])reg(?:\.exe)?\s+add\b", ("registry change", "kayıt defteri değişikliği")),
    (r"(?i)(?<![\w-])set-executionpolicy\b", ("execution policy change", "yürütme politikası değişikliği")),
    (r"(?i)(?<![\w-])-(?:executionpolicy|exec|ep)\s+[\"']?(?:bypass|unrestricted)\b",
     ("running a script past the execution policy", "yürütme politikasını atlayarak betik çalıştırma")),
    (r"(?i)(?<![\w-])setx(?:\.exe)?\b", ("permanent environment variable change (setx)", "kalıcı ortam değişkeni değişikliği (setx)")),
    # commands that print a token or the whole environment (rule #18)
    (r"(?i)(?<![\w-])gh\s+auth\s+(?:token\b|status\b[^;&|\n]*(?:--show-token|\s-t)\b)",
     ("printing the GitHub token", "GitHub token'ını ekrana basma")),
    (r"(?i)(?<![\w-])git\s+(?:-\S+\s+)*credential(?:-[\w-]+)?\b",
     ("reading or writing git credentials", "git kimlik bilgisini okuma ya da yazma")),
    (r"(?i)(?<![\w-])cmdkey(?:\.exe)?\b", ("the Windows credential store (cmdkey)", "Windows kimlik bilgisi deposu (cmdkey)")),
    (r"(?i)(?<![\w-])(?:get-childitem|gci|dir|ls|get-item|gi)\s+(?:-path\s+)?env:[\\/]?\*?(?=$|[\s;&|)])",
     ("printing every environment variable", "bütün ortam değişkenlerini ekrana basma")),
    (r"(?i)\[(?:system\.)?environment\]::getenvironmentvariables\b",
     ("printing every environment variable", "bütün ortam değişkenlerini ekrana basma")),
]
ASK_CODE = [  # inside a script (py -c "…", heredoc) asked even when quoted
    (r"\bos\.(?:replace|renames?)\s*\(|\bshutil\.move\s*\(",
     ("moving or renaming with Python: overwrites the target if it exists (rule #22)",
      "Python ile taşıma ya da yeniden adlandırma: hedef varsa üzerine yazar (kural #22)")),
    (r"(?i)\.kill\s*\(", ("killing a process (.kill())", "süreç öldürme (.kill())")),
    (r"(?i)currentversion[\\/]+run(?:once|services)?\b",
     ("starting automatically at sign-in (Run key, rule #13)", "oturum açılışında otomatik çalışma (Run anahtarı, kural #13)")),
]


# Writing to the vault's protected files (sources/, log.md) with the shell → ask. The shell side of write_guard.py.
# The target must follow the write operator in the same command part: a records.py call whose title contains "log.md"
# is not a write. The target is searched after the operator, in the same part (write_target): operator + lazy
# wildcard scanned from every operator to the end of the part, 123 s on 80,000 characters.
WRITE_OPERATOR = re.compile(r"(?i)(?:(?<![<>=&\d-])>{1,2}|(?<![\w-])(?:sed\s+(?:-\w+\s+)*-i\S*|perl\s+(?:-\w+\s+)*-\w*i\w*|set-content|out-file"
                            r"|add-content|tee(?:-object)?|truncate|cp|copy|copy-item|mv|move|move-item)\b)")
PART_END = re.compile(r"[|;&\n]")
PROTECTED_TAIL = (rf"(?:{re.escape(name('sources'))}[\\/]|log\.md\b"
                  rf"|{re.escape(name('archive'))}[\\/]+(?:log|{re.escape(name('pending'))})[\\/])")
PROTECTED_ABSOLUTE = re.compile(r"(?i)" + VAULT_PATH + SEP + PROTECTED_TAIL)
PROTECTED_RELATIVE = re.compile(r"(?i)(?<![\w.\\/:-])(?:\.[\\/])?" + PROTECTED_TAIL)

# Secret files: the Read tool is blocked with a settings.json deny rule, reading them with the shell is asked too.
# Example files (.env.example, .env.sample, .env.template) carry no secrets and are allowed.
SECRET_FILE = re.compile(r"(?i)(?:^|[\s'\"=/\\])(?:\.env(?:\.(?:local|development|production|test|staging))?(?:\.local)?"
                         r"|id_(?:rsa|ed25519|ecdsa|dsa)(?:\.pub)?|[\w.-]+\.(?:pem|key|pfx|p12)|\.git-credentials|\.credentials\.json"
                         r"|\.ssh[\\/][^\s'\"]*)(?=$|[\s'\"|;&)<>])")
# A wildcard only expands outside quotes: `cat ~/.claude/.cred*` reads a secret, `echo '.env*' >> .gitignore` does not
SECRET_WILDCARD = re.compile(r"(?i)(?<![\w.-])(?:\.(?:cred|env|git-cred)[\w.-]*\*|[\w.-]*\*[\w.-]*\.(?:pem|key|pfx|p12)\b|id_\*)")


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


def git_subcommand_index(words: list[str]) -> int:
    """`git -C x -c a=b status` → the index of status; len(words) when there is no sub-command."""
    i = 1
    while i < len(words) and words[i].startswith("-"):
        i += 1 if "=" in words[i] or words[i] not in GIT_VALUE_OPTIONS else 2
    return min(i, len(words))


def git_reads(words: list[str]) -> bool:
    i = git_subcommand_index(words)
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
    escapes the next character outside single quotes (the old count was O(n²) and treated "'" as an open quote)."""
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


# A wrapper is found by its flag first (`-c "…"`), then the shell name is looked for backwards in the same part: a lazy
# scan from the shell name to the flag ran to the end of the line for every `bash`.
SHELL_NAME = re.compile(r"(?i)(?<![\w-])(?:bash|sh|zsh|dash|ksh|cmd(?:\.exe)?|powershell(?:\.exe)?|pwsh(?:\.exe)?)\b")
SHELL_FLAG = re.compile(r"""(?i)\s(?:-c|/c|/k|-command|-cmd)\s+(?:"((?:[^"\\]|\\.)*)"|'([^']*)')""")
SHELL_BOUNDARY = re.compile(r"""[\n;&|"']""")
EVAL_INNER = re.compile(r"""(?i)(?<![\w.$-])eval\s+(?:"((?:[^"\\]|\\.)*)"|'([^']*)')""")
START_PROCESS = re.compile(r"""(?i)(?<![\w-])(?:start-process|saps)\s+(?:-filepath\s+)?["']?([\w.\\/:-]+)""")
ARGUMENT_LIST = re.compile(r"""(?i)\s-argumentlist\s+(?:"((?:[^"\\]|\\.)*)"|'([^']*)')""")
ARGUMENT_BOUNDARY = re.compile(r"[\n;|]")
WRAPPER_DEPTH = 3


def quoted(m: re.Match) -> str:
    """The filled one of a double- or single-quoted capture group."""
    return m.group(1) if m.group(1) is not None else m.group(2)


class PartSearch:
    """The first match of a pattern in the part of a position (after a boundary character); every part is scanned once."""

    def __init__(self, text: str, boundary: re.Pattern, pattern: re.Pattern):
        self.text, self.pattern = text, pattern
        self.boundaries = [m.start() for m in boundary.finditer(text)]
        self.firsts: dict[int, re.Match | None] = {}

    def before(self, position: int) -> re.Match | None:
        """The first match before `position` in the same part, if any."""
        index = bisect.bisect_left(self.boundaries, position)
        start = self.boundaries[index - 1] + 1 if index else 0
        if start not in self.firsts:
            end = self.boundaries[index] if index < len(self.boundaries) else len(self.text)
            self.firsts[start] = self.pattern.search(self.text, start, end)
        first = self.firsts[start]
        return first if first and first.end() <= position else None


def wrapped_commands(layer: str) -> list[str]:
    """The commands inside `bash -c "…"`, `eval "…"` and `Start-Process x -ArgumentList '…'`."""
    shell = PartSearch(layer, SHELL_BOUNDARY, SHELL_NAME)
    inner = [quoted(m) for m in SHELL_FLAG.finditer(layer) if shell.before(m.start() + 1)]
    inner += [quoted(m) for m in EVAL_INNER.finditer(layer)]
    starter = PartSearch(layer, ARGUMENT_BOUNDARY, START_PROCESS)
    for m in ARGUMENT_LIST.finditer(layer):
        started = starter.before(m.start() + 1)
        if started:
            inner.append(f"{started.group(1)} {quoted(m)}")
    return inner


def with_inner_commands(text: str) -> str:
    """The command plus, on lines of their own, the commands wrapped in `bash -c "…"`, `cmd /c "…"`,
    `powershell -Command "…"`, `eval "…"` and `Start-Process -ArgumentList` (a wrapped deletion was read as quoted text)."""
    found, layer = [], text
    for _ in range(WRAPPER_DEPTH):
        inner = wrapped_commands(layer)
        if not inner:
            break
        found += inner
        layer = "\n".join(inner)
    return "\n".join([text, *found])


# A hidden command name: a quoted name or one with quotes and backslashes sprinkled in (`"rm" -rf ~/`, `c''url`,
# `"r""m"`, `r\m`) and a leading assignment or prefix (`HUSKY=0 git …`, `command curl …`) blinded the guard. The opened
# form of the part is added as a line of its own and every pattern looks at it too; PowerShell's `&` call operator is a
# part separator. A quote with a space in it (`'rm -rf ~/' | Out-File`) is text and is not opened.
HIDDEN_NAME = re.compile(r"""\s*[({]*\s*((?:[\w.-]|\\.|'[^'\s]*'|"[^"\s]*")+)(?=\s|$)""")
NAME_HIDERS = re.compile(r"""[\\'"]""")
PREFIXES = ("command", "builtin", "exec", "env", "nohup", "time", "sudo", "nice")   # prefixes that run the real command
ASSIGNMENT = re.compile(r"[A-Za-z_]\w*=.*", re.S)
PREFIX = re.compile(r"""\s*(?:[A-Za-z_]\w*=(?:'[^']*'|"[^"]*"|[^\s'"]*)\s+|(?i:%s)(?:\s+(?:-\S*|\d+))*\s+)+""" % "|".join(PREFIXES))
COMPUTED_NAME = re.compile(r"\s*(?:\$\(|`)")
COMPUTED_NAME_REASON = (
    "computed command name: the guard cannot see which command `$(…)` or a backtick builds; write the command by its "
    "plain name. Part: `{part}`",
    "hesaplanan komut adı: `$(…)` ya da ters tırnakla kurulan komutun ne olduğu kapıdan görülmez; komutu açık adıyla "
    "yaz. Parça: `{part}`")


def after_prefixes(part: str) -> str:
    """The part without its leading assignments and prefixes (`FOO=1`, `command`, `sudo -E` …)."""
    prefix = PREFIX.match(part)
    return part[prefix.end():] if prefix else part


@lru_cache(maxsize=8)
def parts(text: str) -> tuple[tuple[int, str], ...]:
    """Command parts split at separators outside quotes (; & | && || and line ends): (start, part)."""
    flags, found, start = quote_map(text), [], 0
    for m in PART_SEPARATOR.finditer(text):
        if flags[m.start()]:
            continue
        found.append((start, text[start:m.start()]))
        start = m.end()
    found.append((start, text[start:]))
    return tuple(found)


def opened_part(part: str) -> str:
    """The part without prefixes and with the quotes and backslashes inside its first word removed; empty if unchanged."""
    body = after_prefixes(part)
    first = HIDDEN_NAME.match(body)
    if first and NAME_HIDERS.search(first.group(1)):
        body = NAME_HIDERS.sub("", first.group(1)) + body[first.end():]
    return body if body.strip() and body != part else ""


def open_command_names(text: str) -> str:
    opened = [open_ for _, part in parts(text) if (open_ := opened_part(part))]
    return "\n".join([text, *opened])


def computed_name_part(text: str) -> str:
    """The part whose command name is computed with `$(…)` or a backtick; empty if none."""
    for _, part in parts(shell_text(text)):
        if COMPUTED_NAME.match(after_prefixes(part)):
            return part_of(part, 0)
    return ""


def find_unquoted(pattern, text: str):
    """The first match outside quotes."""
    for m in re.finditer(pattern, text):
        if not inside_quotes(text, m.start()):
            return m
    return None


def decide(decision: str, reason: str) -> None:
    hook_io.emit(CLIENT, decision, f"{localized(('[Command guard]', '[Koruma kapısı]'))} {reason}")


def part_of(text: str, position: int) -> str:
    """The command from `position` to the end of the line, as long as the reason shows. If the line is empty (the match
    started at a line end), the next filled line: an empty part must not look like "no match"."""
    while True:
        end = text.find("\n", position)
        line = (text[position:] if end < 0 else text[position:end]).strip()
        if line or end < 0:
            break
        position = end + 1
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


@lru_cache(maxsize=8)
def end_lines(text: str) -> tuple[dict, dict]:
    """Lines by their first word: (all, unindented); each maps word → [(the \\n before the line, end of the word)]."""
    every, unindented = {}, {}
    for m in LINE_FIRST_WORD.finditer(text):
        entry = (m.start(), m.end())
        every.setdefault(m.group(2), []).append(entry)
        if not m.group(1):
            unindented.setdefault(m.group(2), []).append(entry)
    return every, unindented


def _heredocs(text: str, ends: dict, unquoted_only: bool) -> list[tuple[re.Match, int, int]]:
    found, position = [], 0
    while header := HEREDOC_HEADER.search(text, position):
        line_end = text.find("\n", header.end())
        if line_end < 0:
            break     # the later headers have no body either
        candidates = [] if unquoted_only and header.group(1) else ends.get(header.group(2), [])
        index = bisect.bisect_left(candidates, (line_end + 1,))
        if index == len(candidates):
            position = header.start() + 1
            continue
        body_end, end_word = candidates[index]
        found.append((header, line_end + 1, body_end))
        position = end_word
    return found


@lru_cache(maxsize=8)
def heredocs(text: str) -> tuple[tuple[re.Match, int, int], ...]:
    """Heredocs: (header, body start, body end)."""
    return tuple(_heredocs(text, end_lines(text)[0], False))


def unquoted_heredocs(text: str) -> list[tuple[re.Match, int, int]]:
    """Heredocs whose body the shell expands (unquoted delimiter, unindented end)."""
    return _heredocs(text, end_lines(text)[1], True)


def header_line(text: str, header: re.Match, body_start: int) -> str:
    return text[text.rfind("\n", 0, header.start()) + 1:body_start]


def backtick_part(text: str) -> str:
    """The part with an unescaped backtick in a double-quoted -c argument or an unquoted heredoc body."""
    for m in DOUBLE_QUOTED_C.finditer(text):
        if not inside_quotes(text, m.start()) and UNESCAPED_BACKTICK.search(m.group(1)):
            return part_of(text, m.start())
    for header, start, end in unquoted_heredocs(text):
        if UNESCAPED_BACKTICK.search(text, start, end):
            return part_of(text, header.start())
    return ""


def heredoc_python_escape(text: str) -> str:
    """The line of a Python heredoc body that holds a backslash escape, or empty text."""
    for header, start, end in heredocs(text):
        if not PYTHON_COMMAND.search(header_line(text, header, start)):
            continue
        escape = BACKSLASH_ESCAPE.search(text, start, end)
        if escape:
            return part_of(text, text.rfind("\n", 0, escape.start()) + 1)
    return ""


def sed_escape(text: str) -> str:
    """The part of an unquoted sed `s/…/…/` expression that holds a backslash escape, or empty text."""
    for m in SED_SUBSTITUTION.finditer(text):
        if not inside_quotes(text, m.start()) and BACKSLASH_ESCAPE.search(m.group(2) + m.group(3)):
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


def write_target(text: str, target: re.Pattern) -> re.Match | None:
    """A write operator outside quotes with the target after it in the same command part, if any."""
    flags, checked = quote_map(text), 0
    for operator in WRITE_OPERATOR.finditer(text):
        if operator.start() < checked or flags[operator.start()]:
            continue     # the first operator of this part already looked to its end
        end = PART_END.search(text, operator.end())
        checked = end.start() if end else len(text)
        if target.search(text, operator.end(), checked):
            return operator
    return None


def words_of(part: str) -> list[str]:
    """The words of a part with quotes removed, starting at the real command (a backslash is not an escape: Windows
    paths must stay whole)."""
    lexer = shlex.shlex(part, posix=True, punctuation_chars=False)
    lexer.whitespace_split, lexer.escape, lexer.commenters = True, "", ""
    try:
        return drop_prefixes(list(lexer))
    except ValueError:   # an unclosed quote
        return drop_prefixes(part.split())


def drop_prefixes(words: list[str]) -> list[str]:
    """Leading assignments (`FOO=1`) and prefixes (`time`, `sudo -E` …) are dropped; if no command is left (a lone
    `env`), the words stay as they are."""
    index = 0
    while index < len(words):
        if ASSIGNMENT.fullmatch(words[index]):
            index += 1
        elif words[index].lower() in PREFIXES:
            index += 1
            while index < len(words) and (words[index].startswith("-") or words[index].isdigit()):
                index += 1
        else:
            break
    return words[index:] or words


def command_name(word: str) -> str:
    """`C:\\Program Files\\Git\\bin\\git.exe` → `git`."""
    return re.sub(r"(?i)\.exe$", "", re.split(r"[\\/]", word)[-1]).lower()


# --- Defense files ---------------------------------------------------------
# Guard scripts, hook settings and permissions, scheduled tasks, agent definitions, the commit hook, the blocklist,
# the rules and the instructions: if one changes, the other rules are only written down. The members live in
# common.DEFENSE_SET (one definition with the write guard); here they become patterns for the command text. Running a
# script, reading, git add/commit are not writes.
NAME_END = r"(?![\w.-])"
COMMAND_END = r"""(?=$|[\s'"`;&|)])"""


def name_pattern(file_pattern: str) -> str:
    """A file name pattern (* and ?) → the pattern searched in the command text."""
    return "".join(r"[\w.-]*" if char == "*" else r"[\w.-]" if char == "?" else re.escape(char) for char in file_pattern)


def text_folder(member) -> list[str]:
    """The folder parts of a member as searched in the command text. Folders are searched without the vault or home
    prefix too (a relative path, a worktree); a file in the vault root only with the vault's own path."""
    folder = [re.escape(segment) for segment in member.folder.split("/") if segment]
    return folder or ([VAULT_PATH] if member.root == "vault" else [])


def member_end(member) -> str:
    """What follows the folder: for a "**" member the folder itself (what is under it is covered too), else the file name."""
    return NAME_END if member.pattern == "**" else SEP + name_pattern(member.pattern) + NAME_END


def defense_patterns(members) -> list[str]:
    """Defense path patterns for the command text. The folder of a member with a wildcard name alone too
    (cp settings.json ~/.claude/)."""
    patterns = []
    for member in members:
        folder = SEP.join(text_folder(member))
        patterns.append(r"(?<![\w-])" + folder + member_end(member))
        if member.pattern != "**" and ("*" in member.pattern or "?" in member.pattern):
            patterns.append(r"(?<![\w-])" + folder + r"[\\/]*" + COMMAND_END)
    return list(dict.fromkeys(patterns))


def defense_context(members) -> list[tuple[str, str]]:
    """(end of the cwd or a `cd` target, the relative path written in that folder): `cd _system && echo x > a.py`
    writes to a defense file too."""
    context = []
    for member in members:
        segments = text_folder(member)
        for index in range(1, len(segments) + 1):
            rest = segments[index:]
            if rest:
                context.append((SEP.join(segments[:index]), SEP.join(rest) + member_end(member)))
            elif member.pattern != "**":
                context.append((SEP.join(segments), name_pattern(member.pattern) + NAME_END))
        if member.pattern == "**":    # inside the folder every name
            context.append((SEP.join(segments) + r"(?:[\\/]+[^\\/\s]+)*", r"[\w.-]+"))
    return list(dict.fromkeys(context))


DEFENSE = re.compile("|".join(defense_patterns(DEFENSE_SET)) or r"(?!)", re.I)   # nothing if the set did not load
DEFENSE_CONTEXT = tuple(defense_context(DEFENSE_SET))
BARE_NAME = r"(?<![\w./\\~$:%-])(?:\.[\\/]+)?(?:{})"
PYTHON_NAMES = {"py", "python", "python3"}
COPIERS = {"cp", "copy", "copy-item", "cpi", "xcopy"}   # read the source, write only the target
GIT_NOT_WRITING = {"add", "commit"}                      # git sub-commands that do not change a defense file (besides the reading ones)
PY_WRITE = re.compile(r"""(?x)
      \bopen\s*\([^\n;]{0,200}?,\s*(?:mode\s*=\s*)?\\?['"][rbt]*[wax][rbt+]*\\?['"]
    | \.open\s*\(\s*(?:mode\s*=\s*)?\\?['"][rbt]*[wax][rbt+]*\\?['"]
    | \.write_(?:text|bytes)\s*\(
    | \bshutil\.(?:copy\w*|move)\s*\(
    | \bos\.(?:replace|renames?)\s*\(""")
PY_VALUE_OPTIONS = {"-X", "-W"}                             # interpreter options whose value is the next word
VAULT_SCRIPT = re.compile(r"(?i)(?:^|[\\/])" + re.escape(name("_system")) + r"[\\/]")
DEFENSE_REASON = (
    "Writing to a defense file with the shell: `{path}`. If the guard scripts, the hook settings and permissions, the "
    "scheduled tasks, the agent definitions, the commit hook, the blocklist, the rules or the instructions change, the "
    "other rules are only written down. Approve if the user asked for the change. Part: `{part}`",
    "Savunma dosyasına kabukla yazma: `{path}`. Kapı betikleri, hook ayarı ve izinler, zamanlanmış görevler, ajan "
    "tanımları, commit kancası, kara liste, kurallar ve talimatlar değişirse öbür kurallar yalnızca yazılı kalır. "
    "Kullanıcı değişikliği istediyse onayla. Parça: `{part}`")


@lru_cache(maxsize=32)
def _defense_pattern(extra: tuple[str, ...]) -> re.Pattern:
    return re.compile(DEFENSE.pattern + "|" + BARE_NAME.format("|".join(extra)), re.I) if extra else DEFENSE


def defense_pattern(text: str, cwd: str) -> re.Pattern:
    """The defense path pattern; if the cwd or a `cd` target is a defense folder (.claude, _system, .git, rules …), the
    relative names written there too."""
    folders = [cwd, *(m.group(1).strip("\"'") for m in CHANGE_DIR.finditer(text))]
    extra = tuple(relative for folder, relative in DEFENSE_CONTEXT
                  if any(re.search(r"(?i)(?:^|[\\/])(?:" + folder + r")[\\/]*$", f) for f in folders if f))
    return _defense_pattern(extra)


@lru_cache(maxsize=8)
def shell_text(text: str) -> str:
    """The text the shell reads as commands: heredoc bodies written to a file (cat > x <<EOF) or given to Python are
    removed, bodies given to a shell (bash <<EOF) stay. A note or a commit message in a body is not a command."""
    kept, position = [], 0
    for header, start, end in heredocs(text):
        if SHELL_NAME.search(header_line(text, header, start)):
            continue
        kept.append(text[position:start])
        position = end
    return "".join(kept) + text[position:]


def python_codes(text: str) -> list[str]:
    """Code given to Python: `-c "…"` / `-c '…'` arguments and the bodies of heredocs whose header line names Python."""
    if not PYTHON_COMMAND.search(text):
        return []
    codes = [m.group(1) for pattern in (DOUBLE_QUOTED_C, SINGLE_QUOTED_C) for m in pattern.finditer(text)]
    return codes + [text[start:end] for header, start, end in heredocs(text)
                    if PYTHON_COMMAND.search(header_line(text, header, start))]


def copy_target(words: list[str]) -> str:
    """The target of cp/Copy-Item: the -Destination value or the last word that is not an option."""
    for i, word in enumerate(words[:-1]):
        if word.lower() in ("-destination", "-dest", "-d"):
            return words[i + 1]
    names = [w for w in words[1:] if not w.startswith("-") and not re.fullmatch(r"/\w+", w)]
    return names[-1] if len(names) > 1 else ""


def python_script(arguments: list[str]) -> tuple[str, list[str]]:
    """The script that runs (`-` stdin, a `-m` module) and the arguments after it; ("", []) for `-c` code or no script."""
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument == "-c":
            return "", []
        if argument == "-m":
            return (arguments[index + 1], arguments[index + 2:]) if index + 1 < len(arguments) else ("", [])
        if argument in PY_VALUE_OPTIONS:
            index += 2
        elif argument.startswith("-") and argument != "-":
            index += 1
        else:
            return argument, arguments[index + 1:]
    return "", []


def python_argument_writes(words: list[str], pattern: re.Pattern) -> bool:
    """Is a defense path given to a script as an argument? The script may write that file and the guard cannot see
    inside it. The arguments of the vault's own _system/ scripts are not checked; -c and heredoc code is checked by
    python_codes."""
    script, arguments = python_script(words[1:])
    if not script or VAULT_SCRIPT.search(script) or pattern.search(script):
        return False
    return any(pattern.search(argument) for argument in arguments)


def writes_defense(text: str, start: int, part: str, pattern: re.Pattern) -> bool:
    """Does a part that names a defense path write? Reading, running a script, git add/commit and a copy source are not
    writes."""
    flags = quote_map(text)
    for operator in REDIRECT.finditer(part):
        if not flags[start + operator.start()] and pattern.search(part, operator.end()):
            return True
    words = words_of(part)
    command = command_name(words[0]) if words else ""
    if command in PYTHON_NAMES:     # before the reading-script names: tmp/search.py is not the vault's search.py
        return python_argument_writes(words, pattern)
    if part_reads(part):
        return False
    if command == "git":
        index = git_subcommand_index(words)
        return not (index < len(words) and words[index].lower() in READING_GIT | GIT_NOT_WRITING)
    if command in COPIERS:
        return bool(pattern.search(copy_target(words)))
    return True


def defense_write_part(text: str, cwd: str) -> tuple[str, str]:
    """The part that writes to a defense file and the path it touches; ("", "") if none."""
    pattern = defense_pattern(text, cwd)
    if not pattern.search(text):
        return "", ""
    for code in python_codes(text):
        path = pattern.search(code)
        if path and PY_WRITE.search(code):
            return part_of(code, 0), path.group(0)
    clean = NULL_REDIRECT.sub("", shell_text(text))
    for start, part in parts(clean):
        path = pattern.search(part)
        if path and writes_defense(clean, start, part, pattern):
            return part_of(part, 0), path.group(0)
    return "", ""


# --- Network calls (rule #32) ---------------------------------------------------------------------------------
# The site guard only sees the browser and WebFetch tools; a network call from the shell is asked, with the address in
# the reason. The tool name must be in command position (part start, `$(`, `(`, `=` ...): `grep -rn curl src/` does not
# go online. git push/pull/fetch without an address stay silent.
NETWORK_TOOL = re.compile(r"""(?ix) (?: ^ | [;&|(){}`=!\n] | \$\( | \b(?:sudo|time|xargs|exec|then|do|else|nohup)\s ) \s*
    (?P<tool> (?: [\w.\\/:-]*[\\/] )? (?: curl | wget | iwr | irm | invoke-webrequest | invoke-restmethod | start-bitstransfer
                                       | certutil (?=(?:\.exe)?\b[^;&|\n]*-urlcache\b) ) (?:\.exe)? \b )""")
PY_NETWORK = re.compile(r"(?:\bimport\s+(?:[\w.]+\s*,\s*)*|\bfrom\s+|__import__\(\s*\\?['\"])(?:urllib|requests|httpx|socket|http\.client|aiohttp|webbrowser)\b"
                        r"|\bfrom\s+http\s+import\s+client\b")
# Python code can hand a network tool to the shell (`os.system('curl …')`, `subprocess.run(['wget', …])`)
PY_SHELL = re.compile(r"\bos\.(?:system|popen)\b|\bsubprocess\b")
NETWORK_TOOL_NAME = re.compile(r"(?i)(?<![\w-])(?:curl|wget|iwr|irm|invoke-webrequest|invoke-restmethod)(?![\w-])")
GIT_ADDRESS = re.compile(r"(?i)://|^[\w.-]+@[\w.-]+:")
ADDRESS = re.compile(r"(?i)\b(?:https?|ftp|ssh|git)://[^\s'\"<>|;`)]+|\b[\w.-]+@[\w.-]+\.[a-z]{2,}(?::[\w./~-]+)?")
DOMAIN = re.compile(r"(?i)(?<![\w.@/-])(?://)?((?:[a-z0-9-]+\.)+[a-z]{2,})(?=[/:\s'\"),\\]|$)")
NETWORK_REASON = (
    "A network call from the shell (rule #32): address {address}. If the user has not allowed this site in this chat, do "
    "not approve; if it sends data (POST, -d @file), check the content. Part: `{part}`",
    "Kabuktan ağa çıkış (kural #32): adres {address}. Site izni bu sohbette kullanıcıdan alınmadıysa onaylama; veri "
    "gönderiyorsa (POST, -d @dosya) içeriği kontrol et. Parça: `{part}`")
NO_ADDRESS = ("not seen", "görülemedi")
MOST_ADDRESSES = 3
# Raw sockets and remote shells; rsync and scp with a remote path (`host:path`, `host::module`); .NET network classes;
# network calls in code given to node/deno/bun; commands that open an address in the default browser (the browser
# goes around the site guard).
NETWORK_COMMANDS = {"nc", "ncat", "netcat", "telnet", "ssh", "sftp", "ftp"}
REMOTE_PATH_COMMANDS = {"rsync", "scp"}
REMOTE_PATH = re.compile(r"^(?:[\w.-]+@)?[\w.-]{2,}::?|^rsync://")       # a single letter is a drive (C:/a), not a host
DOTNET_NETWORK = re.compile(r"(?i)\b(?:system\.)?net\.(?:webclient|http|sockets|httpwebrequest|webrequest)\b|\bhttpclient\b")
JS_RUNNERS = {"node", "deno", "bun"}
JS_CODE_OPTIONS = {"-e", "-p", "--eval", "--print", "eval"}
JS_NETWORK = re.compile(r"""\bfetch\s*\(|\b(?:https?|net)\.\w|\baxios\b|require\(\s*['"](?:https?|net|axios)['"]""")
BROWSER_OPENERS = {"start", "explorer", "open", "xdg-open", "start-process", "saps"}
WEB_ADDRESS = re.compile(r"(?i)^(?:https?|ftp)://")


def git_goes_online(words: list[str]) -> bool:
    index = git_subcommand_index(words)
    sub, arguments = (words[index].lower(), words[index + 1:]) if index < len(words) else ("", [])
    if sub == "clone" or (sub == "remote" and arguments[:1] in (["add"], ["set-url"])):
        return True
    return sub in ("push", "pull", "fetch") and any(GIT_ADDRESS.search(a) for a in arguments)


def network_part(text: str) -> str:
    """The part of a command that goes online; empty if none."""
    shell = shell_text(text)
    tool = find_unquoted(NETWORK_TOOL, shell)
    if tool:
        return part_of(shell, tool.start("tool"))
    dotnet = find_unquoted(DOTNET_NETWORK, shell)
    if dotnet:
        return part_of(shell, dotnet.start())
    for _, part in parts(shell):
        words = words_of(part)
        if words and words_go_online(command_name(words[0]), words, part):
            return part_of(part, 0)
    return next((part_of(code, 0) for code in python_codes(text) if python_goes_online(code)), "")


def words_go_online(command: str, words: list[str], part: str) -> bool:
    """A network call by command name and words: git, gh api, network tools, a remote path, JavaScript code, opening an
    address in the browser."""
    arguments = words[1:]
    if command == "git":
        return git_goes_online(words)
    if command == "gh":
        return arguments[:1] == ["api"]
    if command in NETWORK_COMMANDS:
        return True
    if command in REMOTE_PATH_COMMANDS:
        return any(REMOTE_PATH.match(a) for a in arguments if not a.startswith("-"))
    if command in JS_RUNNERS:
        return bool(JS_CODE_OPTIONS & set(arguments)) and bool(JS_NETWORK.search(part))
    return command in BROWSER_OPENERS and any(WEB_ADDRESS.match(a) for a in arguments)


def python_goes_online(code: str) -> bool:
    """A network module is imported, or a network tool appears in the text of a call that goes to the shell."""
    return bool(PY_NETWORK.search(code) or (PY_SHELL.search(code) and NETWORK_TOOL_NAME.search(code)))


def addresses(text: str) -> str:
    found = ADDRESS.findall(text) or DOMAIN.findall(text)
    if re.search(r"(?i)(?<![\w-])gh\s+api\b", text):
        found.append("api.github.com")
    unique = list(dict.fromkeys(found))[:MOST_ADDRESSES]
    return ", ".join(f"`{a}`" for a in unique) if unique else localized(NO_ADDRESS)


# --- Checked by git and shell words -------------------------------------------------------------------------------
COMMIT_SHORT_WITH_VALUE = set("mFCct")        # the letters after these short options, or the next word, are a value
COMMIT_LONG_WITH_VALUE = {"--message", "--file", "--reuse-message", "--reedit-message", "--template", "--author", "--date",
                          "--fixup", "--squash", "--trailer", "--cleanup", "--pathspec-from-file"}
SECRET_NAME = re.compile(r"(?i)token|secret|passw|api_?key|credential|auth|private")
ENVIRONMENT_PRINTERS = {"printenv", "env", "set"}
TEXT_PRINTERS = {"echo", "printf", "write-output", "write-host", "write"}
VARIABLE = re.compile(r"\$\{?(?:env:)?(\w+)|%(\w+)%")      # $X, ${X}, $env:X, %X%
LONE_ENV_VARIABLE = re.compile(r"(?i)^\$\{?env:(\w+)\}?$")   # in PowerShell a lone `$env:X` prints the value
GIT_REASONS = {
    "hooks_path": ("changing the git hook path (core.hooksPath): the secret scan in the commit hook stops running",
                   "git kanca yolunu değiştirme (core.hooksPath): commit kancasındaki sır taraması devre dışı kalır"),
    "no_verify": ("skipping the commit hook (--no-verify / -n): the secret scan does not run",
                  "commit kancasını atlama (--no-verify / -n): sır taraması çalışmaz"),
    "checkout": ("git checkout -- <path>: the unsaved changes in the file are lost for good (rule #22)",
                 "git checkout -- <yol>: dosyadaki kaydedilmemiş değişiklikler geri alınamaz biçimde gider (kural #22)"),
    "restore": ("git restore <path>: the unsaved changes in the file are lost for good (rule #22)",
                "git restore <yol>: dosyadaki kaydedilmemiş değişiklikler geri alınamaz biçimde gider (kural #22)"),
    "worktree": ("deleting a working tree (git worktree remove, rule #22)", "çalışma ağacını silme (git worktree remove, kural #22)"),
    "patch": ("applying a patch (git apply / git am): a patch can change the defense files and the guard cannot see its content",
              "yama uygulama (git apply / git am): yama savunma dosyalarını değiştirebilir, içeriğini kapı göremez"),
    "plus_push": ("git push +<ref>: a forced push that overwrites the remote history",
                  "git push +<ref>: zorla gönderme, uzak geçmişi ezer"),
}
ALL_ENVIRONMENT = ("printing every environment variable (may hold a token, rule #18)",
                   "bütün ortam değişkenlerini ekrana basma (token içerebilir, kural #18)")
SECRET_VARIABLE = ("printing an environment variable with a secret name (rule #18)",
                   "sır adlı ortam değişkenini ekrana basma (kural #18)")


def commit_skips_hook(arguments: list[str]) -> bool:
    """Do the `git commit` arguments hold --no-verify or a short -n (e.g. -anm)? The value of -m ("n") does not count."""
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument == "--":
            break
        if argument == "--no-verify":
            return True
        if argument.startswith("--"):
            index += 2 if argument in COMMIT_LONG_WITH_VALUE else 1
            continue
        if argument.startswith("-") and len(argument) > 1:
            for position, letter in enumerate(argument[1:], start=1):
                if letter == "n":
                    return True
                if letter in COMMIT_SHORT_WITH_VALUE:
                    index += position == len(argument) - 1   # the value is the next word
                    break
        index += 1
    return False


def git_reason_key(words: list[str]) -> str:
    if any("core.hookspath" in w.lower() for w in words):
        return "hooks_path"
    index = git_subcommand_index(words)
    if index >= len(words):
        return ""
    sub, arguments = words[index].lower(), words[index + 1:]
    if sub == "commit" and commit_skips_hook(arguments):
        return "no_verify"
    if sub == "checkout" and "--" in arguments[:-1]:
        return "checkout"
    if sub == "restore" and not ({"--staged", "-S"} & set(arguments) and not {"--worktree", "-W"} & set(arguments)):
        return "restore"
    if sub == "worktree" and arguments[:1] == ["remove"]:
        return "worktree"
    if sub in ("apply", "am"):
        return "patch"
    if sub == "push" and any(a.startswith("+") for a in arguments):
        return "plus_push"
    return ""


def shell_word_reason(text: str) -> str:
    """Parts checked by their words: the git hook, discarding and forced pushes; printing the whole environment or a
    variable with a secret name."""
    for _, part in parts(shell_text(text)):
        words = words_of(part)
        command = command_name(words[0]) if words else ""
        if command == "git":
            key = git_reason_key(words)
            if key:
                return f"{localized(GIT_REASONS[key])}: `{part_of(part, 0)}`"
        elif command in ENVIRONMENT_PRINTERS and len(words) == 1:
            return f"{localized(ALL_ENVIRONMENT)}: `{part.strip()}`"
        elif prints_secret_variable(command, words):
            return f"{localized(SECRET_VARIABLE)}: `{part_of(part, 0)}`"
    return ""


def prints_secret_variable(command: str, words: list[str]) -> bool:
    """`printenv GITHUB_TOKEN`, `echo $X_TOKEN`, `Write-Output $env:API_KEY`, a lone `$env:API_KEY`."""
    if command == "printenv":
        return any(SECRET_NAME.search(w) for w in words[1:])
    if command in TEXT_PRINTERS:
        names = (m.group(1) or m.group(2) for w in words[1:] for m in VARIABLE.finditer(w))
        return any(SECRET_NAME.search(variable) for variable in names)
    lone = LONE_ENV_VARIABLE.match(words[0]) if len(words) == 1 else None
    return bool(lone and SECRET_NAME.search(lone.group(1)))


# --- Moving to a temporary folder -------------------------------------------------------------------------------
# A file moved from the vault to a temporary folder disappears from the vault and does not come back when the
# temporary folder is cleaned (rule #22).
MOVERS = {"mv", "move", "move-item", "mi"}
MOVE_TARGET_OPTIONS = {"-destination", "-dest", "-d", "-t", "--target-directory"}
TEMP_FOLDER = re.compile(r"(?i)^/tmp(?![\w.-])|\$env:te?mp\b|%te?mp%|appdata[\\/]+local[\\/]+temp(?![\w.-])")
TEMP_MOVE_REASON = (
    "Moving from the vault to a temporary folder: the file disappears from the vault and does not come back when the "
    "temporary folder is cleaned (rule #22). To put it away, move it to {archive}/; approve if the user asked. Part: `{part}`",
    "Vault'tan geçici klasöre taşıma: dosya vault'tan kaybolur, geçici klasör temizlenince geri gelmez (kural #22). "
    "Kaldırılacaksa {archive}/'e taşı; kullanıcı istediyse onayla. Parça: `{part}`")


def move_target(words: list[str]) -> tuple[str, int]:
    """The target of a move and its word index: the -Destination / -t value or the last word that is not an option;
    ("", -1) if none."""
    for index, word in enumerate(words[:-1]):
        if word.lower() in MOVE_TARGET_OPTIONS:
            return words[index + 1], index + 1
    names = [index for index, word in enumerate(words) if index and not word.startswith("-")]
    return (words[names[-1]], names[-1]) if len(names) > 1 else ("", -1)


def temp_move_part(text: str, cwd: str) -> str:
    """The part that moves from the vault (cwd or a cd target in the vault, or a path pointing at it) to a temporary folder."""
    cwd_in_vault = any(in_vault(d) for d in [cwd, *(m.group(1).strip("\"'") for m in CHANGE_DIR.finditer(text))] if d)
    for _, part in parts(shell_text(text)):
        words = words_of(part)
        if not words or command_name(words[0]) not in MOVERS:
            continue
        target, target_index = move_target(words)
        sources = [w for index, w in enumerate(words) if index and index != target_index and not w.startswith("-")]
        if TEMP_FOLDER.search(target) and (cwd_in_vault or any(in_vault(s) for s in sources)):
            return part_of(part, 0)
    return ""


def check(command: str, cwd: str, sid: str = "") -> None:
    if len(command) > MAX_COMMAND:   # before the patterns: a long input must not blow the time limit
        unrecorded = sm.is_unrecorded(sid)   # a command that is not read may write a record (#43)
        decide("deny" if unrecorded else "ask", localized(LONG_COMMAND_REASON).format(length=len(command), limit=MAX_COMMAND)
               + (localized(LONG_UNRECORDED) if unrecorded else ""))
        return
    text = open_command_names(with_inner_commands(command.strip()))
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

    if check_deletions(text, cwd):
        return

    # Writing/moving to the home or root folder (not deletion) — full path check
    if re.search(r"(?i)(?<![\w-])(?:mv|move|move-item|cp\s+-r|copy-item\s+[^|\n]*-recurse|robocopy|xcopy)\b", text) and (ROOT.search(text) or HOME.search(text)):
        decide("ask", localized(("Bulk move/copy into a drive root or the home folder.",
                                 "Sürücü kökü ya da ev dizinine toplu taşıma/kopyalama.")))
        return

    if write_target(text, PROTECTED_ABSOLUTE) or (in_vault(cwd) and write_target(text, PROTECTED_RELATIVE)):
        sources = name("sources")
        decide("ask", localized((
            f"Writing to a protected vault file with the shell: the raw sources under {sources}/ are not changed, log.md is "
            f"only appended to with `records.py log` (CLAUDE.md §2, §10). `{text[:160]}`",
            f"Vault'un korunan dosyasına kabukla yazma: {sources}/ altındaki ham kaynaklar değiştirilmez, log.md'ye yalnızca "
            f"`records.py log` ile eklenir (CLAUDE.md §2, §10). `{text[:160]}`")))
        return

    defense_part, defense_path = defense_write_part(text, cwd)
    if defense_part:
        decide("ask", localized(DEFENSE_REASON).format(path=defense_path, part=defense_part))
        return

    if SECRET_FILE.search(text) or find_unquoted(SECRET_WILDCARD, text):
        decide("ask", localized((
            "The command touches a secret file (.env, SSH key, .pem/.key, credentials; rule #18). Claude should not see "
            "the content of these files; if a value is needed, only where it is stored is written. If the command does not "
            f"print the content and is needed, approve: `{text[:160]}`",
            "Komut bir sır dosyasına dokunuyor (.env, SSH anahtarı, .pem/.key, kimlik bilgisi; kural #18). Claude bu "
            "dosyaların içeriğini görmemeli; değer gerekiyorsa yalnızca nerede durduğu yazılır. Komut içeriği ekrana "
            f"basmıyorsa ve gerekliyse onayla: `{text[:160]}`")))
        return

    if check_asks(text, cwd):
        return

    for finder, reason in ((backtick_part, BACKTICK_REASON), (heredoc_python_escape, HEREDOC_BACKSLASH_REASON),
                           (sed_escape, SED_BACKSLASH_REASON)):
        part = finder(text)
        if part:
            decide("ask", localized(reason).format(part=part))
            return


def check_deletions(text: str, cwd: str) -> bool:
    """Recursive and single deletions; True if it decided."""
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
            return True
        # If $HOME / a variable is empty the target may be the root: targets built with variables are denied
        if re.search(r"\$\{?\w+\}?\s*[\\/]|%\w+%[\\/]|\$env:\w+[\\/]", target_text) and not re.search(r"\$\{?(?:pwd|cwd)\}?", target_text, re.I):
            decide("deny", localized((
                f"The deletion target is built with an environment variable: `{shown}`. If the variable is empty, the root "
                "or the home folder is deleted (this has happened). Use a full, fixed path.",
                f"Silme hedefi bir ortam değişkeniyle kuruluyor: `{shown}`. Değişken boş kalırsa kök/ev dizini silinir "
                "(yaşanmış olay). Tam, sabit yol kullan.")))
            return True
        decide(hook_io.ASK_OR_DENY, localized(DELETE_REASON).format(part=shown) + " " + localized((
            "A recursive/forced deletion cannot be undone; if possible send it to the Recycle Bin.",
            "Özyinelemeli/zorlamalı silme geri alınamaz; mümkünse Geri Dönüşüm Kutusu'na gönder.")))
        return True
    deletion_part = simple_deletion_part(text)
    if deletion_part:
        decide(hook_io.ASK_OR_CLIENT, localized(DELETE_REASON).format(part=deletion_part))
        return True
    return False


def check_asks(text: str, cwd: str) -> bool:
    """The asking patterns, shell words, computed names, temporary moves and network calls; True if it asked."""
    for pattern, reason in ASK:
        if find_unquoted(pattern, text):
            decide("ask", f"{localized(reason)}: `{text[:160]}`")
            return True
    for pattern, reason in ASK_CODE:
        m = re.search(pattern, text)
        if m:
            decide("ask", f"{localized(reason)}: `{part_of(text, m.start())}`")
            return True
    word_reason = shell_word_reason(text)
    if word_reason:
        decide("ask", word_reason)
        return True
    computed = computed_name_part(text)
    if computed:
        decide("ask", localized(COMPUTED_NAME_REASON).format(part=computed))
        return True
    moved = temp_move_part(text, cwd)
    if moved:
        decide("ask", localized(TEMP_MOVE_REASON).format(archive=name("archive"), part=moved))
        return True
    online = network_part(text)
    if online:
        decide("ask", localized(NETWORK_REASON).format(address=addresses(text), part=online))
        return True
    return False


IMPORT_REASON = ("The guard could not load its helper modules (common, session_mode: {error}); the recording mode and the "
                 "rules could not be checked, the user should approve.")


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
        if IMPORT_ERROR:
            decide(hook_io.FAIL, IMPORT_REASON.format(error=IMPORT_ERROR))
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
