"""common.py tests: retry when the atomic-write target is locked for a moment; name map; home folder."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

# Turkish install: `names` in config.json holds the `folders` and `files` tables of locales/tr/names.json
TR_NAMES = {
    "folders": {
        "inbox": "gelen", "sessions": "oturumlar", "projects": "projeler", "ideas": "fikirler", "councils": "kurullar",
        "problems": "sorunlar", "knowledge": "bilgi", "agents-log": "ajanlar", "research": "arastirmalar", "me": "ben",
        "rules": "kurallar", "drafts": "taslaklar", "archive": "arsiv", "sources": "kaynaklar", "decisions": "kararlar",
        "experiments": "deneyler", "_templates": "_sablonlar", "_system": "_sistem", "output": "cikti",
        "agents": "ajanlar", "skills": "beceriler", "instructions": "talimatlar", "council": "kurul",
        "round1": "tur1", "round2": "tur2",
    },
    "files": {
        "pending": "bekleyenler", "handoff": "devir", "general-rules": "genel-kurallar",
        "rule-violations": "kural-ihlalleri", "lesson-candidates": "ders-adaylari",
        "rejected-proposals": "reddedilen-oneriler", "project-proposals": "proje-onerileri", "profile": "profil",
        "environment": "ortam", "schema-details": "sema-ayrinti", "skills-registry": "beceriler",
        "config": "ayarlar", "task": "gorev", "decision": "karar", "report": "rapor", "blocked-sites": "engelli-siteler",
    },
}


TEST_DIR = common.OUTPUT / "test_common"   # fixed folder, files are overwritten, nothing is deleted (#22)


def turkish_names():
    """Loads TR_NAMES the way an install does: from a config.json file."""
    TEST_DIR.mkdir(parents=True, exist_ok=True)
    config = TEST_DIR / "config.json"
    config.write_text(json.dumps({"language": "tr", "names": TR_NAMES}), encoding="utf-8")
    settings, error = common.load_config(config)
    assert not error, error
    return common.load_names(settings)


class ReplaceTest(unittest.TestCase):
    def setUp(self):
        common.OUTPUT.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=common.OUTPUT)
        self.target = Path(self.temporary.name) / "log.md"

    def tearDown(self):
        self.temporary.cleanup()

    def test_retries_while_target_is_locked(self):
        real = common.os.replace
        errors = [PermissionError(5, "Access denied"), PermissionError(5, "Access denied")]
        def fake(a, b):
            if errors:
                raise errors.pop(0)
            real(a, b)
        with mock.patch.object(common.os, "replace", side_effect=fake), mock.patch.object(common, "REPLACE_STEP_S", 0):
            common.atomic_write(self.target, "new\n")
        self.assertEqual(self.target.read_text(encoding="utf-8"), "new\n")

    def test_raises_if_lock_persists(self):
        with mock.patch.object(common.os, "replace", side_effect=PermissionError(5, "x")), \
             mock.patch.object(common, "REPLACE_STEP_S", 0), self.assertRaises(PermissionError):
            common.atomic_write(self.target, "new\n")


class NameMapTest(unittest.TestCase):
    def setUp(self):
        common.OUTPUT.mkdir(parents=True, exist_ok=True)

    def test_english_install_keeps_base_names(self):
        with mock.patch.object(common, "NAMES", {"folders": {}, "files": {}}):
            self.assertEqual(common.name("inbox"), "inbox")
            self.assertEqual(common.vault_path("inbox", "pending.md"), common.VAULT / "inbox" / "pending.md")

    def test_turkish_install_gives_turkish_paths(self):
        with mock.patch.object(common, "NAMES", turkish_names()):
            self.assertEqual(common.vault_path("inbox", "pending.md"), common.VAULT / "gelen" / "bekleyenler.md")
            self.assertEqual(common.vault_path("_system", "output"), common.VAULT / "_sistem" / "cikti")
            self.assertEqual(common.vault_path("archive/handoff"), common.VAULT / "arsiv" / "devir")
            self.assertEqual(common.vault_path("rules", "general-rules.md"), common.VAULT / "kurallar" / "genel-kurallar.md")
            self.assertEqual(common.name("handoff"), "devir")              # wiki link target without extension
            self.assertEqual(common.name("log.md"), "log.md")              # no mapping: the key itself
            self.assertEqual(common.name("index.md"), "index.md")
            self.assertEqual(common.name("log-2026-09.md"), "log-2026-09.md")
            self.assertEqual(common.name(".git"), ".git")

    def test_missing_and_broken_config_fall_back_to_base_names(self):
        TEST_DIR.mkdir(parents=True, exist_ok=True)
        settings, error = common.load_config(TEST_DIR / "missing.json")
        self.assertEqual((settings, error), ({}, ""))
        broken = TEST_DIR / "broken.json"
        broken.write_text("{broken", encoding="utf-8")
        settings, error = common.load_config(broken)
        self.assertEqual(settings, {})
        self.assertIn("broken.json", error)
        self.assertEqual(common.load_names(settings), {"folders": {}, "files": {}})

    def test_shipped_config_is_english_with_empty_names(self):
        settings, error = common.load_config()
        self.assertEqual(error, "")
        self.assertEqual(settings["language"], "en")
        self.assertFalse(any(common.load_names(settings).values()))


class HomeFolderTest(unittest.TestCase):
    """Tests run with a fake home (HOME/USERPROFILE); Path.home() must follow those variables."""

    def test_path_home_follows_environment(self):
        fake_home = TEST_DIR / "home"
        fake_home.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ, HOME=str(fake_home), USERPROFILE=str(fake_home))
        out = subprocess.run([sys.executable, "-I", "-c", "from pathlib import Path; print(Path.home())"],
                             capture_output=True, text=True, env=env, stdin=subprocess.DEVNULL, check=True).stdout
        self.assertEqual(Path(out.strip()).resolve(), fake_home.resolve())

    def test_current_run_uses_environment_home(self):
        expected = os.environ.get("USERPROFILE" if os.name == "nt" else "HOME")
        if expected:
            self.assertEqual(Path.home().resolve(), Path(expected).resolve())


if __name__ == "__main__":
    unittest.main()
