"""Secret scan before a commit: stops the commit if it finds a secret or a machine code (rule #18).

Why: checking `git diff --cached` by hand can be forgotten. A secret filter that is off by default protects
nobody; here it is on by default and automatic (rule #37).

Modes (from the vault root):
  secret_scan.py --staged     scans the lines added to the commit (the git pre-commit hook calls this)
  secret_scan.py --all        scans every text file tracked by git (health check)
  secret_scan.py --install    installs the .git/hooks/pre-commit hook (leaves another hook untouched)

If an example is written on purpose, put `secret-scan: allow` on the line (with a reason).
Found values are printed masked.
"""
import argparse
import ipaddress
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the -I flag does not add the script folder to the path
from common import VAULT, vault_path  # noqa: E402

ALLOW_MARKER = "secret-scan: allow"
HOOK = VAULT / ".git" / "hooks" / "pre-commit"
HOOK_SIGNATURE = "# mindgate secret_scan"
TEXT_EXTENSIONS = {".md", ".py", ".json", ".html", ".txt", ".yml", ".yaml", ".base", ".canvas", ".sh", ".ps1", ".cfg", ".toml"}
# "ornek" is the Turkish word for "example"; Turkish vaults use it as a placeholder too
PLACEHOLDER = re.compile(r"^(?:\$|<|\{|\*{3}|x{3,}|\.{3}|os\.environ|env|none|null|true|false|ornek|example|changeme)", re.I)
# Private networks (192.168..., Docker 172.17...) are the same in every home and identify nobody; only a public IP is a finding.
EXAMPLE_NETWORKS = [ipaddress.ip_network("93.184.216.34/32")]  # example.com; an example in documents
VERSION_PREFIX = re.compile(r"(?i)(?:\bv|sürüm|surum|version|release|==?)\s*$")

PATTERNS = [
    ("API key (sk-)", re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_\-]{20,}")),
    ("Hugging Face token", re.compile(r"\bhf_[A-Za-z0-9]{30,}")),
    ("GitHub token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}|\bgithub_pat_[A-Za-z0-9_]{40,}")),
    ("AWS key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("Private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("Product/license key", re.compile(r"\b(?:[A-Z0-9]{5}-){4}[A-Z0-9]{5}\b")),
    ("BitLocker recovery key", re.compile(r"\b(?:\d{6}-){7}\d{6}\b")),
    ("IBAN", re.compile(r"\bTR\d{2}(?:\s?\d{4}){5}\s?\d{2}\b")),
    ("MAC address", re.compile(r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b")),
]
# No letter/digit before the key, but `_` is allowed: OPENAI_API_KEY=..., DB_PASSWORD=...; quoted JSON key: "api_key": "..."
# (parola, şifre, sifre: Turkish words for password)
ASSIGNMENT = re.compile(r"(?i)(?<![A-Za-z0-9])(password|passwd|pwd|parola|şifre|sifre|api[_-]?key|apikey|secret|token|access[_-]?key)"
                        r"[\"']?\s*[:=]\s*[\"']?([^\s'\"`,;(){}\[\]]{8,})(\()?")
IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
CODE_EXPRESSION = re.compile(r"^[A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)+$")   # data.get, os.getenv, self.token


def mask(value: str) -> str:
    return value[:4] + "…" + f"({len(value)} characters)"


def ip_finding(line: str, m: re.Match) -> bool:
    try:
        ip = ipaddress.ip_address(m.group(0))
    except ValueError:
        return False   # like 999.1.2.3: not an IP
    if not ip.is_global or any(ip in network for network in EXAMPLE_NETWORKS):
        return False
    return not VERSION_PREFIX.search(line[: m.start()])   # "v1.0.0.12", "version 1.0.0.12"


def assignment_finding(m: re.Match) -> bool:
    value = m.group(2)
    return not (m.group(3) or PLACEHOLDER.match(value) or CODE_EXPRESSION.match(value))   # a call or attribute access is not a secret


def scan_line(line: str) -> list[tuple[str, str]]:
    """[(kind, masked value)]"""
    if ALLOW_MARKER in line:
        return []
    findings = [(kind, mask(m.group(0))) for kind, pattern in PATTERNS for m in pattern.finditer(line)]
    findings += [(f"Assigned secret ({m.group(1)})", mask(m.group(2))) for m in ASSIGNMENT.finditer(line) if assignment_finding(m)]
    findings += [("IP address", mask(m.group(0))) for m in IPV4.finditer(line) if ip_finding(line, m)]
    return findings


def git(*args: str) -> str:
    # core.quotepath=false: file names with non-ASCII characters are not quoted and escaped (they were skipped before)
    return subprocess.run(["git", "-C", str(VAULT), "-c", "core.quotepath=false", *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", check=True).stdout


def staged_lines() -> list[tuple[str, int, str]]:
    """Lines added to the commit: [(file, line no, text)]. Header lines are looked for only between `diff --git` and `@@`;
    an added line whose content starts with "++ " is not taken for a header."""
    result, file, no, in_header = [], "", 0, False
    for line in git("diff", "--cached", "-U0", "--no-color", "--diff-filter=ACMR").splitlines():
        if line.startswith("diff --git "):
            in_header, file = True, ""
        elif in_header and line.startswith("+++ "):
            path = line[4:].strip().strip('"')
            file = path[2:] if path.startswith("b/") else ""
        elif line.startswith("@@"):
            in_header = False
            m = re.search(r"\+(\d+)", line)
            no = int(m.group(1)) if m else 0
        elif not in_header and line.startswith("+") and file:
            result.append((file, no, line[1:]))
            no += 1
    return result


def tracked_lines() -> list[tuple[str, int, str]]:
    result = []
    for file in git("ls-files").splitlines():
        path = VAULT / file
        if path.suffix.lower() not in TEXT_EXTENSIONS or not path.is_file():
            continue
        for no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            result.append((file, no, line))
    return result


def scan(lines: list[tuple[str, int, str]]) -> list[str]:
    return [f"{file}:{no}: {kind}: {value}" for file, no, text in lines for kind, value in scan_line(text)]


def install_hook() -> str:
    if HOOK.is_file() and HOOK_SIGNATURE not in HOOK.read_text(encoding="utf-8", errors="replace"):
        return f"{HOOK} is another hook; left untouched. Ask the user."
    python = Path(sys.executable).as_posix()
    script = vault_path("_system", "secret_scan.py").relative_to(VAULT).as_posix()
    HOOK.write_text(f"#!/bin/sh\n{HOOK_SIGNATURE} (rule #18): stops the commit if it finds a secret. Written by secret_scan.py --install.\n"
                    f'exec "{python}" -I "$(git rev-parse --show-toplevel)/{script}" --staged\n',
                    encoding="utf-8", newline="\n")
    return f"hook installed: {HOOK}"


def hook_installed() -> bool:
    return HOOK.is_file() and HOOK_SIGNATURE in HOOK.read_text(encoding="utf-8", errors="replace")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Secret scan before a commit (rule #18)")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--staged", action="store_true")
    mode.add_argument("--all", action="store_true")
    mode.add_argument("--install", action="store_true")
    args = p.parse_args()
    if args.install:
        print(install_hook())
        return 0
    findings = scan(staged_lines() if args.staged else tracked_lines())
    if not findings:
        print("secret scan: clean")
        return 0
    print("SECRET SCAN: commit stopped (rule #18). Take the value out of the file; write only where it is kept "
          f"(e.g. \"OPENAI_API_KEY in .env\"). If it is an example written on purpose, add '{ALLOW_MARKER}' to the line.",
          file=sys.stderr)
    for f in findings:
        print("  " + f, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
