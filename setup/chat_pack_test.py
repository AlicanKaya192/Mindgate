"""Tests of the chat app pack builder (chat_pack.py).

Every build goes to a new folder under `.yerel/k6/runs/` of the repository (or the folder named by the
MINDGATE_TEST_RUNS environment variable). Nothing is deleted: the run folders stay.

Run (from setup/): py -3 -I -B chat_pack_test.py -v
"""
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import chat_pack  # noqa: E402
import installer_lib as lib  # noqa: E402

REPO = HERE.parent
RUNS = Path(os.environ.get("MINDGATE_TEST_RUNS") or REPO / ".yerel" / "k6" / "runs")
BLOCKLIST = REPO / ".yerel" / "yasak-liste.txt"
INSTALL_PLACEHOLDER = re.compile(r"\{\{(VAULT|PY|HOME|LANG|USER)\}\}")
LANGUAGES = ("en", "tr")


def new_folder(prefix: str) -> Path:
    RUNS.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=prefix, dir=RUNS))


def build(language: str) -> Path:
    out = new_folder(f"chat-pack-{language}-")
    chat_pack.build(language, out)
    return out


class InstructionTexts(unittest.TestCase):
    def test_short_and_long_texts_fit_their_limits(self):
        for language in LANGUAGES:
            with self.subTest(language=language):
                short = chat_pack.static_text(language, "instructions-short")
                long = chat_pack.static_text(language, "instructions-long")
                self.assertLessEqual(len(short), chat_pack.SHORT_LIMIT)
                self.assertLessEqual(len(long), chat_pack.LONG_LIMIT)
                self.assertGreater(len(long), len(short))

    def test_every_text_starts_with_the_no_gates_line(self):
        for language in LANGUAGES:
            for stem in chat_pack.STATIC_FILES:
                with self.subTest(language=language, file=stem):
                    lines = chat_pack.static_text(language, stem).splitlines()
                    first_text = next(line for line in lines if line.strip() and not line.startswith("#"))
                    self.assertIn(chat_pack.NO_GATES_LINE[language], first_text)


class Build(unittest.TestCase):
    def test_writes_every_file_under_its_local_name(self):
        for language in LANGUAGES:
            with self.subTest(language=language):
                out = build(language)
                names = lib.load_names(language)
                expected = {chat_pack.output_name(stem, suffix, names) for stem, suffix in chat_pack.OUTPUTS}
                self.assertEqual({p.name for p in out.iterdir()}, expected)

    def test_turkish_pack_has_turkish_file_names(self):
        names = {p.name for p in build("tr").iterdir()}
        self.assertIn("kurallar.md", names)
        self.assertIn("talimat-kisa.txt", names)

    def test_knowledge_files_hold_the_vault_sources_of_the_language(self):
        out = build("tr")
        rules = (out / "kurallar.md").read_text(encoding="utf-8")
        self.assertIn("Sorun çözüm geçmişi", rules)
        templates = (out / "sablonlar.md").read_text(encoding="utf-8")
        for template in sorted((lib.VAULT_SOURCE / "_templates").glob("*.md")):
            local = lib.translate_parts(("_templates", template.name), lib.load_names("tr"))[-1]
            self.assertIn(f"## {local}", templates)

    def test_no_install_placeholder_is_left(self):
        for language in LANGUAGES:
            with self.subTest(language=language):
                for path in build(language).iterdir():
                    self.assertIsNone(INSTALL_PLACEHOLDER.search(path.read_text(encoding="utf-8")), path.name)

    def test_built_files_pass_the_secret_scan(self):
        for language in LANGUAGES:
            with self.subTest(language=language):
                for path in build(language).iterdir():
                    for line in path.read_text(encoding="utf-8").splitlines():
                        self.assertEqual(chat_pack.secret_scan.scan_line(line), [], path.name)

    @unittest.skipUnless(BLOCKLIST.is_file(), "the personal blocklist exists only on the maintainer's computer")
    def test_built_files_hold_no_personal_word(self):
        lines = BLOCKLIST.read_text(encoding="utf-8").splitlines()
        patterns = [re.compile(l.strip(), re.I) for l in lines if l.strip() and not l.strip().startswith("#")]
        for language in LANGUAGES:
            for path in build(language).iterdir():
                text = path.read_text(encoding="utf-8")
                for pattern in patterns:
                    with self.subTest(language=language, file=path.name, pattern=pattern.pattern):
                        self.assertIsNone(pattern.search(text))


class Refusals(unittest.TestCase):
    def test_refuses_a_folder_that_is_not_empty(self):
        out = new_folder("chat-pack-full-")
        (out / "mine.txt").write_text("my own file", encoding="utf-8")
        with self.assertRaises(lib.InstallerError):
            chat_pack.build("en", out)
        self.assertEqual([p.name for p in out.iterdir()], ["mine.txt"])

    def test_refuses_to_write_anything_when_a_secret_is_found(self):
        out = new_folder("chat-pack-secret-") / "pack"
        leaked = "api_key = Zq8vLm2pRt5xWc9n"  # secret-scan: allow (test input)
        with mock.patch.object(chat_pack, "schema_text", return_value=leaked):
            with self.assertRaises(lib.InstallerError):
                chat_pack.build("en", out)
        self.assertFalse(out.exists())

    def test_unknown_language_is_refused(self):
        with self.assertRaises(lib.InstallerError):
            chat_pack.build("xx", new_folder("chat-pack-xx-"))


if __name__ == "__main__":
    unittest.main()
