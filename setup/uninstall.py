"""Mindgate uninstaller: undoes what install.py recorded in ~/.claude/mindgate/install-manifest.json.

- settings.json and CLAUDE.md: put back from the backups when they have not changed since the install; when they
  changed, only the Mindgate hooks, import line or block are taken out.
- Installed skills, agents, scheduled tasks and ~/.claude/mindgate/ are not deleted: they are moved into
  ~/.claude/mindgate-removed-<time stamp>/. You can delete that folder yourself later.
- The vault is never touched; it holds your notes.

Usage:
  py -3 setup/uninstall.py [--dry-run] [--answers answers.json --home <folder>]
"""
from __future__ import annotations  # lets an old Python reach the version check

import argparse
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the -I flag does not add the script folder to the path
import installer_lib as lib  # noqa: E402
import installer_messages as msg  # noqa: E402

HANDLED_KINDS = ("settings", "instructions")   # "core" moves with ~/.claude/mindgate; "config" is in the vault


@dataclass
class FilePlan:
    path: Path
    before: bytes | None              # content on disk now
    final: bytes | None               # content after the uninstall; None = the file is moved away
    action: str = "missing"           # restore | clean | keep | move | missing
    backup: str = ""


@dataclass
class Plan:
    files: list = field(default_factory=list)
    moves: list = field(default_factory=list)       # existing paths to move into the removed folder
    missing: list = field(default_factory=list)
    vaults: list = field(default_factory=list)
    notes: list = field(default_factory=list)       # extra lines to show (e.g. a broken settings.json)


class Uninstaller:
    def __init__(self, home: Path, asker, dry_run: bool = False, output=print):
        self.home = home
        self.claude = lib.claude_dir(home)
        self.asker = asker
        self.dry_run = dry_run
        self.out = output
        self.language = "en"

    def say(self, key: str, /, **values) -> None:
        self.out(msg.text(self.language, key, **values))

    def run(self) -> int:
        try:
            manifest = lib.read_manifest(self.home)
        except (OSError, ValueError) as error:
            self.say("un_manifest_broken", error=error)
            return 2
        if manifest is None:
            self.say("un_no_manifest", path=lib.manifest_path(self.home))
            return 0
        installs = manifest["installs"]
        self.language = next((i.get("language") for i in reversed(installs) if i.get("language") in msg.LANGUAGES), "en")
        self.asker.language = self.language
        plan = self.build_plan(installs)
        target = lib.free_path(self.claude / f"{lib.REMOVED_PREFIX}{lib.stamp()}")
        self.show(plan, target)
        if self.dry_run:
            self.say("dry_run_done")
            return 0
        if not self.asker.yes_no("confirm", msg.text(self.language, "un_question"), False):
            self.say("cancelled")
            return 0
        try:
            self.execute(plan, target)
        except OSError as error:
            self.say("un_partial", error=error, path=target)
            return 1
        self.say("un_done", path=target)
        for vault in plan.vaults:
            self.say("un_vault", path=vault)
        return 0

    # ---------- plan ----------
    def build_plan(self, installs: list) -> Plan:
        plan = Plan()
        state: dict = {}
        for install in reversed(installs):
            if install.get("vault") and install["vault"] not in plan.vaults:
                plan.vaults.append(install["vault"])
            for entry in reversed(install.get("changed", [])):
                if entry.get("kind") in HANDLED_KINDS:
                    self.plan_file(plan, state, entry)
        plan.files = list(state.values())
        for install in reversed(installs):
            for key in ("skills", "agents", "tasks"):
                for raw in install.get(key, []):
                    self.plan_move(plan, Path(raw))
        self.plan_move(plan, lib.mindgate_dir(self.home))
        return plan

    def plan_move(self, plan: Plan, path: Path) -> None:
        if not lib.inside(path, self.claude) or path in plan.moves or path in plan.missing:
            return
        (plan.moves if path.exists() else plan.missing).append(path)

    def plan_file(self, plan: Plan, state: dict, entry: dict) -> None:
        path = Path(entry["path"])
        if not lib.inside(path, self.claude):
            return
        if path not in state:
            current = path.read_bytes() if path.is_file() else None
            state[path] = FilePlan(path, current, current)
        item = state[path]
        if item.final is None:
            return
        if lib.sha256(item.final) == entry.get("sha256"):
            self.undo_unchanged(item, entry)
        else:
            self.undo_changed(plan, item, entry)

    def undo_unchanged(self, item: FilePlan, entry: dict) -> None:
        backup = Path(entry["backup"]) if entry.get("backup") else None
        if backup is None:
            item.final, item.action = None, "move"
        elif backup.is_file():
            item.final, item.action, item.backup = backup.read_bytes(), "restore", str(backup)
        else:
            item.action = "keep"

    def undo_changed(self, plan: Plan, item: FilePlan, entry: dict) -> None:
        if entry["kind"] == "settings":
            try:
                settings = lib.parse_settings(item.final)
            except (ValueError, TypeError, UnicodeDecodeError):
                item.action = "keep"
                plan.notes.append(msg.text(self.language, "un_settings_broken", path=item.path))
                return
            commands: dict = {}
            for hook in entry.get("hooks", []):
                commands.setdefault(hook["event"], set()).add(hook["command"])
            item.final, item.action = lib.settings_bytes(lib.remove_hooks(settings, commands)), "clean"
        elif entry.get("created"):
            item.action = "keep"
        else:
            item.final, item.action = lib.encode(lib.remove_mindgate(lib.decode(item.final))), "clean"

    # ---------- show and run ----------
    def show(self, plan: Plan, target: Path) -> None:
        self.say("un_title")
        self.say("un_what")
        for item in plan.files:
            if item.action == "restore":
                self.say("un_restore", path=item.path, backup=item.backup)
            elif item.action == "clean":
                self.say("un_clean", path=item.path)
            elif item.action == "keep":
                self.say("un_keep", path=item.path)
            elif item.action == "move":
                self.say("un_move", path=item.path)
            else:
                self.say("un_missing", path=item.path)
        for path in plan.moves:
            self.say("un_move", path=path)
        for path in plan.missing:
            self.say("un_missing", path=path)
        for note in plan.notes:
            self.out(note)
        self.say("un_target", path=target)
        for vault in plan.vaults:
            self.say("un_vault", path=vault)

    def move(self, path: Path, target_root: Path, sub: str = "") -> None:
        """os.rename only: on the same disk a move never copies and deletes."""
        destination = lib.free_path(target_root / sub / path.relative_to(self.claude))
        destination.parent.mkdir(parents=True, exist_ok=True)
        os.rename(path, destination)

    def execute(self, plan: Plan, target: Path) -> None:
        target.mkdir(parents=True, exist_ok=False)
        for item in plan.files:
            if item.before == item.final or item.before is None:
                continue
            self.move(item.path, target, "" if item.final is None else "before-uninstall")
            if item.final is not None:
                lib.write_new(item.path, item.final)
        for path in plan.moves:
            self.move(path, target)


def parse_args(argv: list | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Remove what the Mindgate installer added (moves, never deletes)")
    p.add_argument("--dry-run", action="store_true", help="only list what would be done")
    p.add_argument("--answers", help="JSON file with the answer to the confirmation (tests): {\"confirm\": true}")
    p.add_argument("--home", help="home folder that holds .claude (default: your home folder)")
    return p.parse_args(argv)


def main(argv: list | None = None, output=print) -> int:
    args = parse_args(argv)
    home = Path(args.home).expanduser().resolve() if args.home else Path.home()
    try:
        asker = lib.make_asker(args.answers, home, output)
        return Uninstaller(home, asker, args.dry_run, output).run()
    except lib.InstallerError as error:
        output(str(error))
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
