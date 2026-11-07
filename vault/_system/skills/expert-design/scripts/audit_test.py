"""Design audit tests: summary, exemption, preservation counter, round comparison, local address gate and measuring in
a real browser.

The browser tests open the local pages under test_pages/; without Edge or Chrome they are skipped. No network is used.
"""
import json
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import audit_summary as summ  # noqa: E402
import browser as br  # noqa: E402
import page_audit as pa  # noqa: E402


def report(url="u", width=1280, theme="light", findings=(), inventory=None):
    return {"url": url, "width": width, "theme": theme, "findings": list(findings), "inventory": inventory or {}, "measurements": {}}


def finding(rule="T01", severity="error", selector="div", detail="x"):
    return {"rule": rule, "severity": severity, "selector": selector, "detail": detail}


class SummaryTest(unittest.TestCase):
    def test_same_finding_at_two_widths_merges_into_one_line(self):
        summary = summ.summarize([report(width=320, findings=[finding()]), report(width=375, findings=[finding()])], [])
        self.assertEqual(summary["error"], 1)
        self.assertEqual(summary["findings"][0]["widths"], [320, 375])

    def test_report_without_errors_passes(self):
        self.assertTrue(summ.summarize([report(findings=[finding(severity="warning")])], [])["passed"])

    def test_report_with_an_error_fails(self):
        self.assertFalse(summ.summarize([report(findings=[finding()])], [])["passed"])


class ExemptionTest(unittest.TestCase):
    def test_justified_exemption_removes_the_error_from_the_count(self):
        summary = summ.summarize([report(findings=[finding()])], [{"rule": "T01", "reason": "the table scrolls sideways"}])
        self.assertEqual((summary["error"], summary["exempt"]), (0, 1))
        self.assertTrue(summary["passed"])

    def test_exemption_without_reason_is_invalid_and_fails_the_check(self):
        summary = summ.summarize([report(findings=[finding()])], [{"rule": "T01", "reason": "  "}])
        self.assertEqual(summary["error"], 1)
        self.assertEqual(len(summary["invalid_exemptions"]), 1)
        self.assertFalse(summary["passed"])

    def test_scope_exempts_only_the_matching_selector(self):
        exemption = [{"rule": "T04", "scope": ".chip", "reason": "dense filter"}]
        summary = summ.summarize([report(findings=[finding("T04", selector="button.chip"), finding("T04", selector="button.main")])], exemption)
        self.assertEqual((summary["error"], summary["exempt"]), (1, 1))

    def test_unused_exemption_is_reported(self):
        summary = summ.summarize([report()], [{"rule": "T09", "reason": "old"}])
        self.assertEqual(summary["unused_exemptions"][0]["rule"], "T09")

    def test_rule_exempt_on_three_pages_suggests_house_style(self):
        reports = [report(url=f"u{i}", findings=[finding("T04")]) for i in range(3)]
        summary = summ.summarize(reports, [{"rule": "T04", "reason": "dense interface"}])
        self.assertEqual(summary["house_style"], ["T04"])


class PreservationTest(unittest.TestCase):
    def test_vanished_item_is_reported_by_name(self):
        result = summ.compare_preservation({"buttons": ["Save", "Delete"]}, {"buttons": ["Save"]}, [])
        self.assertEqual(result["lost"], [{"type": "buttons", "name": "Delete"}])
        self.assertEqual(result["counts"]["buttons"], [2, 1])
        self.assertFalse(result["ok"])

    def test_removal_with_a_reason_is_not_a_loss(self):
        removed = [{"type": "buttons", "name": "Delete", "reason": "moved to the menu"}]
        result = summ.compare_preservation({"buttons": ["Delete"]}, {"buttons": []}, removed)
        self.assertEqual(result["lost"], [])
        self.assertEqual(len(result["justified"]), 1)
        self.assertTrue(result["ok"])

    def test_removal_without_a_reason_stays_a_loss(self):
        result = summ.compare_preservation({"buttons": ["Delete"]}, {"buttons": []}, [{"type": "buttons", "name": "Delete", "reason": ""}])
        self.assertEqual(len(result["lost"]), 1)

    def test_one_of_two_items_with_the_same_name_vanishing_is_caught(self):
        result = summ.compare_preservation({"links": ["Open", "Open"]}, {"links": ["Open"]}, [])
        self.assertEqual(result["lost"], [{"type": "links", "name": "Open"}])

    def test_added_items_are_listed_apart(self):
        result = summ.compare_preservation({"buttons": []}, {"buttons": ["New"]}, [])
        self.assertEqual(result["added"], [{"type": "buttons", "name": "New"}])
        self.assertTrue(result["ok"])


class RoundTest(unittest.TestCase):
    def test_first_round_has_no_comparison(self):
        self.assertEqual(summ.compare_rounds(None, {"keys": ["a"]}), {"new": [], "fixed": [], "regressed": False})

    def test_new_finding_counts_as_regression(self):
        difference = summ.compare_rounds({"keys": ["a"]}, {"keys": ["a", "b"]})
        self.assertEqual(difference["new"], ["b"])
        self.assertTrue(difference["regressed"])

    def test_fixed_finding_is_listed(self):
        difference = summ.compare_rounds({"keys": ["a"]}, {"keys": []})
        self.assertEqual(difference["fixed"], ["a"])
        self.assertFalse(difference["regressed"])


class AddressGateTest(unittest.TestCase):
    def setUp(self):
        self.old_socket = socket.socket
        socket.socket = lambda *a, **k: self.fail("the address gate must not open the network")

    def tearDown(self):
        socket.socket = self.old_socket

    def test_local_addresses_pass(self):
        for address in ("file:///C:/a.html", "http://localhost:3000/", "http://127.0.0.1:8000", "http://[::1]:80/", "http://app.localhost/", "https://x.test/"):
            self.assertTrue(pa.is_local_address(address), address)

    def test_external_address_and_tricks_are_refused(self):
        for address in ("https://example.com", "http://localhost.evil.com/", "http://127.0.0.1@evil.com/", "http://127.0.0.1.evil.com/", "javascript:alert(1)", "ftp://localhost/"):
            self.assertFalse(pa.is_local_address(address), address)


@unittest.skipUnless(br.find_browser(), "Edge or Chrome not found")
class MeasureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        cls.browser = br.Browser(Path(cls.folder.name) / "profile")

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.folder.cleanup()

    def measure(self, page, width=1280, theme="light"):
        address = (HERE / "test_pages" / page).as_uri()
        return pa.measure_page(self.browser, address, width, theme, Path(self.folder.name))

    def rules(self, result, severity=None):
        return {f["rule"] for f in result["findings"] if severity is None or f["severity"] == severity}

    def test_measures_at_the_real_width(self):
        self.assertEqual(self.measure("clean.html", 320)["measurements"]["width"], 320)

    def test_clean_page_has_no_error_or_warning(self):
        for width in (320, 375, 768, 1280, 1440, 1920):
            for theme in ("light", "dark"):
                with self.subTest(width=width, theme=theme):
                    result = self.measure("clean.html", width, theme)
                    self.assertEqual([f for f in result["findings"] if f["severity"] != "note"], [])

    def test_errors_on_flawed_page_are_caught(self):
        self.assertLessEqual({"T01", "T03", "T04", "T17"}, self.rules(self.measure("flawed.html"), "error"))

    def test_card_off_screen_is_measured_too(self):
        # content-visibility:auto does not render off-screen elements; the audit must see them as well
        targets = [f for f in self.measure("flawed.html")["findings"] if f["rule"] == "T04"]
        self.assertTrue(any("far-away" in f["selector"] for f in targets), targets)

    def test_contrast_of_oklch_color_is_measured(self):
        contrast = [f for f in self.measure("flawed.html")["findings"] if f["rule"] == "T03"]
        self.assertTrue(any("p.faded" in f["selector"] for f in contrast), contrast)

    def test_warnings_on_flawed_page_are_caught(self):
        expected = {"T07", "T08", "T09", "T14", "T15", "T16", "T18", "T25", "T27", "T28", "T30"}
        self.assertLessEqual(expected, self.rules(self.measure("flawed.html"), "warning"))

    def test_ai_traces_on_flawed_page_are_caught(self):
        expected = {"T11", "T12", "T19", "T20", "T21", "T22", "T23", "T24", "T26"}
        self.assertLessEqual(expected, self.rules(self.measure("flawed.html"), "note"))

    def test_small_input_text_on_narrow_screen_is_warned(self):
        self.assertIn("T05", self.rules(self.measure("flawed.html", 375), "warning"))

    def test_overflow_on_narrow_screen_is_caught(self):
        for width in (320, 375):
            with self.subTest(width=width):
                result = self.measure("flawed.html", width)
                self.assertEqual(result["measurements"]["width"], width)
                self.assertIn("T01", self.rules(result, "error"))

    def test_button_label_that_really_breaks_is_caught(self):
        broken = [f for f in self.measure("flawed.html")["findings"] if f["rule"] == "T25"]
        self.assertTrue(any("narrow-button" in f["selector"] for f in broken), broken)

    def test_inventory_items_come_with_their_names(self):
        inventory = self.measure("clean.html")["inventory"]
        self.assertIn("Open file", inventory["buttons"])
        self.assertIn("See problems -> #problems", inventory["links"])
        self.assertIn("h1: Customer records are ready", inventory["headings"])
        self.assertIn("File name", inventory["fields"])

    def test_measurements_give_control_height_and_first_screen_words(self):
        measurements = self.measure("clean.html")["measurements"]
        self.assertIn(48, measurements["control_heights"])
        self.assertGreater(measurements["first_screen_words"], 5)

    def test_screenshot_is_written(self):
        result = self.measure("clean.html", 375, "dark")
        self.assertGreater(Path(result["image"]).stat().st_size, 1000)


@unittest.skipUnless(br.find_browser(), "Edge or Chrome not found")
class CommandTest(unittest.TestCase):
    BEFORE = '<!doctype html><html lang="en"><title>t</title><h1>Top</h1><button style="min-width:48px;min-height:48px;font-size:16px">Save</button><button style="min-width:48px;min-height:48px;font-size:16px">Delete</button>'
    AFTER = '<!doctype html><html lang="en"><title>t</title><h1>Top</h1><button style="min-width:48px;min-height:48px;font-size:16px">Save</button>'

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.page = self.root / "page.html"
        self.record = self.root / "record.json"

    def run_audit(self, *extra):
        return subprocess.run(
            [sys.executable, "-I", str(HERE / "page_audit.py"), self.page.as_uri(), "--output", str(self.root / "output"), "--record", str(self.record), "--widths", "1280", *extra],
            capture_output=True, encoding="utf-8", timeout=120,
        )

    def test_vanished_button_is_reported_by_name_and_fails(self):
        self.page.write_text(self.BEFORE, encoding="utf-8")
        self.assertEqual(self.run_audit("--baseline").returncode, 0)
        self.page.write_text(self.AFTER, encoding="utf-8")
        result = self.run_audit()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("LOST buttons: Delete", result.stdout)

    def test_loss_passes_once_a_reason_is_written(self):
        self.page.write_text(self.BEFORE, encoding="utf-8")
        self.run_audit("--baseline")
        record = json.loads(self.record.read_text(encoding="utf-8"))
        record["removed"] = [{"type": "buttons", "name": "Delete", "reason": "moved to the menu"}]
        self.record.write_text(json.dumps(record), encoding="utf-8")
        self.page.write_text(self.AFTER, encoding="utf-8")
        self.assertEqual(self.run_audit().returncode, 0)

    def test_round_history_and_user_note_are_written(self):
        self.page.write_text(self.BEFORE, encoding="utf-8")
        self.run_audit()
        self.run_audit("--note", "make the heading bigger")
        rounds = json.loads(self.record.read_text(encoding="utf-8"))["rounds"]
        self.assertEqual([r["round"] for r in rounds], [1, 2])
        self.assertEqual(rounds[1]["user_note"], "make the heading bigger")

    def test_new_finding_is_reported_as_regression(self):
        self.page.write_text(self.BEFORE, encoding="utf-8")
        self.run_audit()
        self.page.write_text(self.BEFORE + "<img src='x.png'>", encoding="utf-8")
        self.assertIn("REGRESSED", self.run_audit().stdout)

    def test_summary_json_is_written(self):
        self.page.write_text(self.BEFORE, encoding="utf-8")
        self.run_audit()
        data = json.loads((self.root / "output" / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(set(data), {"summary", "preservation", "round_difference", "reports"})
        self.assertIn("external_resources", data["reports"][0]["measurements"])

    def test_external_address_is_refused_without_opening_a_browser(self):
        result = subprocess.run(
            [sys.executable, "-I", str(HERE / "page_audit.py"), "https://example.com", "--output", str(self.root / "output")],
            capture_output=True, encoding="utf-8", timeout=30,
        )
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.root / "output").exists())


if __name__ == "__main__":
    unittest.main()
