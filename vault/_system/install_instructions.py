"""The master copy of the global instructions lives in the vault: `_system/instructions/global-CLAUDE.md` ->
`~/.claude/CLAUDE.md`.

Why: the global instructions load in every session and every project, so they belong under version control; a wrong
edit can then be undone. The master copy is kept in git and this script installs it. Edits are always made in the
vault copy.

The master copy holds the placeholders `{{VAULT}}` and `{{PY}}`; `install` fills them with `--vault` and `--py`.
`install` never overwrites the user's own `~/.claude/CLAUDE.md`: if the file exists, nothing is written and the
installer offers the choices (merge, keep, replace). A new file is written only with `--force-new` and only when no
file exists.

Usage (from the vault root):
  python _system/install_instructions.py status [--vault PATH] [--py CMD]   is the installed copy the same as the master
  python _system/install_instructions.py install --force-new [--vault PATH] [--py CMD]

Exit codes: 0 done (status: same), 1 status differs or an installed file exists (nothing written), 2 usage error.
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the -I flag does not add the script folder to the path
from common import CONFIG, VAULT, vault_path  # noqa: E402

SOURCE = vault_path("_system", "instructions") / "global-CLAUDE.md"
INSTALLED = Path.home() / ".claude" / "CLAUDE.md"
SAME, DIFFERENT, NOT_INSTALLED, NO_SOURCE = "same", "different", "not_installed", "no_source"
INSTALLED_NEW, EXISTING, NEEDS_FORCE_NEW = "installed", "existing", "needs_force_new"
EXISTING_MESSAGE = ("You already have your own instructions in ~/.claude/CLAUDE.md; nothing was written. "
                    "The installer will offer you options.")


def default_vault() -> str:
    return str(VAULT)


def default_py() -> str:
    """The Python command chosen at install (`python` in config.json); a common default otherwise."""
    return str(CONFIG.get("python") or ("py -3" if os.name == "nt" else "python3"))


def render(source: Path, vault: str, py: str) -> bytes:
    """The master copy with its placeholders filled; line endings are kept as they are."""
    text = source.read_bytes().decode("utf-8")
    return text.replace("{{VAULT}}", vault).replace("{{PY}}", py).encode("utf-8")


def status(source: Path = SOURCE, installed: Path = INSTALLED, vault: str | None = None, py: str | None = None) -> str:
    """'same', 'different', 'not_installed' or 'no_source'."""
    if not source.is_file():
        return NO_SOURCE
    if not installed.is_file():
        return NOT_INSTALLED
    wanted = render(source, vault or default_vault(), py or default_py())
    return SAME if installed.read_bytes() == wanted else DIFFERENT


def install(source: Path = SOURCE, installed: Path = INSTALLED, vault: str | None = None, py: str | None = None,
            force_new: bool = False) -> str:
    """Writes the filled master copy only as a new file. An existing file is never touched."""
    if not source.is_file():
        raise FileNotFoundError(f"master instructions not found: {source}")
    if installed.exists():
        return EXISTING
    if not force_new:
        return NEEDS_FORCE_NEW
    text = render(source, vault or default_vault(), py or default_py())
    installed.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(installed, "xb") as f:   # "x": fails if the file appeared in the meantime, so it is never overwritten
            f.write(text)
    except FileExistsError:
        return EXISTING
    return INSTALLED_NEW


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Install the global instructions from the vault's master copy")
    sub = p.add_subparsers(dest="command", required=True)
    for command in ("status", "install"):
        s = sub.add_parser(command)
        s.add_argument("--vault", default=None, help="value for {{VAULT}} (default: this vault)")
        s.add_argument("--py", default=None, help="value for {{PY}} (default: `python` in config.json)")
        if command == "install":
            s.add_argument("--force-new", action="store_true", help="write ~/.claude/CLAUDE.md if it does not exist")
    args = p.parse_args(argv)
    if args.command == "status":
        result = status(vault=args.vault, py=args.py)
        print(result)
        return 0 if result == SAME else 1
    try:
        result = install(vault=args.vault, py=args.py, force_new=args.force_new)
    except FileNotFoundError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    if result == EXISTING:
        print(EXISTING_MESSAGE)
        return 1
    if result == NEEDS_FORCE_NEW:
        print("~/.claude/CLAUDE.md does not exist; nothing was written. Run again with --force-new to create it.")
        return 2
    print(f"installed: {INSTALLED}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
