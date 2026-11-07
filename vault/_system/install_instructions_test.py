"""install_instructions.py tests: status, filling the placeholders, never overwriting an existing file.
Everything runs in temporary folders under _system/output/; the subprocess tests use a fake home folder."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import install_instructions as ii  # noqa: E402
from common import OUTPUT  # noqa: E402

SCRIPT = Path(__file__).resolve().parent / "install_instructions.py"
MASTER = "Vault: `{{VAULT}}`\r\nSearch: `{{PY}} -I {{VAULT}}/_system/search.py`\n"


class InstallInstructionsTest(unittest.TestCase):
    def setUp(self):
        OUTPUT.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=OUTPUT)
        root = Path(self.temporary.name)
        self.source, self.installed = root / "master.md", root / "home" / ".claude" / "CLAUDE.md"
        self.source.write_bytes(MASTER.encode("utf-8"))

    def tearDown(self):
        self.temporary.cleanup()

    def install(self, force_new: bool = True) -> str:
        return ii.install(self.source, self.installed, "/v", "python3", force_new=force_new)

    def test_installs_only_with_force_new_when_missing(self):
        self.assertEqual(ii.status(self.source, self.installed, "/v", "python3"), "not_installed")
        self.assertEqual(self.install(force_new=False), "needs_force_new")
        self.assertFalse(self.installed.exists())
        self.assertEqual(self.install(), "installed")
        self.assertEqual(ii.status(self.source, self.installed, "/v", "python3"), "same")

    def test_placeholders_are_filled_and_line_endings_kept(self):
        self.install()
        self.assertEqual(self.installed.read_bytes(), b"Vault: `/v`\r\nSearch: `python3 -I /v/_system/search.py`\n")
        self.assertEqual(ii.status(self.source, self.installed, "/v", "py -3"), "different")

    def test_existing_file_is_never_overwritten(self):
        self.installed.parent.mkdir(parents=True)
        own = "my own instructions\r\n".encode("utf-8")
        self.installed.write_bytes(own)
        self.assertEqual(ii.status(self.source, self.installed, "/v", "python3"), "different")
        self.assertEqual(self.install(force_new=True), "existing")
        self.assertEqual(self.installed.read_bytes(), own)

    def test_same_copy_is_left_alone(self):
        self.install()
        before = self.installed.stat().st_mtime_ns
        self.assertEqual(self.install(), "existing")
        self.assertEqual(self.installed.stat().st_mtime_ns, before)

    def test_missing_master_is_an_error(self):
        with self.assertRaises(FileNotFoundError):
            ii.install(self.source.with_name("missing.md"), self.installed, "/v", "python3", force_new=True)
        self.assertEqual(ii.status(self.source.with_name("missing.md"), self.installed), "no_source")

    def test_master_copy_has_both_placeholders(self):
        text = ii.SOURCE.read_text(encoding="utf-8")
        self.assertIn("{{VAULT}}", text)
        self.assertIn("{{PY}}", text)

    def run_script(self, home: Path, *args: str) -> subprocess.CompletedProcess:
        env = {**os.environ, "HOME": str(home), "USERPROFILE": str(home)}
        return subprocess.run([sys.executable, "-I", "-B", str(SCRIPT), *args], capture_output=True, text=True,
                              encoding="utf-8", env=env, stdin=subprocess.DEVNULL, timeout=60)

    def test_command_in_fake_home_keeps_existing_file_byte_for_byte(self):
        home = Path(self.temporary.name) / "fake-home"
        (home / ".claude").mkdir(parents=True)
        own = b"# keep me\n\xc3\xa7 \r\n"
        (home / ".claude" / "CLAUDE.md").write_bytes(own)
        result = self.run_script(home, "install", "--force-new", "--vault", "/v", "--py", "python3")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("installer will offer you options", result.stdout)
        self.assertEqual((home / ".claude" / "CLAUDE.md").read_bytes(), own)

    def test_command_in_empty_fake_home(self):
        home = Path(self.temporary.name) / "empty-home"
        home.mkdir()
        self.assertEqual(self.run_script(home, "install", "--vault", "/v").returncode, 2)
        self.assertFalse((home / ".claude" / "CLAUDE.md").exists())
        result = self.run_script(home, "install", "--force-new", "--vault", "/v", "--py", "python3")
        self.assertEqual(result.returncode, 0, result.stderr)
        text = (home / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertNotIn("{{VAULT}}", text)
        self.assertNotIn("{{PY}}", text)
        self.assertIn("python3 -I", text)
        self.assertEqual(self.run_script(home, "status", "--vault", "/v", "--py", "python3").stdout.strip(), "same")


if __name__ == "__main__":
    unittest.main()
