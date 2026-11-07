"""Tests of the Mindgate installer and uninstaller.

Every run uses a fake home and a fake vault place under `.yerel/k6/runs/` of the repository (or the folder named by
the MINDGATE_TEST_RUNS environment variable); the installer is always called with --home. Obsidian, the `claude`
command, git and the system language are mocked, so no real setting is read. Nothing is deleted: the run folders stay.

Run (from setup/): py -3 -I -B installer_test.py -v
"""
import contextlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import antigravity as ag  # noqa: E402
import codex  # noqa: E402
import gemini  # noqa: E402
import install  # noqa: E402
import installer_lib as lib  # noqa: E402
import installer_messages as msg  # noqa: E402
import uninstall  # noqa: E402

REPO = HERE.parent
RUNS = Path(os.environ.get("MINDGATE_TEST_RUNS") or REPO / ".yerel" / "k6" / "runs")
BLOCKLIST = REPO / ".yerel" / "yasak-liste.txt"
NEW_FILES = ["install.py", "uninstall.py", "installer_lib.py", "installer_messages.py", "installer_test.py",
             "answers.example.json", "antigravity.py", "antigravity/hooks.template.json", "codex.py",
             "codex/hooks.template.json", "gemini.py", "gemini/hooks.template.json"]
PLACEHOLDER = re.compile(r"\{\{(VAULT|PY|HOME|LANG|USER)\}\}")
ANY_PLACEHOLDER = re.compile(r"\{\{[^{}\n]*\}\}")
USER_HOOKS = {"hooks": {
    "PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "echo own-pre"}]}],
    "Stop": [{"hooks": [{"type": "command", "command": "echo own-stop"}]}],
    "Notification": [{"hooks": [{"type": "command", "command": "echo own-note"}]}]},
    "theme": "dark"}
USER_CLAUDE = "# My own rules\r\n\r\n- Keep answers short.\r\n- Kısa yaz.\r\n".encode("utf-8")


def base_answers(**overrides) -> dict:
    answers = {"language": "en", "continue_without_claude": True, "continue_without_obsidian": True,
               "python_command": "py -3", "install_vault": True, "vault_path": "", "reuse_vault": True,
               "global_instructions": "import", "hooks": "all", "hooks_pick": [], "install_skills": True,
               "install_agents": True, "name_conflict": "skip", "daily_task": True, "weekly_task": True,
               "scan_all_projects": False, "git_push": False, "weekly_trending": False, "optional_rules": [],
               "usage_limit_5h": 93, "usage_limit_week": 98, "assistants": [], "confirm": True}
    answers.update(overrides)
    return answers


def all_no() -> dict:
    return base_answers(continue_without_obsidian=False, continue_without_claude=False, install_vault=False,
                        reuse_vault=False, global_instructions="skip", hooks="none", install_skills=False,
                        install_agents=False, daily_task=False, weekly_task=False, confirm=False)


def files_under(folder: Path) -> list:
    return sorted(p for p in folder.rglob("*") if p.is_file()) if folder.exists() else []


def blocklist() -> list:
    lines = BLOCKLIST.read_text(encoding="utf-8").splitlines()
    return [re.compile(l.strip(), re.I) for l in lines if l.strip() and not l.strip().startswith("#")]


def source_placeholders() -> set:
    """Every {{...}} written on purpose in the shipped sources (template hints, regex examples)."""
    found = set()
    for root in (REPO / "vault", REPO / "locales", REPO / "setup" / "tasks"):
        for path in files_under(root):
            if path.suffix in (".md", ".json"):
                found |= set(ANY_PLACEHOLDER.findall(path.read_text(encoding="utf-8", errors="replace")))
    return found - {"{{" + p + "}}" for p in lib.PLACEHOLDERS}


class Run:
    """One fake home and one fake vault place, plus helpers to run the installer and uninstaller against them."""

    def __init__(self):
        RUNS.mkdir(parents=True, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(dir=RUNS, prefix="run-"))
        self.home = self.root / "home"
        self.home.mkdir()
        self.vault = self.root / "places" / "Mindgate-Vault"
        self.claude = self.home / ".claude"
        self.count = 0

    def answers_file(self, answers: dict) -> Path:
        self.count += 1
        path = self.root / f"answers-{self.count}.json"
        answers = {**answers, "vault_path": answers.get("vault_path") or str(self.vault)}
        path.write_text(json.dumps(answers, ensure_ascii=False), encoding="utf-8")
        return path

    def install(self, answers: dict, *flags: str, obsidian: bool = True, claude: bool = True) -> tuple:
        lines = []
        info = lib.ObsidianInfo(True, "mocked", None) if obsidian else lib.ObsidianInfo(False)
        with mock.patch.object(lib, "detect_obsidian", return_value=info), \
                mock.patch.object(lib, "detect_claude_command", return_value="claude" if claude else None), \
                mock.patch.object(lib, "detect_git", return_value="git"), \
                mock.patch.object(lib, "detect_os_language", return_value="en"), \
                mock.patch.object(lib, "machine_fingerprint", return_value="f" * 64):
            code = install.main(["--home", str(self.home), "--answers", str(self.answers_file(answers)), *flags],
                                output=lambda *a: lines.append(" ".join(str(x) for x in a)))
        return code, "\n".join(lines)

    def uninstall(self, confirm: bool = True, *flags: str) -> tuple:
        lines = []
        code = uninstall.main(["--home", str(self.home), "--answers", str(self.answers_file({"confirm": confirm})),
                               *flags], output=lambda *a: lines.append(" ".join(str(x) for x in a)))
        return code, "\n".join(lines)

    def user_files(self) -> None:
        self.claude.mkdir(parents=True)
        (self.claude / "settings.json").write_bytes(json.dumps(USER_HOOKS, indent=4).encode("utf-8"))
        (self.claude / "CLAUDE.md").write_bytes(USER_CLAUDE)

    def settings(self) -> dict:
        return json.loads((self.claude / "settings.json").read_text(encoding="utf-8"))

    def commands(self) -> list:
        return [h["command"] for groups in self.settings()["hooks"].values() for g in groups for h in g["hooks"]]

    def neutral(self, text: str) -> str:
        """The test's own folder paths replaced, so the blocklist only sees what the installer copied."""
        for path in (self.root, self.home, self.vault):
            for form in (str(path), path.as_posix(), json.dumps(str(path))[1:-1]):
                text = text.replace(form, "<TEST>")
        return text


class InstallUninstallTest(unittest.TestCase):
    def test_install_all_then_uninstall_gives_back_the_same_bytes(self):
        run = Run()
        run.user_files()
        settings_before = (run.claude / "settings.json").read_bytes()
        code, out = run.install(base_answers())
        self.assertEqual(code, 0, out)
        self.assertEqual(len(run.commands()), 3 + 12)
        self.assertTrue((run.claude / "CLAUDE.md").read_bytes().startswith(USER_CLAUDE))
        self.assertIn(lib.IMPORT_LINE, (run.claude / "CLAUDE.md").read_text(encoding="utf-8"))
        self.assertTrue((run.claude / "mindgate" / "CLAUDE.md").is_file())
        self.assertTrue((run.claude / "skills" / "idea" / "SKILL.md").is_file())
        backups = files_under(run.claude / "mindgate" / "backups")
        self.assertEqual(sorted(p.name for p in backups), ["CLAUDE.md", "settings.json"])

        code, out = run.uninstall()
        self.assertEqual(code, 0, out)
        self.assertEqual((run.claude / "settings.json").read_bytes(), settings_before)
        self.assertEqual((run.claude / "CLAUDE.md").read_bytes(), USER_CLAUDE)
        removed = list(run.claude.glob(lib.REMOVED_PREFIX + "*"))
        self.assertEqual(len(removed), 1, out)
        self.assertTrue((removed[0] / "skills" / "idea" / "SKILL.md").is_file())
        self.assertTrue((removed[0] / "agents" / "scout.md").is_file())
        self.assertTrue((removed[0] / "scheduled-tasks" / "daily" / "SKILL.md").is_file())
        self.assertTrue((removed[0] / "mindgate" / lib.MANIFEST_NAME).is_file())
        self.assertFalse((run.claude / "skills" / "idea").exists())
        self.assertTrue((run.vault / "rules" / "general-rules.md").is_file(), "the vault must not be touched")
        self.assertIn(str(run.vault), out)

    def test_uninstall_keeps_changes_made_after_the_install(self):
        run = Run()
        run.user_files()
        self.assertEqual(run.install(base_answers())[0], 0)
        settings = run.settings()
        settings["model"] = "opus"
        (run.claude / "settings.json").write_text(json.dumps(settings), encoding="utf-8")
        with open(run.claude / "CLAUDE.md", "ab") as f:
            f.write(b"- added later\n")
        code, out = run.uninstall()
        self.assertEqual(code, 0, out)
        self.assertEqual(sorted(run.commands()), ["echo own-note", "echo own-pre", "echo own-stop"])
        self.assertEqual(run.settings()["model"], "opus")
        text = (run.claude / "CLAUDE.md").read_bytes()
        self.assertNotIn(lib.IMPORT_TARGET.encode(), text)
        self.assertTrue(text.startswith(USER_CLAUDE) and text.endswith(b"- added later\n"))

    def test_no_to_every_question_writes_nothing(self):
        run = Run()
        code, out = run.install(all_no(), obsidian=False)
        self.assertEqual(code, 1, out)
        self.assertEqual(files_under(run.home), [])
        self.assertFalse(run.vault.exists())
        run2 = Run()
        code, out = run2.install(all_no())
        self.assertEqual(code, 0, out)
        self.assertEqual(files_under(run2.home), [])
        self.assertFalse(run2.vault.exists())

    def test_no_at_the_confirmation_writes_nothing(self):
        run = Run()
        code, out = run.install(base_answers(confirm=False))
        self.assertEqual(code, 0, out)
        self.assertIn(msg.text("en", "cancelled"), out)
        self.assertEqual(files_under(run.home), [])
        self.assertFalse(run.vault.exists())

    def test_dry_run_lists_and_writes_nothing(self):
        run = Run()
        run.user_files()
        before = {p: p.read_bytes() for p in files_under(run.home)}
        code, out = run.install(base_answers(), "--dry-run")
        self.assertEqual(code, 0, out)
        self.assertEqual({p: p.read_bytes() for p in files_under(run.home)}, before)
        self.assertFalse(run.vault.exists())
        self.assertIn(str(run.claude / "settings.json"), out)
        self.assertIn(str(run.vault / "inbox" / "pending.md"), out)
        self.assertIn(str(run.claude / "mindgate" / lib.MANIFEST_NAME), out)
        self.assertIn(msg.text("en", "dry_run_done"), out)
        code, out = run.uninstall(True, "--dry-run")
        self.assertIn(str(lib.manifest_path(run.home)), out)   # no manifest: nothing to do

    def test_uninstall_dry_run_changes_nothing(self):
        run = Run()
        run.user_files()
        self.assertEqual(run.install(base_answers())[0], 0)
        before = {p: p.read_bytes() for p in files_under(run.home)}
        code, out = run.uninstall(True, "--dry-run")
        self.assertEqual(code, 0, out)
        self.assertEqual({p: p.read_bytes() for p in files_under(run.home)}, before)
        self.assertIn(msg.text("en", "dry_run_done"), out)

    def test_second_install_adds_no_hook_or_import_line_twice(self):
        run = Run()
        run.user_files()
        self.assertEqual(run.install(base_answers())[0], 0)
        code, out = run.install(base_answers())
        self.assertEqual(code, 0, out)
        pairs = [(event, h["command"]) for event, groups in run.settings()["hooks"].items() for g in groups
                 for h in g["hooks"]]
        self.assertEqual(len(pairs), len(set(pairs)), "a hook was added twice")
        self.assertEqual(len(pairs), 15)
        self.assertEqual((run.claude / "CLAUDE.md").read_text(encoding="utf-8").count(lib.IMPORT_TARGET), 1)
        self.assertEqual(files_under(run.claude / "mindgate" / "backups").__len__(), 2)
        code, out = run.uninstall()
        self.assertEqual(code, 0, out)
        self.assertEqual((run.claude / "CLAUDE.md").read_bytes(), USER_CLAUDE)

    def test_broken_settings_json_stops_before_writing(self):
        run = Run()
        run.claude.mkdir(parents=True)
        (run.claude / "settings.json").write_bytes(b'{"hooks": {')
        code, out = run.install(base_answers())
        self.assertEqual(code, 2)
        self.assertIn("settings.json", out)
        self.assertIn("JSON", out)
        self.assertEqual(files_under(run.home), [run.claude / "settings.json"])
        self.assertEqual((run.claude / "settings.json").read_bytes(), b'{"hooks": {')
        self.assertFalse(run.vault.exists())

    def test_full_folder_is_never_written_over(self):
        run = Run()
        run.vault.mkdir(parents=True)
        (run.vault / "mine.md").write_text("my note", encoding="utf-8")
        code, out = run.install(base_answers())
        self.assertEqual(code, 2)
        self.assertIn(msg.text("en", "vault_full", path=run.vault), out)
        self.assertEqual(files_under(run.vault), [run.vault / "mine.md"])
        self.assertEqual(files_under(run.home), [])

    def test_existing_skill_is_skipped_or_renamed_never_overwritten(self):
        for choice in ("skip", "rename"):
            run = Run()
            own = run.claude / "skills" / "idea" / "SKILL.md"
            own.parent.mkdir(parents=True)
            own.write_text("---\nname: idea\n---\nmine\n", encoding="utf-8")
            code, out = run.install(base_answers(name_conflict=choice))
            self.assertEqual(code, 0, out)
            self.assertEqual(own.read_text(encoding="utf-8"), "---\nname: idea\n---\nmine\n")
            renamed = run.claude / "skills" / "mindgate-idea" / "SKILL.md"
            self.assertEqual(renamed.is_file(), choice == "rename")
            if choice == "rename":
                self.assertIn("name: mindgate-idea", renamed.read_text(encoding="utf-8"))

    def test_hooks_can_be_picked_one_by_one(self):
        run = Run()
        code, out = run.install(base_answers(hooks="pick", hooks_pick=["PreToolUse:command_guard", "Stop:context_check stop"],
                                             global_instructions="write"))
        self.assertEqual(code, 0, out)
        commands = run.commands()
        self.assertEqual(len(commands), 2)
        self.assertTrue(all("command_guard.py" in c or "context_check.py\" stop" in c for c in commands))
        self.assertFalse((run.claude / "CLAUDE.md").read_text(encoding="utf-8").count("{{"))

    def test_answers_against_the_real_home_are_refused(self):
        lines = []
        answers = Run().answers_file(base_answers())
        with mock.patch.object(lib, "real_homes", return_value=[Path.home()]):
            code = install.main(["--home", str(Path.home()), "--answers", str(answers)], output=lines.append)
        self.assertEqual(code, 2)
        self.assertIn("--home", "\n".join(lines))
        self.assertTrue(lib.is_real_home(Path.home()))


class LanguageTest(unittest.TestCase):
    def test_turkish_install(self):
        run = Run()
        code, out = run.install(base_answers(language="tr", optional_rules=[17]))
        self.assertEqual(code, 0, out)
        self.assertTrue((run.vault / "gelen" / "bekleyenler.md").is_file())
        rules = (run.vault / "kurallar" / "genel-kurallar.md").read_text(encoding="utf-8")
        self.assertIn("İsteğe bağlı kurallar", rules)
        self.assertTrue((run.vault / "_sistem" / "records.py").is_file())
        self.assertTrue((run.vault / "_sistem" / "beceriler" / "fikir" / "SKILL.md").is_file())
        skill = (run.claude / "skills" / "fikir" / "SKILL.md").read_text(encoding="utf-8")
        self.assertRegex(skill, r"(?m)^name: fikir$")
        self.assertTrue((run.claude / "agents" / "kasif.md").is_file())
        self.assertTrue((run.claude / "scheduled-tasks" / "gunluk" / "SKILL.md").is_file())
        commands = run.commands()
        self.assertEqual(len(commands), 12)
        self.assertTrue(all("/_sistem/" in c and "/_system/" not in c for c in commands))
        config = json.loads((run.vault / "_sistem" / "config.json").read_text(encoding="utf-8"))
        self.assertEqual(config["language"], "tr")
        self.assertEqual(config["names"]["folders"]["inbox"], "gelen")
        self.assertEqual(config["names"]["files"]["pending"], "bekleyenler")
        self.assertTrue(config["optional_rules"]["single_machine"])
        self.assertEqual(config["optional_rules"]["machine_sha256"], "f" * 64)   # mocked: no real computer name
        self.assertNotIn(config["optional_rules"]["machine_sha256"], out, "the fingerprint must not be shown")
        self.assertIn("## Kapananlar", (run.vault / "gelen" / "bekleyenler.md").read_text(encoding="utf-8"))
        self.assertIn(msg.text("tr", "vault_title"), out)

    def test_english_install(self):
        run = Run()
        code, out = run.install(base_answers(global_instructions="write"))
        self.assertEqual(code, 0, out)
        self.assertTrue((run.vault / "inbox" / "pending.md").is_file())
        self.assertTrue((run.claude / "skills" / "idea" / "SKILL.md").is_file())
        self.assertTrue((run.claude / "scheduled-tasks" / "weekly" / "SKILL.md").is_file())
        config = json.loads((run.vault / "_system" / "config.json").read_text(encoding="utf-8"))
        self.assertEqual((config["language"], config["python"], config["names"]), ("en", "py -3", {"folders": {}, "files": {}}))
        self.assertEqual(config["daily"], {"scan_all_projects": False, "git_push": False})
        self.assertEqual(config["weekly"], {"trending": False})
        app = json.loads((run.vault / ".obsidian" / "app.json").read_text(encoding="utf-8"))
        self.assertEqual(app["newFileFolderPath"], "inbox")
        self.assertTrue((run.claude / "CLAUDE.md").read_text(encoding="utf-8").startswith("# Global instructions"))

    def test_weekly_trending_question_is_saved_in_the_config(self):
        for answer in (False, True):
            run = Run()
            code, out = run.install(base_answers(weekly_trending=answer))
            self.assertEqual(code, 0, out)
            self.assertIn(msg.text("en", "trending_what"), out)
            config = json.loads((run.vault / "_system" / "config.json").read_text(encoding="utf-8"))
            self.assertIs(config["weekly"]["trending"], answer)

    def test_weekly_trending_is_not_asked_without_the_weekly_task(self):
        run = Run()
        answers = base_answers(weekly_task=False)
        del answers["weekly_trending"]          # a missing key would stop the installer if it were asked
        code, out = run.install(answers)
        self.assertEqual(code, 0, out)
        self.assertNotIn(msg.text("en", "trending_what"), out)
        config = json.loads((run.vault / "_system" / "config.json").read_text(encoding="utf-8"))
        self.assertIs(config["weekly"]["trending"], False)

    def test_missing_obsidian_is_explained_and_does_not_stop(self):
        run = Run()
        code, out = run.install(base_answers(), obsidian=False)
        self.assertEqual(code, 0, out)
        self.assertIn(msg.text("en", "obsidian_missing"), out)
        self.assertTrue((run.vault / "inbox" / "pending.md").is_file())

    def test_every_message_exists_in_both_languages(self):
        self.assertEqual(set(msg.MESSAGES["en"]), set(msg.MESSAGES["tr"]))
        self.assertEqual(set(msg.HOOK_DESCRIPTIONS["en"]), set(msg.HOOK_DESCRIPTIONS["tr"]))
        ids = {s.id for s in lib.hook_specs(lib.Values(Path("/v"), "py", Path("/h"), "en", "x"), "_system", "en")}
        self.assertEqual(ids, set(msg.HOOK_DESCRIPTIONS["en"]))


class InstalledContentTest(unittest.TestCase):
    """Leak and placeholder checks on everything an install writes, in both languages."""

    @classmethod
    def setUpClass(cls):
        cls.patterns = blocklist()
        cls.allowed = source_placeholders()
        cls.runs = {}
        for language in ("en", "tr"):
            run = Run()
            code, out = run.install(base_answers(language=language, optional_rules=[9, 17]))
            assert code == 0, out
            cls.runs[language] = run

    def installed(self, run: Run) -> list:
        return files_under(run.home) + files_under(run.vault)

    def test_blocklist_has_no_match_in_installed_files(self):
        for language, run in self.runs.items():
            hits = []
            for path in self.installed(run):
                text = run.neutral(path.read_text(encoding="utf-8", errors="replace"))
                hits += [f"{path.relative_to(run.root)} #{i}" for i, p in enumerate(self.patterns) if p.search(text)]
            self.assertEqual(hits, [], f"{language}: blocklist matches")

    def test_blocklist_has_no_match_in_the_new_setup_files(self):
        hits = [f"{name} #{i}" for name in NEW_FILES for i, p in enumerate(self.patterns)
                if p.search((HERE / name).read_text(encoding="utf-8"))]
        self.assertEqual(hits, [])

    def test_no_installer_placeholder_is_left(self):
        for language, run in self.runs.items():
            for path in self.installed(run):
                parts = path.parts
                if path.suffix == ".py" or "scripts" in parts or path.name == "global-CLAUDE.md":
                    continue
                text = path.read_text(encoding="utf-8", errors="replace")
                self.assertIsNone(PLACEHOLDER.search(text), f"{language}: {path}")
                left = set(ANY_PLACEHOLDER.findall(text)) - {"{{date}}", "{{title}}"} - self.allowed
                self.assertEqual(left, set(), f"{language}: {path}")

    def test_master_copy_keeps_its_placeholders_for_install_instructions(self):
        for language, run in self.runs.items():
            system = "_system" if language == "en" else "_sistem"
            folder = "instructions" if language == "en" else "talimatlar"
            master = (run.vault / system / folder / "global-CLAUDE.md").read_text(encoding="utf-8")
            self.assertIn("{{VAULT}}", master)
            core = (run.claude / "CLAUDE.md").read_text(encoding="utf-8")   # no own file: written directly
            self.assertIsNone(PLACEHOLDER.search(core))
            self.assertIn(run.vault.as_posix(), core)

    def notes(self, run: Run) -> dict:
        """Note name (lower-case stem) -> installed .md paths, skill folders left out (SKILL.md is in every one)."""
        found: dict = {}
        for path in files_under(run.vault):
            relative = path.relative_to(run.vault).parts
            if path.suffix == ".md" and relative[1:2] not in (("skills",), ("beceriler",)):
                found.setdefault(path.stem.lower(), []).append("/".join(relative))
        return found

    def test_no_two_notes_share_a_name(self):
        """Obsidian resolves [[name]] by file name; two notes with one name (once `research/research.md` and
        `_templates/research.md`) make the link ambiguous."""
        for language, run in self.runs.items():
            double = {stem: paths for stem, paths in self.notes(run).items() if len(paths) > 1}
            self.assertEqual(double, {}, language)

    def test_index_links_reach_installed_notes(self):
        for language, run in self.runs.items():
            links = re.findall(r"\[\[([^\]|#]+)", (run.vault / "index.md").read_text(encoding="utf-8"))
            self.assertTrue(links)
            self.assertEqual([l for l in links if l.lower() not in self.notes(run)], [], language)
        self.assertIn("[[research-notes]]", (self.runs["en"].vault / "index.md").read_text(encoding="utf-8"))
        self.assertTrue((self.runs["en"].vault / "research" / "research-notes.md").is_file())
        self.assertTrue((self.runs["tr"].vault / "arastirmalar" / "arastirmalar.md").is_file())

    def test_wiki_links_in_notes_reach_installed_files(self):
        """The same check as health.py's broken links: a fresh install starts with none."""
        code = re.compile(r"```.*?```|`[^`\n]*`", re.S)
        for language, run in self.runs.items():
            names = lib.load_names(language)
            skipped = {lib.local_name(key, names) for key in ("_templates", "_system", "sources")}
            existing = {p.stem for p in files_under(run.vault)} | {p.name for p in files_under(run.vault)}
            broken = []
            for path in files_under(run.vault):
                relative = path.relative_to(run.vault)
                if path.suffix != ".md" or relative.parts[0] in skipped:
                    continue
                body = code.sub("", path.read_text(encoding="utf-8"))
                broken += [f"{relative.as_posix()} → {target}" for target in re.findall(r"\[\[([^\]|#]+)", body)
                           if target.strip() not in existing]
            self.assertEqual(broken, [], language)

    def test_profile_page_is_an_empty_template(self):
        for language, (path, title) in {"en": (("me", "profile.md"), "# Profile"),
                                        "tr": (("ben", "profil.md"), "# Profil")}.items():
            text = (self.runs[language].vault / Path(*path)).read_text(encoding="utf-8")
            head, body = text.split("\n---\n", 1)
            self.assertIn("type: profile", head)
            lines = [l for l in body.splitlines() if l.strip()]
            self.assertEqual(lines[0], title)
            self.assertTrue(lines[1].startswith("> "))            # one description line
            self.assertTrue(all(l.startswith("## ") for l in lines[2:]), f"{language}: only headings: {lines[2:]}")
            self.assertGreaterEqual(len(lines[2:]), 3)
            self.assertIn(path[1][:-3], {stem for stem in self.notes(self.runs[language])})

    def test_search_exam_follows_the_install_language(self):
        exams = {}
        for language, run in self.runs.items():
            system = "_system" if language == "en" else "_sistem"
            exams[language] = json.loads((run.vault / system / "search_exam.json").read_text(encoding="utf-8"))["questions"]
            names = self.notes(run)
            expected = {stem for q in exams[language] for stem in q["expected"]}
            self.assertEqual([s for s in expected if s.lower() not in names], [], f"{language}: exam names missing notes")
        self.assertEqual({s for q in exams["tr"] for s in q["expected"]}, {"genel-kurallar", "CLAUDE"})
        self.assertEqual(len(exams["tr"]), len(exams["en"]))
        english = {q["question"] for q in exams["en"]}
        self.assertFalse([q["question"] for q in exams["tr"] if q["question"] in english])
        self.assertTrue(any(re.search(r"[çğıöşü]", q["question"]) for q in exams["tr"]))

    def test_usage_limit_is_saved(self):
        config = json.loads((self.runs["en"].vault / "_system" / "config.json").read_text(encoding="utf-8"))
        self.assertEqual(config["optional_rules"]["usage_limit"], {"five_hour_percent": 93, "weekly_percent": 98})
        self.assertEqual(config["optional_rules"]["enabled"], [9, 17])


class VaultTestsInInstalledVault(unittest.TestCase):
    """The installed vault runs its own test suite (fake home, installed language)."""

    def run_vault_tests(self, language: str) -> subprocess.CompletedProcess:
        run = Run()
        code, out = run.install(base_answers(language=language))
        self.assertEqual(code, 0, out)
        system = "_system" if language == "en" else "_sistem"
        env = {**os.environ, "HOME": str(run.home), "USERPROFILE": str(run.home), "PYTHONIOENCODING": "utf-8"}
        return subprocess.run([sys.executable, "-I", "-B", str(run.vault / system / "run_tests.py")],
                              capture_output=True, text=True, encoding="utf-8", errors="replace", env=env,
                              cwd=run.vault, stdin=subprocess.DEVNULL, timeout=900)

    def assert_all_pass(self, language: str) -> None:
        """Every test file of the installed vault passes, in the installed language; no tolerance."""
        result = self.run_vault_tests(language)
        lines = result.stdout.strip().splitlines()
        self.assertEqual(result.returncode, 0, result.stdout[-3000:] + result.stderr[-2000:])
        self.assertRegex(lines[-1], r"^(\d+)/\1 test files passed$")
        self.assertFalse([line for line in lines if line.startswith("FAILED ")], result.stdout[-3000:])
        print(f"\n[{language}] {lines[-1]}", file=sys.stderr)

    def test_english_vault_tests_pass(self):
        self.assert_all_pass("en")

    def test_turkish_vault_tests_pass(self):
        self.assert_all_pass("tr")


class ConsoleTest(unittest.TestCase):
    """The terminal flow: Enter takes every default; the confirmation defaults to no."""

    def run_console(self, language: str, confirm: str) -> tuple:
        run, lines = Run(), []
        def read(prompt: str) -> str:
            lines.append(prompt)
            if prompt.startswith("Language / Dil"):
                return language
            return confirm if prompt.startswith(msg.text(language, "confirm_question")) else ""
        info = lib.ObsidianInfo(True, "mocked", None)
        with mock.patch.object(lib, "detect_obsidian", return_value=info), \
                mock.patch.object(lib, "detect_claude_command", return_value="claude"), \
                mock.patch.object(lib, "detect_git", return_value="git"), \
                mock.patch.object(lib, "detect_os_language", return_value="en"):
            asker = lib.ConsoleAsker(lines.append, read)
            code = install.Installer(run.home, asker, False, lines.append).run()
        return run, code, "\n".join(lines)

    def test_enter_everywhere_writes_nothing(self):
        for language in ("en", "tr"):
            run, code, out = self.run_console(language, "")
            self.assertEqual(code, 0, out)
            self.assertIn(msg.text(language, "cancelled"), out)
            self.assertEqual(files_under(run.home), [])

    def test_defaults_and_yes_install_into_the_default_place(self):
        run, code, out = self.run_console("tr", "e")
        self.assertEqual(code, 0, out)
        self.assertTrue((run.home / "Documents" / "Mindgate-Vault" / "gelen" / "bekleyenler.md").is_file())
        self.assertTrue((run.claude / "skills" / "fikir" / "SKILL.md").is_file())
        self.assertEqual(len(run.commands()), 12)


USER_AGY_HOOKS = {"my-linter": {"PostToolUse": [{"matcher": "run_command", "hooks": [{"command": "./lint.sh"}]}]}}
USER_AGENTS_MD = "# My Antigravity rules\n\n- Keep diffs small.\n".encode("utf-8")


class AntigravityTest(unittest.TestCase):
    """Antigravity (experimental): what is written under ~/.gemini and that the uninstaller gives it all back."""

    def install(self, run: Run, **answers) -> str:
        code, out = run.install(base_answers(assistants=["antigravity"], **answers))
        self.assertEqual(code, 0, out)
        return out

    def hook_set(self, run: Run) -> dict:
        return json.loads(ag.hooks_path(run.home).read_text(encoding="utf-8"))[ag.HOOK_SET]

    def test_fresh_home_gets_guards_instructions_skills_and_agents(self):
        run = Run()
        self.install(run)
        commands = [h["command"] for g in self.hook_set(run)["PreToolUse"] for h in g["hooks"]]
        self.assertEqual(len(commands), 3)
        for script in ("command_guard.py", "write_guard.py", "site_guard.py"):
            self.assertTrue(any(script in c and c.endswith("--client antigravity") and run.vault.as_posix() in c
                                for c in commands), script)
        instructions = ag.instructions_path(run.home).read_bytes()
        self.assertLessEqual(len(instructions), ag.INSTRUCTIONS_LIMIT)
        self.assertIn(lib.BLOCK_START, lib.decode(instructions))
        self.assertTrue((ag.skills_dir(run.home) / "idea" / "SKILL.md").is_file())
        scout = (ag.agents_dir(run.home) / "scout.md").read_text(encoding="utf-8")
        self.assertIn("tools: [view_file, grep_search, find_by_name, list_dir, run_command", scout)
        self.assertNotIn("\neffort:", scout)
        self.assertRegex(scout, r"(?m)^model: (inherit|flash|pro)$")

    def test_users_own_files_come_back_byte_for_byte(self):
        run = Run()
        ag.hooks_path(run.home).parent.mkdir(parents=True)
        ag.hooks_path(run.home).write_bytes(json.dumps(USER_AGY_HOOKS, indent=4).encode("utf-8"))
        ag.instructions_path(run.home).write_bytes(USER_AGENTS_MD)
        hooks_before = ag.hooks_path(run.home).read_bytes()
        self.install(run)
        installed = json.loads(ag.hooks_path(run.home).read_text(encoding="utf-8"))
        self.assertEqual(installed["my-linter"], USER_AGY_HOOKS["my-linter"])
        self.assertTrue(ag.instructions_path(run.home).read_bytes().startswith(USER_AGENTS_MD))

        code, out = run.uninstall()
        self.assertEqual(code, 0, out)
        self.assertEqual(ag.hooks_path(run.home).read_bytes(), hooks_before)
        self.assertEqual(ag.instructions_path(run.home).read_bytes(), USER_AGENTS_MD)
        self.assertFalse((ag.skills_dir(run.home) / "idea").exists())
        self.assertFalse((ag.agents_dir(run.home) / "scout.md").exists())
        removed = list(run.claude.glob(lib.REMOVED_PREFIX + "*"))
        self.assertTrue((removed[0] / ".gemini" / "config" / "skills" / "idea" / "SKILL.md").is_file(), out)

    def test_files_mindgate_created_are_moved_away_on_uninstall(self):
        run = Run()
        self.install(run)
        code, out = run.uninstall()
        self.assertEqual(code, 0, out)
        self.assertFalse(ag.hooks_path(run.home).exists())
        self.assertFalse(ag.instructions_path(run.home).exists())

    def test_turkish_install_uses_the_turkish_script_folder_and_header(self):
        run = Run()
        self.install(run, language="tr")
        commands = [h["command"] for g in self.hook_set(run)["PreToolUse"] for h in g["hooks"]]
        self.assertTrue(all("/_sistem/" in c for c in commands), commands)
        self.assertIn(ag.HEADER["tr"], ag.instructions_path(run.home).read_text(encoding="utf-8"))

    def test_installed_command_guard_denies_deleting_the_home_folder(self):
        run = Run()
        self.install(run)
        command = next(h["command"] for g in self.hook_set(run)["PreToolUse"] for h in g["hooks"]
                       if "command_guard.py" in h["command"])
        payload = {"toolCall": {"name": "run_command", "args": {"CommandLine": "rm -rf ~", "Cwd": str(run.root)}},
                   "conversationId": "c1", "workspacePaths": [str(run.root)]}
        result = subprocess.run(command, shell=True, input=json.dumps(payload), capture_output=True, text=True,
                                encoding="utf-8")
        self.assertEqual(json.loads(result.stdout)["decision"], "deny", result.stderr)

    def test_not_chosen_writes_nothing_under_gemini(self):
        run = Run()
        code, out = run.install(base_answers())
        self.assertEqual(code, 0, out)
        self.assertFalse(ag.gemini_dir(run.home).exists())

    def test_broken_hooks_file_stops_before_writing(self):
        run = Run()
        ag.hooks_path(run.home).parent.mkdir(parents=True)
        ag.hooks_path(run.home).write_bytes(b"[1, 2]")
        code, out = run.install(base_answers(assistants=["antigravity"]))
        self.assertNotEqual(code, 0, out)
        self.assertEqual(ag.hooks_path(run.home).read_bytes(), b"[1, 2]")
        self.assertFalse(run.vault.exists())

    def test_instructions_over_the_size_limit_are_refused(self):
        with self.assertRaises(lib.InstallerError):
            ag.instructions_text("x" * ag.INSTRUCTIONS_LIMIT, "core", "en")

    def test_agent_with_an_unknown_tool_is_refused(self):
        bundle = lib.Bundle("odd", {("odd.md",): b"---\nname: odd\ntools: Read, Teleport\n---\nbody\n"})
        with self.assertRaises(lib.InstallerError):
            ag.convert_agent(bundle)


USER_CODEX_HOOKS = {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "echo mine"}]}]}}
USER_GEMINI_SETTINGS = {"ui": {"theme": "Dracula"}, "hooks": {"AfterTool": [{"hooks": [{"type": "command", "command": "echo x"}]}]}}


def run_hook(command: str, payload: dict) -> dict:
    result = subprocess.run(command, shell=True, input=json.dumps(payload), capture_output=True, text=True, encoding="utf-8")
    return json.loads(result.stdout) if result.stdout.strip() else {}


def hook_commands(path: Path, event: str) -> list:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [h["command"] for g in data["hooks"].get(event, []) for h in g["hooks"]]


class CodexTest(unittest.TestCase):
    def install(self, run: Run, **answers) -> str:
        code, out = run.install(base_answers(assistants=["codex"], **answers))
        self.assertEqual(code, 0, out)
        return out

    def test_fresh_home_gets_guards_instructions_skills_and_toml_agents(self):
        run = Run()
        self.install(run)
        commands = hook_commands(codex.hooks_path(run.home), "PreToolUse")
        self.assertEqual(len(commands), 2)
        self.assertTrue(all(c.endswith("--client codex") for c in commands), commands)
        self.assertLessEqual(len(codex.instructions_path(run.home).read_bytes()), codex.INSTRUCTIONS_LIMIT)
        self.assertTrue((codex.skills_dir(run.home) / "idea" / "SKILL.md").is_file())
        agents = sorted(codex.agents_dir(run.home).glob("*.toml"))
        self.assertGreater(len(agents), 5)
        for path in agents:
            with self.subTest(agent=path.name):
                data = tomllib.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(data["name"], path.stem)
                self.assertTrue(data["description"] and data["developer_instructions"].strip())

    def test_users_own_files_come_back_byte_for_byte(self):
        run = Run()
        codex.codex_dir(run.home).mkdir(parents=True)
        codex.hooks_path(run.home).write_bytes(json.dumps(USER_CODEX_HOOKS, indent=2).encode("utf-8"))
        codex.instructions_path(run.home).write_bytes(USER_AGENTS_MD)
        before = codex.hooks_path(run.home).read_bytes()
        self.install(run)
        self.assertIn("echo mine", hook_commands(codex.hooks_path(run.home), "PreToolUse"))
        code, out = run.uninstall()
        self.assertEqual(code, 0, out)
        self.assertEqual(codex.hooks_path(run.home).read_bytes(), before)
        self.assertEqual(codex.instructions_path(run.home).read_bytes(), USER_AGENTS_MD)
        self.assertFalse((codex.skills_dir(run.home) / "idea").exists())
        self.assertFalse(any(codex.agents_dir(run.home).glob("*.toml")))

    def test_second_install_adds_no_hook_twice(self):
        run = Run()
        self.install(run)
        self.install(run, reuse_vault=True)
        self.assertEqual(len(hook_commands(codex.hooks_path(run.home), "PreToolUse")), 2)

    def test_installed_guards_deny_home_deletion_and_log_writes(self):
        run = Run()
        self.install(run)
        command, write = hook_commands(codex.hooks_path(run.home), "PreToolUse")
        shell = {"session_id": "t1", "cwd": str(run.root), "hook_event_name": "PreToolUse", "tool_name": "Bash",
                 "tool_input": {"command": "rm -rf ~"}}
        self.assertEqual(run_hook(command, shell)["hookSpecificOutput"]["permissionDecision"], "deny")
        patch = f"*** Begin Patch\n*** Update File: {run.vault / 'log.md'}\n@@\n-a\n+b\n*** End Patch\n"
        edit = {**shell, "tool_name": "apply_patch", "tool_input": {"command": patch}}
        self.assertEqual(run_hook(write, edit)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_instructions_over_32_kib_are_refused(self):
        with self.assertRaises(lib.InstallerError):
            codex.instructions_text("x" * codex.INSTRUCTIONS_LIMIT, "core", "en")

    def test_agent_text_with_three_quotes_stays_valid_toml(self):
        three = "'" * 3
        text = f"---\nname: q\ndescription: Q\n---\nSay {three} and \"\"\" here.\n"
        data = tomllib.loads(lib.decode(codex.convert_agent(lib.Bundle("q", {("q.md",): text.encode()})).files[("q.toml",)]))
        self.assertIn(three, data["developer_instructions"])


class GeminiTest(unittest.TestCase):
    def install(self, run: Run, assistants: list, **answers) -> str:
        code, out = run.install(base_answers(assistants=assistants, **answers))
        self.assertEqual(code, 0, out)
        return out

    def test_fresh_home_gets_guards_instructions_skills_and_agents(self):
        run = Run()
        self.install(run, ["gemini"])
        commands = hook_commands(gemini.settings_path(run.home), "BeforeTool")
        self.assertEqual(len(commands), 3)
        self.assertTrue(all(c.endswith("--client gemini") for c in commands), commands)
        self.assertIn(gemini.HEADER["en"], gemini.instructions_path(run.home).read_text(encoding="utf-8"))
        self.assertTrue((codex.skills_dir(run.home) / "idea" / "SKILL.md").is_file())
        scout = (gemini.agents_dir(run.home) / "scout.md").read_text(encoding="utf-8")
        self.assertIn("tools: [read_file, read_many_files, grep_search, glob, list_directory, run_shell_command", scout)
        self.assertNotRegex(scout, r"(?m)^(model|effort|skills):")

    def test_other_settings_stay_and_come_back_byte_for_byte(self):
        run = Run()
        ag.gemini_dir(run.home).mkdir(parents=True)
        gemini.settings_path(run.home).write_bytes(json.dumps(USER_GEMINI_SETTINGS, indent=2).encode("utf-8"))
        before = gemini.settings_path(run.home).read_bytes()
        self.install(run, ["gemini"])
        installed = json.loads(gemini.settings_path(run.home).read_text(encoding="utf-8"))
        self.assertEqual(installed["ui"], USER_GEMINI_SETTINGS["ui"])
        self.assertEqual(installed["hooks"]["AfterTool"], USER_GEMINI_SETTINGS["hooks"]["AfterTool"])
        code, out = run.uninstall()
        self.assertEqual(code, 0, out)
        self.assertEqual(gemini.settings_path(run.home).read_bytes(), before)
        self.assertFalse(gemini.instructions_path(run.home).exists())

    def test_installed_guards_deny_what_claude_would_ask(self):
        run = Run()
        self.install(run, ["gemini"])
        command, _, site = hook_commands(gemini.settings_path(run.home), "BeforeTool")
        base = {"session_id": "t1", "cwd": str(run.root), "hook_event_name": "BeforeTool"}
        shell = {**base, "tool_name": "run_shell_command", "tool_input": {"command": "rm -rf ~/x"}}
        self.assertEqual(run_hook(command, shell)["decision"], "deny")
        fetch = {**base, "tool_name": "web_fetch", "tool_input": {"prompt": "Summarize https://docs.python.org/3/"}}
        self.assertEqual(run_hook(site, fetch)["decision"], "deny")

    def test_all_three_assistants_share_files_without_writing_twice(self):
        run = Run()
        self.install(run, ["antigravity", "gemini", "codex"])
        self.assertFalse(ag.instructions_path(run.home).exists(), "Antigravity reads the shared GEMINI.md")
        self.assertIn(gemini.SHARED_HEADER["en"], gemini.instructions_path(run.home).read_text(encoding="utf-8"))
        self.assertTrue((codex.skills_dir(run.home) / "idea" / "SKILL.md").is_file())
        self.assertTrue((ag.skills_dir(run.home) / "idea" / "SKILL.md").is_file())
        code, out = run.uninstall()
        self.assertEqual(code, 0, out)
        for path in (gemini.settings_path(run.home), codex.hooks_path(run.home), ag.hooks_path(run.home),
                     codex.skills_dir(run.home) / "idea"):
            self.assertFalse(path.exists(), path)


class CodeRulesTest(unittest.TestCase):
    def test_no_deleting_call_in_the_installer_code(self):
        deleting = re.compile(r"\b(os\.remove|os\.unlink|\.unlink\(|rmtree|os\.rmdir|\.rmdir\(|shutil\.move|send2trash)")
        for name in ("install.py", "uninstall.py", "installer_lib.py", "antigravity.py", "codex.py", "gemini.py"):
            self.assertIsNone(deleting.search((HERE / name).read_text(encoding="utf-8")), name)


if __name__ == "__main__":
    unittest.main()
