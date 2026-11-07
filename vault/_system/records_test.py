"""records.py and common.py tests. They never touch real vault files: temporary copies under _system/output/test_records/."""
import importlib
import sys
import threading
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
import records  # noqa: E402
from common_test import TR_NAMES  # noqa: E402

TEST_DIR = common.OUTPUT / "test_records"
PENDING_MONTH = f"{common.name('pending')}-2026-09.md"   # archive of closed items: <pending name>-<month>.md
PENDING_SAMPLE = """---
type: entry
updated: 2000-01-01
---

# Pending

## Open
- [ ] P-005 | question | 2026-10-01 | old question | [[a]] | chat: X
- [ ] P-012 | approval | 2026-10-02 | waiting for approval | [[b]] | chat: X

## Closed
- [x] P-003 | task | 2026-09-01 | done | [[c]] | chat: X | ✔ 2026-09-02
"""


def sample_log(day_lines: dict[str, int], line: str = "- a") -> str:
    """Sample log with two entries per day, about `line count` long in total."""
    parts = ["# Log\n"]
    for day, count in day_lines.items():
        for half in (count // 2, count - count // 2):
            parts.append(f"## [{day}] setup | [[n]]\n" + f"{line}\n" * (half - 1))
    return "".join(parts)


class RecordsTest(unittest.TestCase):
    def setUp(self):
        TEST_DIR.mkdir(parents=True, exist_ok=True)
        self.old = (records.PENDING, records.LOG, records.HANDOFF, records.HANDOFF_ARCHIVE, records.LOG_ARCHIVE,
                    records.PENDING_ARCHIVE)
        records.LOG_ARCHIVE = TEST_DIR / "log_archive"            # must never write to the real archive
        records.PENDING_ARCHIVE = TEST_DIR / "pending_archive"
        for folder in (records.LOG_ARCHIVE, records.PENDING_ARCHIVE):
            for f in folder.glob("*.md") if folder.is_dir() else []:
                f.write_text("", encoding="utf-8")  # empty without deleting (#22)
        records.PENDING = TEST_DIR / "pending.md"
        records.LOG = TEST_DIR / "log.md"
        records.HANDOFF = TEST_DIR / "handoff.md"
        records.HANDOFF_ARCHIVE = TEST_DIR / "archive"
        records.PENDING.write_text(PENDING_SAMPLE, encoding="utf-8")
        records.LOG.write_text("# Log\n", encoding="utf-8")
        records.HANDOFF.write_text("", encoding="utf-8")
        for f in records.HANDOFF_ARCHIVE.glob("*.md") if records.HANDOFF_ARCHIVE.is_dir() else []:
            f.write_text("", encoding="utf-8")  # empty without deleting (#22)

    def tearDown(self):
        (records.PENDING, records.LOG, records.HANDOFF, records.HANDOFF_ARCHIVE, records.LOG_ARCHIVE,
         records.PENDING_ARCHIVE) = self.old

    def test_number_is_largest_plus_one_and_before_closed(self):
        no = records.add_pending("approval", "new | item", "note", "Chat")
        text = records.PENDING.read_text(encoding="utf-8")
        new = f"{records.PENDING_PREFIX}-013"                  # new ids take the prefix of the install language
        self.assertEqual(no, new)
        self.assertLess(text.index(new), text.index("## Closed"))
        self.assertIn("new / item", text)                      # | must not break the table
        self.assertIn(f"pending | {new}", records.LOG.read_text(encoding="utf-8"))

    def test_invalid_type_and_missing_chat_rejected(self):
        with self.assertRaises(records.RecordError):
            records.add_pending("wish", "x", "a", "S")
        with self.assertRaises(records.RecordError):
            records.add_pending("question", "x", "a", " ")

    def test_source_and_project_line_injection_rejected(self):
        # Regression (reviewer): a fake closed line could be written through the source field
        for source, project in (("x]]\n- [x] P-900 | approval | 2026-01-01 | fake | [[y", ""), ("note", "p|q"), ("a[b", "")):
            with self.subTest(source=source[:10], project=project):
                with self.assertRaises(records.RecordError):
                    records.add_pending("question", "x", source, "S", project)
        self.assertNotIn("P-900", records.PENDING.read_text(encoding="utf-8"))

    def test_item_is_not_lost_when_heading_missing(self):
        # Regression: an item closed with "## Closed " (trailing space) was silently deleted
        text = PENDING_SAMPLE.replace("## Closed\n", "## Closed items\n")
        records.PENDING.write_text(text, encoding="utf-8")
        with self.assertRaises(records.RecordError):
            records.close_pending("P-005", "yes", "commit 1")
        self.assertEqual(records.PENDING.read_text(encoding="utf-8"), text)
        records.PENDING.write_text(PENDING_SAMPLE.replace("## Closed\n", "## Closed  \n"), encoding="utf-8")
        records.close_pending("P-005", "yes", "commit 1")      # a trailing space is tolerated
        self.assertIn("- [x] P-005", records.PENDING.read_text(encoding="utf-8"))

    def test_cannot_close_without_evidence(self):
        with self.assertRaises(records.RecordError):
            records.close_pending("P-005", "answered", "  ")

    def test_close_with_evidence_moves_to_closed(self):
        records.close_pending("P-005", "user: yes", "commit abc1234")
        text = records.PENDING.read_text(encoding="utf-8")
        open_part, closed_part = text.split("## Closed")
        self.assertNotIn("P-005", open_part)
        self.assertIn("- [x] P-005", closed_part)
        self.assertIn("evidence: commit abc1234", closed_part)
        self.assertIn("done | P-005", records.LOG.read_text(encoding="utf-8"))   # evidence in the pending line, one log line
        self.assertIn("P-003", (records.PENDING_ARCHIVE / PENDING_MONTH).read_text(encoding="utf-8"))  # past month archived
        self.assertNotIn("P-003", records.PENDING.read_text(encoding="utf-8"))
        with self.assertRaises(records.RecordError):
            records.close_pending("P-005", "again", "x")         # already closed

    def test_hold_changes_type_keeps_open(self):
        records.hold_pending("P-012", "look at later")
        line = [s for s in records.PENDING.read_text(encoding="utf-8").splitlines() if "P-012" in s][0]
        self.assertTrue(line.startswith("- [ ] P-012 | on-hold |"))
        self.assertIn("⏸", line)

    def test_short_summary_does_not_cut_inside_link(self):
        # A log line once kept "([[sample-pro": the 80-character cut fell inside the link
        text = "a" * 65 + " done ([[sample-progress]]) and more"   # link 72-91: limit 80 inside
        summary = records.short_summary(text, 80)
        self.assertIn("[[sample-progress]]", summary)
        self.assertEqual(summary.count("[["), summary.count("]]"))
        self.assertTrue(summary.endswith("…"))

    def test_short_summary_keeps_text_that_fits(self):
        self.assertEqual(records.short_summary("short [[note]]", 80), "short [[note]]")

    def test_hold_log_does_not_break_link(self):
        no = records.add_pending("question", "x", "source", "chat")
        records.hold_pending(no, "b" * 40 + " site permission given, done ([[sample-progress]])")   # link 70-89
        log = records.LOG.read_text(encoding="utf-8")
        self.assertIn("[[sample-progress]]", log)

    def test_log_operation_checked_and_learned_written(self):
        with self.assertRaises(records.RecordError):
            records.add_log("random", "x")
        records.add_log("progress", "work [[note]]", "- done", learned="lesson")
        self.assertIn("- Learned: lesson", records.LOG.read_text(encoding="utf-8"))

    def test_handoff_same_session_renews_its_own_card(self):
        records.write_handoff("aaaaaaaa1111", "first", "first text")
        records.write_handoff("bbbbbbbb2222", "second", "another session")
        records.write_handoff("aaaaaaaa1111", "first", "updated text")
        text = records.HANDOFF.read_text(encoding="utf-8")
        self.assertEqual(text.count("aaaaaaaa"), 1)
        self.assertIn("updated text", text)
        self.assertNotIn("first text", text)
        self.assertLess(text.index("aaaaaaaa"), text.index("bbbbbbbb"))   # newest on top

    def test_handoff_old_cards_moved_to_archive_not_deleted(self):
        for i in range(records.HANDOFF_KEPT + 2):
            records.write_handoff(f"{i:08x}", f"card{i}", f"text-{i}")
        cards = records.handoff_cards(records.HANDOFF.read_text(encoding="utf-8"))
        archive = "".join(f.read_text(encoding="utf-8") for f in records.HANDOFF_ARCHIVE.glob("*.md"))
        self.assertEqual(len(cards), records.HANDOFF_KEPT)
        self.assertIn("text-0", archive)
        self.assertIn("text-1", archive)

    def test_handoff_long_card_rejected(self):
        with self.assertRaises(records.RecordError):
            records.write_handoff("cccccccc", "long", "x" * (records.HANDOFF_CARD_LIMIT + 1))

    def test_handoff_summary_is_limited(self):
        records.write_handoff("dddddddd", "a", "y" * 2500)
        self.assertLessEqual(len(records.handoff_summary(limit=500)), 560)

    def test_work_entry_needs_link_and_short_body(self):
        with self.assertRaises(records.RecordError):
            records.add_log("setup", "no link", "- x")
        with self.assertRaises(records.RecordError):
            records.add_log("setup", "[[note]]", "- a\n- b\n- c\n- d", learned="none")   # rejected for its length
        records.add_log("pending", "P-001 — no link needed")

    def test_work_entry_without_learned_rejected(self):
        # Progress entries were once written without a 'Learned:' line; the log is append-only, so they could not be fixed
        with self.assertRaises(records.RecordError):
            records.add_log("progress", "work [[note]]", "- done")
        records.add_log("progress", "work [[note]]", "- done", learned="none")
        records.add_log("idea", "idea [[note]]")   # an idea does not count as a work entry
        self.assertIn("- Learned: none", records.LOG.read_text(encoding="utf-8"))

    def test_log_moves_past_month_to_archive_keeps_this_month(self):
        remaining, months = records.rotate_log("head\n## [2026-09-30] setup | old\n- a\n## [2026-10-01] idea | new\n", "2026-10-01")
        self.assertEqual(remaining, "head\n## [2026-10-01] idea | new\n")
        self.assertEqual(months, {"2026-09": "## [2026-09-30] setup | old\n- a\n"})

    def test_below_limit_cutoff_is_month_start(self):
        self.assertEqual(records.cutoff_date(sample_log({"2026-10-02": 300, "2026-10-16": 300}), "2026-10-16"), "2026-10-01")

    def test_above_limit_oldest_days_moved_rest_fits_target(self):
        text = sample_log({f"2026-10-{d}": 300 for d in range(10, 17)})        # 7 days x 300 lines
        cutoff = records.cutoff_date(text, "2026-10-16")
        remaining, months = records.rotate_log(text, cutoff)
        self.assertEqual(cutoff, "2026-10-14")                                   # 1 + 3 x 300 <= 1,000; a 4th day does not fit
        self.assertLessEqual(remaining.count("\n"), records.LOG_TARGET_LINES)
        self.assertEqual(remaining.count("## ["), 6)                             # days are not split: 3 days x 2 entries
        self.assertEqual(months["2026-10"].count("## ["), 8)

    def test_byte_limit_also_rotates(self):
        text = sample_log({"2026-10-15": 10, "2026-10-16": 10}, line="x" * 9000)   # 21 lines, ~144 KB
        self.assertEqual(records.cutoff_date(text, "2026-10-16"), "2026-10-16")

    def test_today_never_moved_even_if_alone_above_limit(self):
        cutoff = records.cutoff_date(sample_log({"2026-10-15": 10, "2026-10-16": 1500}), "2026-10-16")
        self.assertEqual(cutoff, "2026-10-16")

    def test_add_log_above_limit_appends_to_same_month_archive(self):
        this_day = records.today()
        days = [(date.fromisoformat(this_day) - timedelta(days=k)).isoformat() for k in range(6, -1, -1)]
        records.LOG.write_text(sample_log(dict.fromkeys(days, 300)), encoding="utf-8")
        archive = records.LOG_ARCHIVE / f"log-{days[0][:7]}.md"
        records.LOG_ARCHIVE.mkdir(parents=True, exist_ok=True)
        archive.write_text("## [2000-01-01] setup | earlier move\n", encoding="utf-8")
        records.add_log("pending", "P-001 — new")
        log = records.LOG.read_text(encoding="utf-8")
        moved = "".join(f.read_text(encoding="utf-8") for f in sorted(records.LOG_ARCHIVE.glob("*.md")))
        self.assertLessEqual(log.count("\n"), records.LOG_TARGET_LINES + 2)
        self.assertIn(f"## [{this_day}] pending | P-001", log)
        self.assertLess(moved.index("earlier move"), moved.index(f"## [{days[0]}]"))
        self.assertEqual(log.count("## [") + moved.count("## ["), 7 * 2 + 1 + 1)   # no entry is lost

    def test_archive_name_carries_kind_log_and_pending_archives_do_not_clash(self):
        records.append_to_archive(records.LOG_ARCHIVE, "log", "2026-09", "## [2026-09-30] setup | x\n")
        records.append_to_archive(records.PENDING_ARCHIVE, "pending", "2026-09", "- [x] P-001 | task | 2026-09-01 | x\n")
        self.assertTrue((records.LOG_ARCHIVE / "log-2026-09.md").is_file())
        self.assertTrue((records.PENDING_ARCHIVE / "pending-2026-09.md").is_file())

    def test_number_counts_archived_ones_too(self):
        records.PENDING_ARCHIVE.mkdir(parents=True, exist_ok=True)
        (records.PENDING_ARCHIVE / "pending-2026-09.md").write_text(
            "- [x] P-040 | task | 2026-09-01 | x | [[c]] | chat: X | ✔ 2026-09-02\n", encoding="utf-8")
        self.assertEqual(records.next_number(records.PENDING.read_text(encoding="utf-8")), 41)

    def test_both_prefixes_and_turkish_heading_accepted(self):
        # A Turkish vault uses B- ids and the "Kapananlar" heading; numbering spans both prefixes
        text = (PENDING_SAMPLE.replace("P-012", "B-020").replace("## Closed\n", "## Kapananlar\n")
                .replace("- [x] P-003", "- [x] B-003"))
        records.PENDING.write_text(text, encoding="utf-8")
        self.assertEqual(records.next_number(text), 21)
        records.close_pending("B-020", "user: yes", "commit abc1234")
        closed_part = records.PENDING.read_text(encoding="utf-8").split("## Kapananlar")[1]
        self.assertIn("- [x] B-020", closed_part)
        self.assertNotIn("B-003", records.PENDING.read_text(encoding="utf-8"))   # closed B- lines rotate too
        self.assertIn("B-003", (records.PENDING_ARCHIVE / PENDING_MONTH).read_text(encoding="utf-8"))


class TurkishInstallTest(unittest.TestCase):
    """With the Turkish name map in config.json, records.py paths and new ids come out Turkish."""

    def test_paths_and_prefix_follow_name_map(self):
        try:
            with mock.patch.object(common, "NAMES", TR_NAMES), mock.patch.object(common, "LANGUAGE", "tr"):
                importlib.reload(records)
                self.assertEqual(records.PENDING, common.VAULT / "gelen" / "bekleyenler.md")
                self.assertEqual(records.HANDOFF, common.VAULT / "gelen" / "devir.md")
                self.assertEqual(records.LOG, common.VAULT / "log.md")
                self.assertEqual(records.INDEX, common.VAULT / "index.md")
                self.assertEqual(records.LOG_ARCHIVE, common.VAULT / "arsiv" / "log")
                self.assertEqual(records.PENDING_ARCHIVE, common.VAULT / "arsiv" / "bekleyenler")
                self.assertEqual(records.HANDOFF_ARCHIVE, common.VAULT / "arsiv" / "devir")
                self.assertEqual(records.PENDING_PREFIX, "B")
        finally:
            importlib.reload(records)   # back to the map of this install
        self.assertEqual(records.PENDING, common.vault_path("inbox", "pending.md"))
        self.assertEqual(records.PENDING_PREFIX, "B" if common.LANGUAGE == "tr" else "P")


class IndexTest(unittest.TestCase):
    INDEX = """# Index
<!-- central:start -->
## Most central notes
- [[a]] — 9 incoming links
<!-- central:end -->

## Knowledge — ML
- [[a]] — note a

## Research
- [[b]] — note b
"""

    def setUp(self):
        TEST_DIR.mkdir(parents=True, exist_ok=True)
        self.old = records.INDEX
        records.INDEX = TEST_DIR / "index.md"
        records.INDEX.write_text(self.INDEX, encoding="utf-8")

    def tearDown(self):
        records.INDEX = self.old

    def test_line_goes_to_section_not_auto_block(self):
        # Regression (rule #36): the line fell into the automatic block because its link also appeared there
        records.add_index("Knowledge — ML", "- [[c]] — note c")
        text = records.INDEX.read_text(encoding="utf-8")
        block_end, ml, research = text.index("central:end"), text.index("## Knowledge — ML"), text.index("## Research")
        self.assertTrue(block_end < ml < text.index("[[c]]") < research)

    def test_existing_outside_section_and_format_rejected(self):
        with self.assertRaises(records.RecordError):
            records.add_index("Knowledge — ML", "- [[a]] — again")
        with self.assertRaises(records.RecordError):
            records.add_index("Most central notes", "- [[d]] — cannot write to the automatic block")
        with self.assertRaises(records.RecordError):
            records.add_index("Knowledge — ML", "plain text")
        self.assertEqual(records.INDEX.read_text(encoding="utf-8"), self.INDEX)

    def test_indented_sub_line_added_and_duplicate_caught(self):
        # Regression: project decisions are indented in the index; the tool did not accept the sub-line or see its duplicate
        records.INDEX.write_text(self.INDEX.replace("## Research", "## Projects\n- [[p]] — project\n  - [[p-adr-001]] — first decision\n\n## Research"), encoding="utf-8")
        records.add_index("Projects", "  - [[p-adr-002]] — second decision")
        text = records.INDEX.read_text(encoding="utf-8")
        self.assertIn("  - [[p-adr-001]] — first decision\n  - [[p-adr-002]] — second decision\n", text)
        with self.assertRaises(records.RecordError):
            records.add_index("Projects", "- [[p-adr-001]] — again")   # counts as present even without indent


class LockTest(unittest.TestCase):
    def test_second_lock_not_taken_while_held(self):
        taken, release = threading.Event(), threading.Event()

        def hold():
            with common.locked("test"):
                taken.set()
                release.wait(5)
        t = threading.Thread(target=hold)
        t.start()
        taken.wait(5)
        try:
            with self.assertRaises(common.LockUnavailable):
                with common.locked("test", wait_s=0.3):
                    pass
        finally:
            release.set()
            t.join()
        with common.locked("test", wait_s=1):    # can be taken once released
            pass

    def test_atomic_write_writes_lf(self):
        TEST_DIR.mkdir(parents=True, exist_ok=True)
        target = TEST_DIR / "atomic.txt"
        common.atomic_write(target, "a\nb\n")
        self.assertEqual(target.read_bytes(), b"a\nb\n")

    def test_frontmatter_list_and_body(self):
        fields, body = common.frontmatter("---\ntype: concept\ntags: [a, b]\nproject: \"[[x]]\"\n---\n# Title\n")
        self.assertEqual(fields["tags"], ["a", "b"])
        self.assertEqual(fields["project"], "[[x]]")
        self.assertEqual(body, "# Title\n")


if __name__ == "__main__":
    unittest.main(verbosity=1)
