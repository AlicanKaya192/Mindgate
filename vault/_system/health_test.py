"""health.py tests: duplicate pending numbers, closing without evidence, the Learned line in the log, note fields,
problem history, regression markers, the monotonic baseline, the folders left out of the note scan, skill and agent
links (installed copies count) and the pre-commit check without git.

Every test works in a new temporary folder under _system/output/test_health/; the real vault is never touched and
nothing is deleted.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
import health  # noqa: E402
from common import name  # noqa: E402

TEST_DIR = common.OUTPUT / "test_health"
PENDING = f"{name('inbox')}/{name('pending.md')}"


class HealthTest(unittest.TestCase):
    def setUp(self):
        TEST_DIR.mkdir(parents=True, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(dir=TEST_DIR))
        self.old = health.VAULT, health.CLAUDE
        health.VAULT = self.root
        health.CLAUDE = self.root / "home" / ".claude"

    def tearDown(self):
        health.VAULT, health.CLAUDE = self.old

    def write(self, relative: str, text: str) -> None:
        (self.root / relative).parent.mkdir(parents=True, exist_ok=True)
        (self.root / relative).write_text(text, encoding="utf-8")

    def test_duplicate_number_is_an_error(self):
        self.write(PENDING, "## Open\n- [ ] P-001 | question | 2026-10-14 | a\n- [ ] P-001 | approval | 2026-10-14 | b\n")
        self.assertEqual(health.pending().status, "error")

    def test_turkish_prefix_is_read_too(self):
        self.write(PENDING, "- [ ] B-001 | question | 2026-10-14 | a\n- [ ] B-001 | approval | 2026-10-14 | b\n")
        self.assertEqual(health.pending().status, "error")

    def test_closing_without_evidence_warns_but_not_an_old_closing(self):
        self.write(PENDING,
                   "- [x] P-002 | question | 2026-10-14 | a | ✔ 2026-10-15 (yes)\n"
                   "- [x] P-003 | question | 2026-10-01 | b | ✔ 2026-10-02 (before the rule)\n"
                   "- [x] P-004 | question | 2026-10-14 | c | ✔ 2026-10-15 (yes · evidence: commit abc)\n")
        result = health.pending()
        self.assertEqual(result.status, "warning")
        self.assertIn("P-002", result.details)
        self.assertNotIn("P-003", result.details)
        self.assertNotIn("P-004", result.details)

    def test_on_hold_is_not_counted_as_old(self):
        self.write(PENDING, "- [ ] P-005 | on-hold | 2026-01-01 | later | ⏸\n")
        self.assertEqual(health.pending().status, "ok")

    def test_log_learned_line(self):
        self.write("log.md", "## [2026-10-14] progress | work\n- done\n\n## [2026-10-14] progress | work2\n- Learned: none\n"
                             "## [2026-10-13] progress | old\n- before the rule\n")
        result = health.log_check()
        self.assertEqual(result.status, "warning")
        self.assertIn("1 entries without", result.summary)

    def test_log_and_pending_archives_are_not_size_checked(self):
        large = "- a\n" * (health.LINE_LIMIT + 1)
        self.write(f"{name('archive')}/{name('log')}/log-2026-10.md", large)
        self.write(f"{name('archive')}/{name('pending')}/{name('pending')}-2026-10.md", large)
        self.write(f"{name('knowledge')}/large-note.md", large)
        result = health.file_sizes(health.read_notes())
        self.assertIn("large-note", result.details)
        self.assertNotIn("2026-10", result.details)

    def test_bad_log_heading_is_an_error(self):
        self.write("log.md", "## [2026-10-14] progress without a title\n")
        self.assertEqual(health.log_check().status, "error")

    def test_invalid_field_values(self):
        notes = {"n": (Path("knowledge/n.md"), {"type": "concept", "updated": "2026-10-14", "source_type": "guess"}, "")}
        self.assertEqual(health.fields(notes).status, "warning")
        notes = {"n": (Path("knowledge/n.md"), {"type": "concept", "updated": "2026-10-14", "privacy": "private"}, "")}
        self.assertEqual(health.fields(notes).status, "ok")

    def test_tried_solutions_in_problem_notes(self):
        # Rule #38: an old solution is not deleted; every attempt stays in the table with its result
        table = ("## Tried solutions\n| Date | Project | Tried | Result | Why |\n|---|---|---|---|---|\n"
                 "| 2026-10-14 | [[p]] | old solution | ✗ did not work | version changed |\n")
        worked = "| 2026-10-14 | [[p]] | new solution | ✔ worked | root cause fixed |\n"
        fm = lambda status, day="2026-10-14": {"type": "problem", "status": status, "updated": day}  # noqa: E731
        path = lambda n: Path(f"problems/{n}.md")  # noqa: E731
        notes = {
            "no-table": (path("no-table"), fm("solved"), "## Solution\n1. x\n"),
            "complete": (path("complete"), fm("solved"), "## Solution\n1. x\n" + table + worked),
            "attempted": (path("attempted"), fm("solved"), table.replace("Tried solutions", "Attempted solutions") + worked),
            "turkish": (path("turkish"), fm("solved"), table.replace("Tried solutions", "Denenen çözümler") + worked),
            "nothing-worked": (path("nothing-worked"), fm("solved"), "## Solution\n1. x\n" + table),
            "open": (path("open"), fm("open"), table),
            "before-rule": (path("before-rule"), fm("solved", "2026-10-10"), "## Solution\n1. x\n"),
            "concept": (Path("knowledge/concept.md"), {"type": "concept", "updated": "2026-10-14"}, ""),
        }
        result = health.problem_history(notes)
        self.assertEqual(result.status, "warning")
        for n in ("no-table", "nothing-worked"):
            self.assertIn(n + ":", result.details)
        for n in ("complete", "attempted", "turkish", "open", "before-rule", "concept"):
            self.assertNotIn(n + ":", result.details)

    def test_broken_link_in_a_fixed_archive_is_not_counted(self):
        # archive/log and archive/pending are kept by the write guard; a broken link there can never be fixed
        log_archive = Path(name("archive"), name("log"), "log-2026-10.md")
        pending_archive = Path(name("archive"), name("pending"), f"{name('pending')}-2026-10.md")
        for path in (log_archive, pending_archive):
            self.write(path.as_posix(), "archive\n")
        notes = {
            "log-2026-10": (log_archive, {}, "example [[link]]"),
            f"{name('pending')}-2026-10": (pending_archive, {}, "[[missing-1]]"),
            "live": (Path("knowledge/live.md"), {}, f"[[missing-2]] [[log-2026-10]] [[{name('pending')}-2026-10]]"),
        }
        broken, _ = health.link_checks(notes)
        self.assertEqual(broken.count, 1)
        self.assertIn("live → missing-2", broken.details)

    def test_regression_marker(self):
        # the string a fix left in the code is gone: the fix may have been reverted silently
        self.write("project/intact.py", "line = 1  # read with utf-8-sig\n")
        self.write("project/reverted.py", "line = 1\n")
        marker = lambda f: f"## Regression marker\n- `{self.root / 'project' / f}` → `read with utf-8-sig`\n"  # noqa: E731
        fm = {"type": "problem", "status": "solved", "updated": "2026-10-20"}
        notes = {
            "kept": (Path("problems/kept.md"), fm, marker("intact.py")),
            "reverted": (Path("problems/reverted.md"), fm, marker("reverted.py")),
            "moved": (Path("problems/moved.md"), fm, marker("missing.py")),
            "turkish": (Path("problems/turkish.md"), fm, marker("intact.py").replace("Regression marker", "Regresyon işaretçisi")),
            "no-marker": (Path("problems/no-marker.md"), fm, "## Solution\n1. x\n"),
        }
        result = health.regression_markers(notes)
        self.assertEqual(result.status, "warning")
        self.assertIn("reverted:", result.details)
        self.assertIn("moved:", result.details)
        self.assertNotIn("kept:", result.details)
        self.assertNotIn("turkish:", result.details)
        self.assertEqual(result.count, 2)
        self.assertEqual(health.regression_markers({"kept": notes["kept"]}).status, "ok")

    def test_monotonic_baseline(self):
        # tracked counts may only go down; going above the baseline is a regression
        result = lambda key, count: health.Result(key, key, "warning", "", count=count)  # noqa: E731
        self.assertEqual(health.baseline_file(), self.root / name("_system") / "health_baseline.json")
        self.assertEqual(health.baseline_check([result("orphans", 3)]).status, "warning")   # no baseline yet
        health.save_baseline([result("orphans", 3), result("broken_links", 2)])
        self.assertEqual(health.baseline_check([result("orphans", 3), result("broken_links", 2)]).status, "ok")
        higher = health.baseline_check([result("orphans", 5), result("broken_links", 1)])
        self.assertEqual(higher.status, "warning")
        self.assertIn("orphans: 3 → 5", higher.details)
        self.assertNotIn("broken_links", higher.details)
        # saving only lowers, never raises
        self.assertEqual(health.save_baseline([result("orphans", 5), result("broken_links", 1)]), {"orphans": 3, "broken_links": 1})

    def test_excluded_folders_are_not_notes(self):
        # .claude holds worktree copies of the vault; system folders and raw sources are not notes either
        for folder in (".claude/worktrees/x", name("_system"), name("_templates"), name("sources"), ".obsidian", ".trash"):
            self.write(f"{folder}/copy.md", "no frontmatter [[missing]]\n")
        self.write(f"{name('inbox')}/{name('sessions')}/record.md", "raw record\n")
        self.write(f"{name('knowledge')}/real.md", "---\ntype: concept\nupdated: 2026-10-14\n---\n")
        self.assertEqual(set(health.read_notes()), {"real"})

    def test_installer_copies_count_as_links(self):
        # the installer copies skills and agents into ~/.claude instead of linking them; a copy with the same content
        # or one listed in the installer manifest is fine, a missing or unknown different file is not
        skills, agents = f"{name('_system')}/{name('skills')}", f"{name('_system')}/{name('agents')}"
        for skill in ("same", "recorded", "changed", "missing"):
            self.write(f"{skills}/{skill}/SKILL.md", f"---\nname: {skill}\n---\n")
        self.write(f"{agents}/scout.md", "agent\n")
        self.write("home/.claude/skills/same/SKILL.md", "---\nname: same\n---\n")
        self.write("home/.claude/skills/recorded/SKILL.md", "edited after the install\n")
        self.write("home/.claude/skills/changed/SKILL.md", "someone else's skill\n")
        self.write("home/.claude/agents/scout.md", "agent\n")
        claude = self.root / "home" / ".claude"
        manifest = {"tool": "mindgate", "version": 1,
                    "installs": [{"skills": [str(claude / "skills" / "recorded")], "agents": [str(claude / "agents" / "scout.md")]}]}
        self.write("home/.claude/mindgate/install-manifest.json", json.dumps(manifest))
        result = health.links()
        self.assertEqual(result.status, "error")
        self.assertEqual(result.summary, "2 links missing or wrong")
        self.assertIn("changed", result.details)
        self.assertIn("missing", result.details)
        self.write("home/.claude/skills/changed/SKILL.md", "---\nname: changed\n---\n")
        self.write("home/.claude/skills/missing/SKILL.md", "---\nname: missing\n---\n")
        self.write("home/.claude/agents/scout.md", "edited agent, listed in the manifest\n")
        self.assertEqual(health.links().status, "ok")

    def test_precommit_without_git_is_only_info(self):
        result = health.precommit()
        self.assertEqual((result.status, result.summary), ("info", "git not set up; secret scan hook not installed"))
        (self.root / ".git" / "hooks").mkdir(parents=True)
        self.assertEqual(health.precommit().status, "warning")
        self.write(".git/hooks/pre-commit", f"#!/bin/sh\n# {health.HOOK_SIGNATURE}\n")
        self.assertEqual(health.precommit().status, "ok")

    def test_missing_files_do_not_crash(self):
        self.assertEqual(health.pending().status, "warning")
        self.assertEqual(health.log_check().status, "warning")
        self.assertEqual(health.handoff().status, "warning")
        self.assertEqual(health.index_missing({}).status, "ok")


if __name__ == "__main__":
    unittest.main(verbosity=1)
