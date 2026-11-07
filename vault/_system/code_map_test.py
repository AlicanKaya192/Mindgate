"""code_map.py tests: module names, import edges and cycles, call labels, skipped files.
Temporary project: _system/output/test_code_map/. No file is run; no network."""
import contextlib
import io
import json
import shutil
import sys
import unittest
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import code_map as cm  # noqa: E402
import common  # noqa: E402

ROOT = common.OUTPUT / "test_code_map"
PROJECT = {
    "pkg/__init__.py": "",
    "pkg/a.py": (
        "import os\n"
        "from pkg import b\n"
        "from .b import helper\n\n"
        "def main():\n"
        "    helper()\n"
        "    b.compute()\n"
        "    local()\n"
        "    os.getcwd()\n\n"
        "def local():\n"
        "    pass\n\n"
        "class Worker:\n"
        "    def run(self):\n"
        "        self.inner()\n\n"
        "    def inner(self):\n"
        "        pass\n"
    ),
    "pkg/b.py": (
        "import pkg.a\n\n"
        "def helper():\n"
        "    pass\n\n"
        "def compute():\n"
        "    pass\n\n"
        "def use(obj):\n"
        "    obj.run()\n"
        "    obj.shared()\n"
        "    pkg.a.local()\n\n"
        "def signal(window):\n"
        "    window.button.run()\n"
    ),
    "pkg/c.py": (
        "class K:\n"
        "    def shared(self):\n"
        "        pass\n\n"
        "class L:\n"
        "    def shared(self):\n"
        "        pass\n"
    ),
    "broken.py": "def (:\n",
    ".venv/outside.py": "def hidden():\n    pass\n",
}


class CodeMapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        shutil.rmtree(ROOT, ignore_errors=True)
        for path, text in PROJECT.items():
            (ROOT / path).parent.mkdir(parents=True, exist_ok=True)
            (ROOT / path).write_text(text, encoding="utf-8")
        cls.m = cm.build_map(ROOT)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(ROOT, ignore_errors=True)

    def edge(self, source: str, target: str) -> str | None:
        return next((c.label for c in self.m.calls if c.source == source and c.target == target), None)

    def test_module_names(self):
        self.assertEqual(set(self.m.modules), {"pkg", "pkg.a", "pkg.b", "pkg.c"})

    def test_virtual_environment_is_not_read(self):
        self.assertFalse(any(d.name.endswith("hidden") for d in self.m.definitions))

    def test_file_with_syntax_error_is_skipped(self):
        self.assertIn("broken.py", [path for path, _ in self.m.skipped])

    def test_internal_imports_are_edges_external_are_not(self):
        self.assertIn(("pkg.a", "pkg.b"), self.m.imports)
        self.assertIn(("pkg.b", "pkg.a"), self.m.imports)
        self.assertFalse(any(t == "os" for _, t in self.m.imports))

    def test_import_cycle_is_found(self):
        self.assertEqual(cm.import_cycles(self.m.imports), [["pkg.a", "pkg.b"]])

    def test_call_through_relative_import_is_extracted(self):
        self.assertEqual(self.edge("pkg.a.main", "pkg.b.helper"), "extracted")

    def test_call_through_module_is_extracted(self):
        self.assertEqual(self.edge("pkg.a.main", "pkg.b.compute"), "extracted")

    def test_call_in_same_module_is_extracted(self):
        self.assertEqual(self.edge("pkg.a.main", "pkg.a.local"), "extracted")

    def test_call_through_dotted_import_is_extracted(self):
        self.assertEqual(self.edge("pkg.b.use", "pkg.a.local"), "extracted")

    def test_self_call_is_extracted(self):
        self.assertEqual(self.edge("pkg.a.Worker.run", "pkg.a.Worker.inner"), "extracted")

    def test_method_fitting_one_definition_is_guessed(self):
        self.assertEqual(self.edge("pkg.b.use", "pkg.a.Worker.run"), "guessed")

    def test_method_through_chained_attribute_is_not_guessed(self):
        # GUI signals (`self.button.clicked.connect`) must not be attached wrongly to the project's only `connect`
        self.assertIsNone(self.edge("pkg.b.signal", "pkg.a.Worker.run"))

    def test_report_call_count_ignores_guesses(self):
        counts = dict(cm.most_called(self.m, 50))
        self.assertNotIn("pkg.a.Worker.run", counts)
        self.assertEqual(counts["pkg.a.Worker.inner"], 1)

    def test_method_fitting_many_definitions_is_no_edge_but_counted(self):
        self.assertFalse(any(c.target.endswith(".shared") for c in self.m.calls))
        self.assertEqual(self.m.ambiguous, 1)

    def test_outside_library_call_is_no_edge(self):
        self.assertFalse(any(c.target.startswith("os") for c in self.m.calls))

    def test_find_definition_and_callers(self):
        definitions, callers = cm.find(self.m, "helper")
        self.assertEqual([(d.file, d.line) for d in definitions], [("pkg/b.py", 3)])
        self.assertEqual([c.source for c in callers], ["pkg.a.main"])

    def test_excluded_folder_is_not_read_module_names_stay_correct(self):
        m = cm.build_map(ROOT, excluded={"pkg/c.py", "broken.py"})
        self.assertEqual(set(m.modules), {"pkg", "pkg.a", "pkg.b"})
        self.assertEqual(m.skipped, [])

    def test_json_record(self):
        target = ROOT / "output" / "map.json"
        cm.save(self.m, target)
        data = json.loads(target.read_text(encoding="utf-8"))
        self.assertIn(["pkg.a", "pkg.b"], data["imports"])
        self.assertTrue(any(c["label"] == "guessed" for c in data["calls"]))

    def test_command_line_find_and_exclude(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(cm.main([str(ROOT), "--find", "helper", "--exclude", "pkg/c.py"]), 0)
        self.assertIn("function pkg.b.helper — pkg/b.py:3", out.getvalue())
        self.assertIn("pkg.a.main — pkg/a.py:6 [extracted]", out.getvalue())


class WarningTest(unittest.TestCase):
    def tearDown(self):
        shutil.rmtree(ROOT, ignore_errors=True)

    def test_invalid_escape_sequence_does_not_leak_a_warning(self):
        (ROOT / "warning").mkdir(parents=True, exist_ok=True)
        (ROOT / "warning" / "m.py").write_text('PATH = "C:\\project"\n', encoding="utf-8")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            m = cm.build_map(ROOT / "warning")
        self.assertEqual(list(m.modules), ["m"])
        self.assertEqual([w for w in caught if issubclass(w.category, SyntaxWarning)], [])


class LargeFileTest(unittest.TestCase):
    def setUp(self):
        (ROOT / "large").mkdir(parents=True, exist_ok=True)
        (ROOT / "large" / "huge.py").write_text("x = 1\n" * 50, encoding="utf-8")
        self.old, cm.MAX_BYTES = cm.MAX_BYTES, 100

    def tearDown(self):
        cm.MAX_BYTES = self.old
        shutil.rmtree(ROOT, ignore_errors=True)

    def test_very_large_file_is_skipped_unread(self):
        m = cm.build_map(ROOT / "large")
        self.assertEqual(m.skipped, [("huge.py", "too large")])
        self.assertEqual(m.modules, {})


if __name__ == "__main__":
    unittest.main()
