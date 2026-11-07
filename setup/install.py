"""Mindgate installer: sets up a second-brain vault and the Claude Code files (~/.claude) step by step.

Each step says what it does, why, and what happens if you say no; "no" skips that step. Nothing is written until you
confirm the summary at the end. Existing files are never overwritten; a file that is changed is backed up first.

Usage:
  py -3 setup/install.py                       (Windows)    python3 setup/install.py   (macOS, Linux)
  ... --dry-run                                 only show what would be written, then stop
  ... --answers answers.json --home <folder>    answer every question from a file (for tests)
"""
from __future__ import annotations  # lets an old Python reach the version check

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the -I flag does not add the script folder to the path
import installer_lib as lib  # noqa: E402
import installer_messages as msg  # noqa: E402

TOTAL_STEPS = 11


@dataclass
class Choices:
    language: str = "en"
    python: str = ""
    vault: Path | None = None
    reuse_vault: bool = False
    instructions: str = "skip"          # import | merge | write | skip | sync
    hooks: list = field(default_factory=list)
    hooks_present: list = field(default_factory=list)
    skills: list = field(default_factory=list)      # Bundles to copy (names already final)
    agents: list = field(default_factory=list)
    tasks: list = field(default_factory=list)       # English task keys
    config: lib.ConfigChoices | None = None


@dataclass
class Plan:
    actions: list = field(default_factory=list)
    record: dict = field(default_factory=dict)
    vault_count: int = 0


class Installer:
    def __init__(self, home: Path, asker, dry_run: bool = False, output=print):
        self.home = home
        self.asker = asker
        self.dry_run = dry_run
        self.out = output
        self.choices = Choices()
        self.today = date.today().isoformat()
        self.stamp = lib.stamp()
        self._vault_files = None
        self._obsidian = (lib.ObsidianInfo(False), None)

    # ---------- helpers ----------
    def t(self, key: str, /, **values) -> str:
        return msg.text(self.choices.language, key, **values)

    def say(self, key: str, /, **values) -> None:
        self.out(self.t(key, **values))

    def step(self, number: int, title_key: str) -> None:
        self.say("step", number=number, total=TOTAL_STEPS, title=self.t(title_key))

    def values(self) -> lib.Values:
        c = self.choices
        return lib.Values(c.vault or self.home, c.python, self.home, c.language, msg.USER_WORD[c.language])

    def names(self) -> dict:
        return lib.load_names(self.choices.language)

    def vault_files(self) -> list:
        """The new vault in memory, built from the final choices (cached)."""
        if self._vault_files is None:
            config = lib.apply_config(lib.base_config(), self.choices.config or self.config_choices())
            self._vault_files = lib.build_vault(self.choices.language, self.values(), config, self.today)
        return self._vault_files

    def config_choices(self) -> lib.ConfigChoices:
        return lib.ConfigChoices(self.choices.language, self.choices.python)

    def claude(self) -> Path:
        return lib.claude_dir(self.home)

    # ---------- steps ----------
    def run(self) -> int:
        self.choose_language()
        if not self.check_environment():
            self.say("stopped")
            return 1
        self.choose_python()
        if self.choose_vault():
            self.choose_instructions()
            self.choose_hooks()
            self.choose_skills_and_agents()
            self.choose_tasks()
            self.choose_optional_rules()
        return self.summarize_and_write()

    def choose_language(self) -> None:
        info = lib.detect_obsidian(self.home)
        from_obsidian = lib.obsidian_language(info.config) if info.found else None
        suggested = from_obsidian if from_obsidian in msg.LANGUAGES else lib.detect_os_language()
        hint = msg.LANGUAGE_HINT["obsidian" if from_obsidian in msg.LANGUAGES else "system"]
        self.out(msg.LANGUAGE_QUESTION)
        self.out(hint.format(language=suggested))
        self.choices.language = self.asker.choose("language", "Language / Dil", list(msg.LANGUAGES), suggested)
        self.asker.language = self.choices.language
        self._obsidian = (info, from_obsidian)

    def check_environment(self) -> bool:
        self.step(2, "env_title")
        self.say("env_what")
        version = ".".join(str(n) for n in sys.version_info[:3])
        if not lib.python_ok():
            self.say("python_old", version=version)
            return False
        self.say("python_ok", version=version)
        self.say("git_ok" if lib.detect_git() else "git_missing")
        if not self.check_claude():
            return False
        return self.check_obsidian()

    def check_claude(self) -> bool:
        command = lib.detect_claude_command()
        folder = self.claude().is_dir()
        if command or folder:
            self.say("claude_ok", where=", ".join(filter(None, [command, "~/.claude" if folder else ""])))
            return True
        self.say("claude_missing")
        return self.asker.yes_no("continue_without_claude", self.t("claude_continue"), False)

    def check_obsidian(self) -> bool:
        info, language = self._obsidian
        if info.found:
            self.say("obsidian_ok", where=info.where)
            if language:
                self.say("obsidian_language", language=language)
            else:
                self.say("obsidian_language_unread")
            return True
        self.say("obsidian_missing")
        return self.asker.yes_no("continue_without_obsidian", self.t("obsidian_continue"), True)

    def choose_python(self) -> None:
        self.step(3, "py_title")
        suggested = lib.suggested_python()
        self.say("py_what", suggested=suggested)
        self.choices.python = self.asker.text("python_command", self.t("py_question"), suggested)

    def choose_vault(self) -> bool:
        self.step(4, "vault_title")
        self.say("vault_what")
        self.say("if_no", result=self.t("vault_no"))
        if not self.asker.yes_no("install_vault", self.t("vault_question"), True):
            self.say("vault_skipped_rest")
            return False
        default = self.home / "Documents" / "Mindgate-Vault"
        while True:
            answer = Path(self.asker.text("vault_path", self.t("vault_path_question"), str(default), once=True))
            path = (answer.expanduser() if answer.is_absolute() or str(answer).startswith("~") else self.home / answer)
            if self.accept_vault_folder(path):
                self.choices.vault = path
                return True

    def accept_vault_folder(self, path: Path) -> bool:
        if path.is_file():
            self.say("vault_not_dir", path=path)
            return False
        if not path.exists() or not any(path.iterdir()):
            return True
        language = lib.existing_vault_language(path)
        if language is None:
            self.say("vault_full", path=path)
            return False
        self.say("vault_existing", language=language, path=path)
        if language != self.choices.language:
            self.say("vault_language_mismatch", language=language)
            return False
        if self.asker.yes_no("reuse_vault", self.t("vault_reuse_question"), True):
            self.choices.reuse_vault = True
            return True
        return False

    def core_text(self) -> str:
        """The global instructions core of this install, filled."""
        master = next(f for f in self.vault_files() if f.source == lib.MASTER_COPY)
        return lib.fill(master.data.decode("utf-8"), self.values())

    def choose_instructions(self) -> None:
        self.step(5, "ins_title")
        self.say("ins_what")
        self.say("if_no", result=self.t("ins_no"))
        path = self.claude() / lib.CORE_NAME
        core = lib.summarize(self.core_text())
        if path.is_file():
            text = lib.decode(path.read_bytes())
            if lib.has_import(text) or lib.has_block(text):
                self.say("ins_already")
                self.choices.instructions = "sync"
                return
            mine = lib.summarize(text)
            self.say("ins_yours", size=mine["size"], lines=mine["lines"])
            self.say("ins_headings", headings="; ".join(mine["headings"]) or "-")
            self.say("ins_first_lines")
            for line in mine["first"]:
                self.out(f"    | {line[:100]}")
            self.say("ins_ours", size=core["size"], lines=core["lines"], headings="; ".join(core["headings"]))
            self.say("ins_options")
            self.say("ins_backup")
            options = ["import", "merge", "skip"]
            self.choices.instructions = self.asker.choose("global_instructions", self.t("ins_question"), options, "import")
        else:
            self.say("ins_ours", size=core["size"], lines=core["lines"], headings="; ".join(core["headings"]))
            self.say("ins_new_options")
            self.choices.instructions = self.asker.choose("global_instructions", self.t("ins_question"), ["write", "skip"],
                                                          "write", aliases={"import": "write", "merge": "write"})

    def read_settings(self) -> tuple:
        """(raw bytes or None, parsed dict); raises InstallerError for a broken file (nothing has been written)."""
        path = self.claude() / "settings.json"
        raw = path.read_bytes() if path.is_file() else None
        try:
            return raw, lib.parse_settings(raw)
        except (ValueError, UnicodeDecodeError) as error:
            raise lib.InstallerError(self.t("hooks_broken", error=f"{type(error).__name__}: {error}")) from None
        except TypeError:
            raise lib.InstallerError(self.t("hooks_not_object")) from None

    def choose_hooks(self) -> None:
        self.step(6, "hooks_title")
        self.say("hooks_what")
        self.say("if_no", result=self.t("hooks_no"))
        _, settings = self.read_settings()
        specs = lib.hook_specs(self.values(), lib.local_name("_system", self.names()), self.choices.language)
        present, offered = lib.split_present(settings, specs)
        descriptions = msg.HOOK_DESCRIPTIONS[self.choices.language]
        for spec in specs:
            self.say("hooks_item", id=spec.id, description=descriptions.get(spec.id, spec.command))
        self.choices.hooks_present = present
        if present:
            self.say("hooks_present", count=len(present))
        if not offered:
            return
        answer = self.asker.choose("hooks", self.t("hooks_question"), ["all", "none", "pick"], "all")
        if answer == "all":
            self.choices.hooks = offered
        elif answer == "pick":
            ids = self.asker.pick("hooks_pick", [s.id for s in offered],
                                  lambda i: self.t("hooks_pick_question", id=i), allowed=[s.id for s in present])
            self.choices.hooks = [s for s in offered if s.id in ids]

    def choose_skills_and_agents(self) -> None:
        self.step(7, "skills_title")
        self.say("skills_what")
        self.say("if_no", result=self.t("skills_no"))
        skills, agents = lib.skill_bundles(self.vault_files()), lib.agent_bundles(self.vault_files())
        self.say("skills_list", count=len(skills), names=", ".join(b.name for b in skills))
        self.say("agents_list", count=len(agents), names=", ".join(b.name for b in agents))
        if self.asker.yes_no("install_skills", self.t("skills_question"), True):
            self.choices.skills = self.resolve_names(skills, self.claude() / "skills", "skill")
        if self.asker.yes_no("install_agents", self.t("agents_question"), True):
            self.choices.agents = self.resolve_names(agents, self.claude() / "agents", "agent")

    def bundle_target(self, folder: Path, bundle: lib.Bundle, kind: str) -> Path:
        return folder / bundle.name if kind == "skill" else folder / f"{bundle.name}.md"

    def same_as_installed(self, folder: Path, bundle: lib.Bundle, kind: str) -> bool:
        main = ("SKILL.md",) if kind == "skill" else (f"{bundle.name}.md",)
        path = folder / bundle.name / "SKILL.md" if kind == "skill" else folder / main[0]
        return path.is_file() and path.read_bytes() == bundle.files[main]

    def resolve_names(self, bundles: list, folder: Path, kind: str) -> list:
        """Bundles to copy: a name already taken is skipped or renamed, as the person chooses; never overwritten."""
        final, same = [], []
        for bundle in bundles:
            if not self.bundle_target(folder, bundle, kind).exists():
                final.append(bundle)
                continue
            if self.same_as_installed(folder, bundle, kind):
                same.append(bundle.name)
                continue
            new_name = self.free_name(folder, bundle.name, kind)
            answer = self.asker.choose("name_conflict", self.t("conflict_question", kind=self.t(f"kind_{kind}"),
                                                               name=bundle.name, new_name=new_name), ["skip", "rename"], "skip")
            if answer == "rename":
                final.append(lib.rename_bundle(bundle, new_name, kind))
        if same:
            self.say("same_present", names=", ".join(same))
        return final

    def free_name(self, folder: Path, name: str, kind: str) -> str:
        candidate, n = f"mindgate-{name}", 2
        while self.bundle_target(folder, lib.Bundle(candidate, {}), kind).exists():
            candidate, n = f"mindgate-{name}-{n}", n + 1
        return candidate

    def choose_tasks(self) -> None:
        self.step(8, "tasks_title")
        self.say("tasks_what")
        self.say("task_daily")
        self.say("task_weekly")
        self.say("if_no", result=self.t("tasks_no"))
        config = self.config_choices()
        for task in lib.TASKS:
            if self.asker.yes_no(f"{task}_task", self.t("task_question", task=self.t(f"task_{task}_name")), True):
                target = self.task_folder(task)
                content = lib.task_content(task, self.choices.language, self.values())
                existing = target / "SKILL.md"
                if existing.is_file() and existing.read_bytes() == content:
                    continue
                if target.exists():
                    self.say("task_exists", path=target)
                    continue
                self.choices.tasks.append(task)
        if self.choices.tasks:
            self.say("tasks_app_note")
            config.scan_all_projects = self.asker.yes_no("scan_all_projects", self.t("scan_question"), False)
            config.git_push = self.asker.yes_no("git_push", self.t("push_question"), False)
        if "weekly" in self.choices.tasks:
            self.say("trending_what")
            config.weekly_trending = self.asker.yes_no("weekly_trending", self.t("trending_question"), False)
        self.choices.config = config

    def task_folder(self, task: str) -> Path:
        return self.claude() / "scheduled-tasks" / lib.mapped(self.names(), "tasks", task)

    def choose_optional_rules(self) -> None:
        self.step(9, "rules_title")
        self.say("rules_what")
        self.say("if_no", result=self.t("rules_no"))
        rules_file = next(f for f in self.vault_files() if f.source == ("rules", "general-rules.md"))
        rules = lib.optional_rules(rules_file.data.decode("utf-8"))
        offered = [r for r in rules if r.offered]
        for rule in rules:
            if rule.offered:
                self.say("rule_item", number=rule.number, title=rule.title)
            else:
                self.say("rule_needs_dashboard", number=rule.number)
        chosen = self.asker.pick("optional_rules", [r.number for r in offered],
                                 lambda n: self.t("rule_question", number=n), default=False)
        config = self.choices.config or self.config_choices()
        config.optional_rules = chosen
        if 9 in chosen:
            config.usage_limit = {"five_hour_percent": self.ask_percent("usage_limit_5h", "usage_5h_question", 93),
                                  "weekly_percent": self.ask_percent("usage_limit_week", "usage_week_question", 98)}
        if 17 in chosen:
            self.say("rule_fingerprint")
        self.choices.config = config
        self._vault_files = None    # the config inside the vault changed

    def ask_percent(self, key: str, question: str, default: int) -> int:
        while True:
            answer = self.asker.text(key, self.t(question), str(default), once=not self.asker.interactive)
            if answer.isdigit() and 1 <= int(answer) <= 100:
                return int(answer)
            self.say("percent_invalid")

    # ---------- plan ----------
    def build_plan(self) -> Plan:
        plan = Plan(record={"time": datetime.now().isoformat(timespec="seconds"), "language": self.choices.language,
                            "python": self.choices.python, "vault": None, "vault_created": False, "vault_files": 0,
                            "skills": [], "agents": [], "tasks": [], "changed": [], "created": []})
        if self.choices.vault is None:
            return plan
        plan.record["vault"] = str(self.choices.vault)
        self.plan_vault(plan)
        self.plan_instructions(plan)
        self.plan_settings(plan)
        self.plan_bundles(plan)
        self.plan_tasks(plan)
        return plan

    def backup_path(self, name: str) -> Path:
        folder = lib.mindgate_dir(self.home) / "backups" / self.stamp
        return lib.free_path(folder / name)

    def add_change(self, plan: Plan, path: Path, data: bytes, kind: str, **extra) -> None:
        """A new file or a backed-up change of an existing one; nothing when the content is already the same."""
        before = path.read_bytes() if path.is_file() else None
        if before == data:
            return
        if before is None:
            plan.actions.append(lib.Write(path, data))
            backup = None
        else:
            backup = self.backup_path(path.name)
            while any(isinstance(a, lib.Change) and a.backup == backup for a in plan.actions):
                backup = lib.free_path(backup.with_name(backup.name + "-x"))
            plan.actions.append(lib.Change(path, data, before, backup))
        plan.record["changed"].append({"path": str(path), "kind": kind, "created": before is None,
                                       "backup": str(backup) if backup else None, "sha256": lib.sha256(data), **extra})

    def plan_vault(self, plan: Plan) -> None:
        vault = self.choices.vault
        if self.choices.reuse_vault:
            path = lib.config_path(vault, self.choices.language)
            current = json.loads(path.read_text(encoding="utf-8"))
            new = lib.config_bytes(lib.apply_config(current, self.choices.config or self.config_choices()))
            self.add_change(plan, path, new, "config")
            return
        files = self.vault_files()
        plan.actions += [lib.Write(vault.joinpath(*f.target), f.data) for f in files]
        plan.vault_count = len(files)
        plan.record.update(vault_created=True, vault_files=len(files))

    def plan_instructions(self, plan: Plan) -> None:
        mode, core = self.choices.instructions, self.core_text()
        user_file = self.claude() / lib.CORE_NAME
        core_file = lib.mindgate_dir(self.home) / lib.CORE_NAME
        if mode == "skip":
            return
        if mode == "write":
            self.add_change(plan, user_file, core.encode("utf-8"), "instructions", mode="write")
            return
        text = lib.decode(user_file.read_bytes())
        if mode == "import" or (mode == "sync" and lib.has_import(text)):
            self.add_change(plan, core_file, core.encode("utf-8"), "core")
            if not lib.has_import(text):
                self.add_change(plan, user_file, lib.encode(lib.add_import(text)), "instructions", mode="import")
        elif mode == "merge":
            self.add_change(plan, user_file, lib.encode(lib.add_block(text, core)), "instructions", mode="merge")
        elif mode == "sync" and lib.has_block(text):
            self.add_change(plan, user_file, lib.encode(lib.replace_block(text, core)), "instructions", mode="merge")

    def plan_settings(self, plan: Plan) -> None:
        if not self.choices.hooks:
            return
        raw, settings = self.read_settings()
        new = lib.settings_bytes(lib.add_hooks(settings, self.choices.hooks))
        hooks = [{"event": s.event, "command": s.command} for s in self.choices.hooks]
        self.add_change(plan, self.claude() / "settings.json", new, "settings", hooks=hooks)

    def plan_bundles(self, plan: Plan) -> None:
        for kind, bundles, folder in (("skill", self.choices.skills, self.claude() / "skills"),
                                      ("agent", self.choices.agents, self.claude() / "agents")):
            for bundle in bundles:
                root = folder / bundle.name if kind == "skill" else folder
                plan.actions += [lib.Write(root.joinpath(*parts), data) for parts, data in sorted(bundle.files.items())]
                plan.record[f"{kind}s"].append(str(self.bundle_target(folder, bundle, kind)))

    def plan_tasks(self, plan: Plan) -> None:
        for task in self.choices.tasks:
            folder = self.task_folder(task)
            plan.actions.append(lib.Write(folder / "SKILL.md", lib.task_content(task, self.choices.language, self.values())))
            plan.record["tasks"].append(str(folder))

    def manifest_action(self, plan: Plan):
        path = lib.manifest_path(self.home)
        if path.is_file():
            before = path.read_bytes()
            data = lib.read_manifest(self.home)
            data["installs"].append(plan.record)
            return lib.Change(path, lib.manifest_bytes(data), before, None)
        return lib.Write(path, lib.manifest_bytes({"tool": "mindgate", "version": 1, "installs": [plan.record]}))

    # ---------- summary and writing ----------
    def show_summary(self, plan: Plan) -> None:
        """Every file that will be written. Vault files and skill folders are grouped; --dry-run lists each file."""
        self.step(10, "summary_title")
        self.say("summary_what")
        vault = self.choices.vault
        vault_writes = [a for a in plan.actions if isinstance(a, lib.Write) and vault and lib.inside(a.path, vault)
                        and not self.choices.reuse_vault]
        if vault_writes:
            self.show_vault_writes(vault, vault_writes)
        in_vault = {id(a) for a in vault_writes}
        self.show_other_actions([a for a in plan.actions if id(a) not in in_vault])

    def show_vault_writes(self, vault: Path, writes: list) -> None:
        self.say("summary_vault", count=len(writes), path=vault)
        folders: dict = {}
        for a in writes:
            parts = a.path.relative_to(vault).parts
            folders[parts[0] if len(parts) > 1 else "."] = folders.get(parts[0] if len(parts) > 1 else ".", 0) + 1
        for folder, count in sorted(folders.items()):
            self.say("summary_vault_folder", folder=folder, count=count)
        if self.dry_run:
            for a in writes:
                self.out(f"           {a.path}")
        else:
            self.say("summary_full_list")

    def show_other_actions(self, actions: list) -> None:
        skills, shown = self.claude() / "skills", set()
        for action in actions:
            if isinstance(action, lib.Change):
                self.say("summary_change", path=action.path)
                if action.backup:
                    self.say("summary_backup", path=action.backup)
            elif self.dry_run or not lib.inside(action.path, skills):
                self.say("summary_new", path=action.path)
            else:
                folder = skills / action.path.relative_to(skills).parts[0]
                if folder not in shown:
                    shown.add(folder)
                    count = sum(1 for a in actions if isinstance(a, lib.Write) and lib.inside(a.path, folder))
                    self.say("summary_new_folder", path=folder, sep=os.sep, count=count)

    def summarize_and_write(self) -> int:
        plan = self.build_plan()
        if not plan.actions:
            self.step(10, "summary_title")
            self.say("summary_nothing")
            return 0
        plan.actions.append(self.manifest_action(plan))
        self.show_summary(plan)
        if self.dry_run:
            self.say("dry_run_done")
            return 0
        if not self.asker.yes_no("confirm", self.t("confirm_question"), False):
            self.say("cancelled")
            return 0
        return self.write(plan)

    def write(self, plan: Plan) -> int:
        self.step(11, "summary_title")
        self.say("writing")
        manifest = plan.actions.pop()
        try:
            written = lib.execute(plan.actions)
        except (OSError, lib.InstallerError) as error:
            plan.record["incomplete"] = True
            self.save_partial_manifest(plan)
            self.say("write_failed", error=error, manifest=lib.manifest_path(self.home))
            return 1
        lib.execute([manifest])
        self.say("done", count=len(written) + 1)
        self.say("done_manifest", path=lib.manifest_path(self.home))
        self.say("done_vault", path=self.choices.vault)
        self.say("done_next")
        self.say("done_uninstall", py=self.choices.python)
        return 0

    def save_partial_manifest(self, plan: Plan) -> None:
        try:
            lib.execute([self.manifest_action(plan)])
        except (OSError, lib.InstallerError, ValueError):
            pass   # the error above is already reported; the partial list cannot be saved either


def parse_args(argv: list | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Install Mindgate (a second-brain vault for Claude Code)")
    p.add_argument("--dry-run", action="store_true", help="only list what would be written")
    p.add_argument("--answers", help="JSON file with an answer for every question (tests, unattended runs)")
    p.add_argument("--home", help="home folder that holds .claude (default: your home folder)")
    return p.parse_args(argv)


def main(argv: list | None = None, output=print) -> int:
    args = parse_args(argv)
    home = Path(args.home).expanduser().resolve() if args.home else Path.home()
    try:
        asker = lib.make_asker(args.answers, home, output)
        return Installer(home, asker, args.dry_run, output).run()
    except lib.InstallerError as error:
        output(str(error))
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
