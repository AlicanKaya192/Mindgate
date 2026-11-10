"""dashboard_data.py tests. Each test builds a small vault in a new folder under _system/output/test_dashboard/ (outside git)
and never reads the real vault; nothing is deleted (#22)."""
import json
import tempfile
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
import dashboard_data as dd  # noqa: E402
from common_test import TR_NAMES  # noqa: E402

TEST_DIR = common.OUTPUT / "test_dashboard"
TODAY = "2026-11-10"
EN_NAMES = {"folders": {}, "files": {}}


def note(kind: str, title: str, body: str = "", **fields) -> str:
    extra = "".join(f"{k}: {v}\n" for k, v in fields.items())
    return f"---\ntype: {kind}\nstatus: active\n{extra}created: 2026-11-01\nupdated: 2026-11-02\n---\n\n# {title}\n\n{body}"


class VaultCase(unittest.TestCase):
    names = EN_NAMES

    def setUp(self):
        TEST_DIR.mkdir(parents=True, exist_ok=True)
        self.vault = Path(tempfile.mkdtemp(prefix=self.id().rsplit(".", 1)[-1] + "-", dir=TEST_DIR))
        patches = [mock.patch.object(common, "VAULT", self.vault), mock.patch.object(common, "NAMES", self.names)]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def write(self, relative: str, text: str) -> None:
        path = self.vault / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def build(self) -> dict:
        return dd.build_datasets(TODAY, extras={})


class PrivacyTest(VaultCase):
    def setUp(self):
        super().setUp()
        self.write("me/profile.md", note("profile", "Profile", "secret life"))
        self.write("CLAUDE.md", "# Schema\n")
        self.write("inbox/sessions/2026-11-10-x.md", note("session", "Raw session", "raw text"))
        self.write("ideas/hidden.md", note("idea", "Hidden idea", "[[public]]", privacy="private"))
        self.write("knowledge/my-passwords.md", note("concept", "Passwords"))
        self.write("knowledge/public.md", note("concept", "Public", "## In one sentence\nA public note.\n\n[[profile]]"))

        self.write("knowledge/other.md", note("concept", "Other", "[[public]] [[hidden]]"))

    def test_private_notes_stay_out(self):
        ids = {r["id"] for r in self.build()["notes"]}
        self.assertEqual(ids, {"public", "other"})

    def test_links_touching_private_notes_stay_out(self):
        links = {(r["source"], r["target"]) for r in self.build()["links"]}
        self.assertEqual(links, {("other", "public")})

    def test_private_link_target_is_not_broken(self):
        self.assertFalse(any(r["broken"] for r in self.build()["links"] if not r.get(dd.PLACEHOLDER)))

    def test_session_records_are_only_counted(self):
        counts = {r["key"]: r["value"] for r in self.build()["counts"]}
        self.assertEqual(counts["sessions_waiting"], 1)
        self.assertEqual(counts["private_notes"], 4)   # profile, CLAUDE, hidden idea, sensitive name

    def test_private_text_never_reaches_any_dataset(self):
        dump = json.dumps(self.build(), ensure_ascii=False)
        for text in ("secret life", "raw text", "Hidden idea", "Passwords"):
            self.assertNotIn(text, dump)


class SecretTest(VaultCase):
    def test_secret_in_summary_is_hidden(self):
        self.write("knowledge/k.md", note("concept", "Key", "## In one sentence\napi_key = sk-ant-abcdefghijklmnopqrstuvwx1234\n"))  # secret-scan: allow (fake key on purpose)
        row = self.build()["notes"][0]
        self.assertNotIn("sk-ant", row["summary"])
        self.assertEqual(row["summary"], dd.HIDDEN_TEXT)

    def test_secret_in_handoff_is_hidden(self):
        card = "## 2026-11-10 10:00 · Work · 0123abcd\npassword = hunter2hunter2\n"
        self.write("inbox/handoff.md", note("entry", "Handoff") + "\n" + card)
        row = self.build()["handoff"][0]
        self.assertNotIn("hunter2", row["text"])


class PlaceholderTest(VaultCase):
    def test_empty_vault_gives_no_empty_dataset(self):
        data = self.build()
        self.assertEqual(set(data), set(dd.DATASETS))
        for dataset, rows in data.items():
            self.assertTrue(rows, dataset)

    def test_placeholder_rows_carry_one_marker(self):
        rows = self.build()["pending"]
        self.assertEqual(rows, [{"key": dd.PLACEHOLDER_KEY, dd.PLACEHOLDER: True}])

    def test_real_rows_have_no_marker(self):
        self.write("knowledge/a.md", note("concept", "A"))
        self.assertNotIn(dd.PLACEHOLDER, self.build()["notes"][0])


class ContentTest(VaultCase):
    def test_note_fields(self):
        self.write("projects/demo/demo.md", note("project", "Demo", "## Goal\nShip it.\n\n## Status\nGoing.\n- [ ] first\n- [x] second\n"))
        row = self.build()["notes"][0]
        self.assertEqual((row["id"], row["type"], row["folder"], row["summary"], row["detail"]),
                         ("demo", "project", "projects", "Ship it.", "Going. first second"))
        self.assertEqual(row["open_tasks"], 1)

    def test_tasks_only_from_work_notes(self):
        self.write("projects/demo/demo.md", note("project", "Demo", "- [ ] first\n- [x] second\n"))
        self.write("knowledge/c.md", note("concept", "C", "- [ ] checklist item\n"))
        tasks = self.build()["tasks"]
        self.assertEqual([(t["task"], t["done"], t["project"]) for t in tasks], [("first", 0, "demo"), ("second", 1, "demo")])

    def test_log_entries_and_hidden_operations(self):
        self.write("log.md", "# Log\n\n## [2026-11-09] setup | Vault\n- Evidence: x\n\n## [2026-11-10] profile | Moved city\n- private detail\n")
        log = self.build()["log"]
        self.assertEqual([(r["date"], r["operation"]) for r in log], [("2026-11-09", "setup"), ("2026-11-10", "profile")])
        self.assertEqual(log[1]["detail"], "")
        self.assertNotIn("Moved city", json.dumps(log))

    def test_pending_status(self):
        self.write("inbox/pending.md", note("entry", "Pending", "## Open\n"
                   "- [ ] P-002 | question | 2026-11-09 | Which one? | [[a]] | chat: X | project: [[demo]]\n"
                   "- [ ] P-003 | on-hold | 2026-11-08 | Later | [[a]] | chat: X | ⏸ 2026-11-09: wait\n"
                   "## Closed\n- [x] P-001 | task | 2026-11-01 | Done thing | [[a]] | chat: X | ✔ 2026-11-02: ok\n"))
        rows = {r["id"]: r for r in self.build()["pending"]}
        self.assertEqual({k: (r["status"], r["kind"]) for k, r in rows.items()},
                         {"P-002": ("open", "question"), "P-003": ("held", "on-hold"), "P-001": ("done", "task")})
        self.assertEqual((rows["P-002"]["project"], rows["P-001"]["closed"]), ("demo", "2026-11-02"))

    def test_progress_entries(self):
        self.write("projects/demo/demo-progress.md", note("progress", "Demo — Progress", "## Log\n\n### 2026-11-09 — Start\n"
                   "- **Done:** the base\n- **Next step:** tests\n", project='"[[demo]]"'))
        rows = self.build()["progress"]
        self.assertEqual([(r["project"], r["date"], r["title"], r["label"], r["text"]) for r in rows],
                         [("demo", "2026-11-09", "Start", "Done", "the base"), ("demo", "2026-11-09", "Start", "Next step", "tests")])

    def test_broken_link(self):
        self.write("knowledge/a.md", note("concept", "A", "[[missing]] [[b]]"))
        self.write("knowledge/b.md", note("concept", "B", "[[a]]"))
        links = {(r["source"], r["target"]): r["broken"] for r in self.build()["links"]}
        self.assertEqual(links, {("a", "missing"): 1, ("a", "b"): 0, ("b", "a"): 0})

    def test_agent_runs_from_agent_page(self):
        self.write("knowledge/agents-log/agent-scout.md", note("concept", "Scout", "## Log\n"
                   "| Date | Mode | Model | Job | Result | Chat | Project |\n|---|---|---|---|---|---|---|\n"
                   "| 2026-11-09 | 1 | haiku | read files | worked | chat A | demo |\n"))
        run = self.build()["agent_runs"][0]
        self.assertEqual((run["agent"], run["date"], run["model"], run["result"], run["project"]),
                         ("scout", "2026-11-09", "haiku", "worked", "demo"))
        self.assertNotIn("chat", run)

    def test_meta_language(self):
        with mock.patch.object(dd.common, "LANGUAGE", "tr"):
            self.assertEqual(self.build()["meta"][0]["language"], "tr")


class TurkishNamesTest(VaultCase):
    names = TR_NAMES

    def test_turkish_folders_are_read_and_reported_by_base_name(self):
        self.write("projeler/demo/demo.md", note("project", "Demo", "## Hedef\nBitir.\n"))
        self.write("gelen/bekleyenler.md", note("entry", "Bekleyenler", "## Açık\n"
                   "- [ ] B-001 | question | 2026-11-09 | Hangisi? | [[a]] | sohbet: X\n## Kapananlar\n"))
        self.write("ben/profil.md", note("profile", "Profil", "özel"))
        self.write("gelen/oturumlar/k.md", note("session", "Kayıt"))
        data = self.build()
        notes = {r["id"]: r for r in data["notes"]}
        self.assertEqual(set(notes), {"demo", "bekleyenler"})
        self.assertEqual((notes["demo"]["folder"], notes["demo"]["summary"]), ("projects", "Bitir."))
        self.assertEqual(data["pending"][0]["id"], "B-001")
        self.assertEqual({r["key"]: r["value"] for r in data["counts"]}["sessions_waiting"], 1)

    def test_turkish_progress_heading(self):
        self.write("projeler/demo/demo-ilerleme.md", note("progress", "Demo", "## Günlük\n\n### 2026-11-09\n- **Yapıldı:** temel\n",
                                                          project='"[[demo]]"'))
        self.assertEqual(self.build()["progress"][0]["label"], "Yapıldı")


class WriteTest(VaultCase):
    def test_write_outputs_and_manifest(self):
        self.write("knowledge/a.md", note("concept", "A"))
        out = self.vault / "_system" / "output" / "dashboard"
        manifest = dd.write_outputs(self.build(), out)
        self.assertEqual(set(manifest), set(dd.DATASETS))
        self.assertEqual(json.loads((out / "manifest.json").read_text(encoding="utf-8")), manifest)
        self.assertEqual(json.loads((out / "notes.json").read_text(encoding="utf-8"))[0]["id"], "a")


class ReviewFixTest(VaultCase):
    SECRET = "sk-ant-abcdefghijklmnopqrstuvwx1234"  # secret-scan: allow (fake key on purpose)

    def test_every_text_field_passes_the_secret_scan(self):
        self.write("knowledge/a.md", note("concept", "A", tags=f"[{self.SECRET}]", aliases=f"[{self.SECRET}]"))
        self.write("councils/c.md", note("council", "C", agents=f"[{self.SECRET}]", mode=self.SECRET, result=self.SECRET))
        self.write("rules/general-rules.md", f"# Rules\n\n| # | Rule | Why |\n|---|---|---|\n| 1 | **{self.SECRET}.** {self.SECRET} | {self.SECRET} |\n")
        self.write("knowledge/agents-log/agent-scout.md", note("concept", "Scout", "| 2026-11-09 | " + " | ".join([self.SECRET] * 6) + " |\n"))
        self.write("_system/agents/scout.md", f"---\nname: scout\nmodel: {self.SECRET}\ncolor: {self.SECRET}\n---\n")
        self.assertNotIn(self.SECRET, json.dumps(self.build(), ensure_ascii=False))

    def test_extras_pass_the_secret_scan_too(self):
        data = dd.build_datasets(TODAY, extras={"health": [{"key": "k", "summary": self.SECRET}]})
        self.assertEqual(data["health"][0]["summary"], dd.HIDDEN_TEXT)

    def test_cost_rows_keep_no_folder_or_chat(self):
        row = {"key": "k", "kind": "session", "model": "m", "date": "2026-11-10", "cost_usd": 1.5,
               "folder": "-home-alice-notes", "chat": "private title", "agent": "scout", "input": 1, "output": 2}
        with mock.patch("cost.rows", return_value=[row]):
            self.assertEqual(dd.cost_rows(), [{"key": "k", "model": "m", "date": "2026-11-10", "cost_usd": 1.5}])

    def test_private_note_name_does_not_leak_through_pending(self):
        self.write("me/profile.md", note("profile", "Profile"))
        self.write("inbox/pending.md", note("entry", "Pending", "## Open\n- [ ] P-001 | question | 2026-11-09 | Ask | [[profile]] | chat: X | project: [[profile]]\n"))
        row = self.build()["pending"][0]
        self.assertEqual((row["source"], row["project"]), ("", ""))


if __name__ == "__main__":
    unittest.main()
