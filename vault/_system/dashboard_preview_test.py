"""dashboard_preview.py tests: data embedding, script escape, missing data sets, output path.

Each test works in a new folder under _system/output/test_dashboard_preview/ (outside git); nothing is deleted (#22)."""
import io
import json
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
import dashboard_preview as dp  # noqa: E402

TEST_DIR = common.OUTPUT / "test_dashboard_preview"
PAGE = '<div class="mg" id="mg"><p>page body</p></div>\n<script>window.pageRan = true;</script>\n'
DATA_BLOCK = re.compile(r'<script type="application/json" id="mg-preview-data">(.*?)</script>', re.S)


class PreviewCase(unittest.TestCase):
    def setUp(self):
        TEST_DIR.mkdir(parents=True, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix="preview-", dir=TEST_DIR))
        self.data = self.root / "data"
        self.data.mkdir()
        self.page = self.root / "dashboard.html"
        self.page.write_text(PAGE, encoding="utf-8")

    def write_dataset(self, dataset: str, rows: list) -> None:
        (self.data / f"{dataset}.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")

    def build(self) -> str:
        return dp.build_preview(PAGE, self.data)

    def embedded(self, html: str) -> dict:
        block = DATA_BLOCK.search(html)
        self.assertIsNotNone(block, "the data block is missing")
        return json.loads(block.group(1))


class EmbedTest(PreviewCase):
    def test_data_set_rows_are_embedded(self):
        self.write_dataset("meta", [{"key": "meta", "language": "tr", "generated": "2026-11-10"}])
        data = self.embedded(self.build())
        self.assertEqual(data["meta"], [{"key": "meta", "language": "tr", "generated": "2026-11-10"}])

    def test_every_data_set_has_an_entry(self):
        self.assertEqual(sorted(self.embedded(self.build())), sorted(dp.DATASETS))

    def test_page_is_placed_inside_the_dash_root(self):
        html = self.build()
        start = html.index('<div id="dash-root">')
        self.assertGreater(html.index('<p>page body</p>'), start)
        self.assertGreater(html.index('window.pageRan'), start)

    def test_runtime_comes_before_the_page(self):
        html = self.build()
        self.assertLess(html.index("window.dash"), html.index('<div id="dash-root">'))


class EscapeTest(PreviewCase):
    def test_closing_script_tag_in_a_value_is_escaped(self):
        self.write_dataset("notes", [{"key": "a", "title": "</script><b>x</b>"}])
        html = self.build()
        self.assertNotIn("</script><b>", html)
        self.assertIn("\\u003c/script>\\u003cb>", html)

    def test_comment_and_script_start_in_a_value_cannot_reach_the_parser(self):
        self.write_dataset("notes", [{"key": "a", "title": "<!--<script>"}])
        block = DATA_BLOCK.search(self.build()).group(1)
        self.assertNotIn("<", block)

    def test_escaped_data_still_reads_back_unchanged(self):
        rows = [{"key": "a", "title": "</script><!-- x -->", "summary": "ğüşiöç"}]
        self.write_dataset("notes", rows)
        self.assertEqual(self.embedded(self.build())["notes"], rows)


class MissingTest(PreviewCase):
    def test_missing_file_is_embedded_as_null(self):
        self.write_dataset("meta", [{"key": "meta"}])
        data = self.embedded(self.build())
        self.assertIsNone(data["notes"])

    def test_runtime_reports_null_as_missing(self):
        runtime = dp.RUNTIME
        self.assertRegex(runtime, r"== null\)\s*return state\('missing'\)")

    def test_unreadable_json_counts_as_missing(self):
        (self.data / "log.json").write_text("{not json", encoding="utf-8")
        self.assertIsNone(self.embedded(self.build())["log"])


class GradualTest(PreviewCase):
    def test_gradual_mode_reads_the_query_and_waits_40_ms(self):
        self.assertIn("has('gradual')", dp.RUNTIME)
        self.assertIn(f"setTimeout(step, {dp.GRADUAL_STEP_MS})", dp.RUNTIME)
        self.assertEqual(dp.GRADUAL_STEP_MS, 40)

    def test_set_link_exists_and_does_nothing(self):
        self.assertRegex(dp.RUNTIME, r"setLink\(\)\s*\{\s*\}")


class OutputPathTest(PreviewCase):
    def test_default_output_is_under_the_dashboard_output_folder(self):
        self.assertEqual(dp.default_out(), common.vault_path("_system", "output", "dashboard", "preview.html"))

    def test_default_output_follows_the_install_names(self):
        names = {"folders": {"_system": "_sistem", "output": "cikti"}, "files": {}}
        with mock.patch.object(common, "NAMES", names):
            out = dp.default_out()
        self.assertEqual(out.relative_to(common.VAULT).as_posix(), "_sistem/cikti/dashboard/preview.html")

    def test_main_writes_the_preview_to_the_given_path(self):
        self.write_dataset("meta", [{"key": "meta", "language": "en"}])
        out = self.root / "nested" / "preview.html"
        with redirect_stdout(io.StringIO()) as printed:
            code = dp.main(["--page", str(self.page), "--data", str(self.data), "--out", str(out)])
        self.assertEqual(code, 0)
        self.assertTrue(out.is_file())
        self.assertIn('<div id="dash-root">', out.read_text(encoding="utf-8"))
        self.assertIn(str(out), printed.getvalue())

    def test_main_fails_with_a_message_when_the_page_is_missing(self):
        out = self.root / "preview.html"
        with redirect_stdout(io.StringIO()) as printed:
            code = dp.main(["--page", str(self.root / "nope.html"), "--data", str(self.data), "--out", str(out)])
        self.assertEqual(code, 1)
        self.assertFalse(out.exists())
        self.assertIn("nope.html", printed.getvalue())


if __name__ == "__main__":
    unittest.main()
