"""Instruction coverage test: while the instruction files are kept short, no rule and no pointer may get lost.

Checks:
- Every rule in `general-rules.md` (the optional rules too) is in the session-start summary (SessionStart hook).
- The red-line rules and the working principles appear in the global core with their numbers.
- The skills and `<vault>/…` paths shown in the core and in the short schema really exist.
- The sections the short schema calls "details" exist in `schema-details.md`.
- Size limits ("keep CLAUDE.md short"): core ≤ 10,000 characters and ≤ 130 lines, short schema ≤ 12,000 characters.
"""
import importlib.util
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import VAULT, vault_path  # noqa: E402

SYSTEM = vault_path("_system")
CORE = vault_path("_system", "instructions") / "global-CLAUDE.md"
DETAILS = vault_path("_system", "instructions", "schema-details.md")
SCHEMA = VAULT / "CLAUDE.md"
RULES = vault_path("rules", "general-rules.md")
RED_LINES = {3, 13, 14, 17, 18, 19, 20, 22, 27, 32, 33, 35}
WORKING_PRINCIPLES = {12, 15, 23, 24, 25, 26, 30, 34, 36, 37, 38}
CORE_LIMIT, CORE_LINES, SCHEMA_LIMIT = 10_000, 130, 12_000
SKILL = re.compile(r"`/?([a-z][a-z0-9]*-[a-z0-9-]+|(?<=`/)[a-z]+)`")   # such as `/idea`, `task-writing`
NOT_SKILLS = {"clear", "compact", "adr-001", "self-learning", "oz-ogrenme"}  # command, naming example, log label
SCRIPTS = ("records.py", "search.py", "health.py", "cost.py", "install_instructions.py")
# Written by other parts of the translation; until they exist their check is skipped, not passed
OTHER_PARTS = {"health.py"}
SESSION_LOG = importlib.util.find_spec("session_log") is not None


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def rule_numbers() -> set[int]:
    """Every rule row of the file: the main table and the optional rules section."""
    return {int(m) for m in re.findall(r"^\|\s*(\d+)\s*\|", read(RULES), re.M)}


def numbers_in(text: str) -> set[int]:
    return {int(n) for n in re.findall(r"#(\d+)", text)}


class InstructionCoverageTest(unittest.TestCase):
    @unittest.skipUnless(SESSION_LOG, "session_log.py (session-start summary) is not written yet")
    def test_every_rule_is_in_the_session_start_summary(self):
        import session_log
        missing = rule_numbers() - numbers_in(session_log.rule_summary())
        self.assertFalse(missing, f"rules missing from the session-start summary: {sorted(missing)}")

    def test_optional_rules_are_counted(self):
        text = read(RULES)
        self.assertRegex(text, r"(?m)^## (Optional rules|İsteğe bağlı kurallar)\s*$")
        optional = re.split(r"(?m)^## (?:Optional rules|İsteğe bağlı kurallar)\s*$", text)[1]
        optional_numbers = {int(m) for m in re.findall(r"^\|\s*(\d+)\s*\|", optional, re.M)}
        self.assertTrue(optional_numbers, "no rule row in the optional rules section")
        self.assertLessEqual(optional_numbers, rule_numbers())

    def test_red_lines_and_principles_are_in_the_core(self):
        missing = (RED_LINES | WORKING_PRINCIPLES) - numbers_in(read(CORE))
        self.assertFalse(missing, f"rules not in the core: {sorted(missing)}")

    def test_red_lines_and_principles_are_rules(self):
        self.assertLessEqual(RED_LINES | WORKING_PRINCIPLES, rule_numbers())

    def test_shown_skills_exist(self):
        skills = {d.name for d in vault_path("_system", "skills").iterdir() if (d / "SKILL.md").is_file()}
        agents = {p.stem for p in vault_path("_system", "agents").glob("*.md")}   # hyphenated agent names such as `red-team`
        for path in (CORE, SCHEMA):
            missing = sorted(set(SKILL.findall(read(path))) - skills - agents - NOT_SKILLS)
            self.assertFalse(missing, f"{path.name}: skill does not exist: {missing}")

    def test_shown_vault_paths_exist(self):
        for path in (CORE, SCHEMA):
            for relative in re.findall(r"`<vault>/([^`\s]+?\.(?:md|py))", read(path)):
                self.assertTrue((VAULT / relative).is_file(), f"{path.name}: path does not exist: {relative}")
        for path in (DETAILS, CORE):
            self.assertTrue(path.is_file(), path)
        pending = []
        for script in SCRIPTS:
            if (SYSTEM / script).is_file():
                continue
            self.assertIn(script, OTHER_PARTS, f"_system/{script} does not exist")
            pending.append(script)
        if pending:
            self.skipTest(f"written by another part, not yet present: {', '.join(pending)}")

    def test_detail_sections_exist(self):
        details = read(DETAILS)
        for section in ("7.1", "7.2", "7.3", "7.4", "7.5", "7.6", "7.7", "7.8", "7.9", "7.10", "7.11", "10.1", "10.2"):
            self.assertRegex(details, rf"(?m)^#+ {re.escape(section)}\b", f"§{section} missing from schema-details.md")

    def test_size_limits(self):
        core = read(CORE)
        self.assertLessEqual(len(core), CORE_LIMIT)
        self.assertLessEqual(len(core.splitlines()), CORE_LINES)
        self.assertLessEqual(len(read(SCHEMA)), SCHEMA_LIMIT)


if __name__ == "__main__":
    unittest.main()
