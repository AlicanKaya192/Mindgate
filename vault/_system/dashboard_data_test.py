"""dashboard_data.py tests. Each test builds a small vault in a new folder under _system/output/test_dashboard/ (outside git)
and never reads the real vault or the real transcripts; nothing is deleted (#22)."""
import contextlib
import io
import json
import tempfile
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
import dashboard_data as dd  # noqa: E402
import health  # noqa: E402
import session_mode as sm  # noqa: E402
from common_test import TR_NAMES  # noqa: E402

TEST_DIR = common.OUTPUT / "test_dashboard"
TODAY = "2026-11-10"
EN_NAMES = {"folders": {}, "files": {}}
SECRET = "sk-ant-abcdefghijklmnopqrstuvwx1234"  # secret-scan: allow (fake key on purpose)
CONTRACT_IDS = ("meta", "notes", "log", "versions", "links", "tasks", "counts", "progress", "weekly", "pending", "agents",
                "agent_runs", "expertise", "skills", "discoveries", "rules", "health", "handoff", "system", "cost",
                "councils")


def note(kind: str, title: str, body: str = "", **fields) -> str:
    extra = "".join(f"{k}: {v}\n" for k, v in fields.items())
    return f"---\ntype: {kind}\nstatus: active\n{extra}created: 2026-11-01\nupdated: 2026-11-02\n---\n\n# {title}\n\n{body}"


def table(header: str, *rows: str) -> str:
    columns = header.count("|") - 1
    return "\n".join([header, "|" + "---|" * columns, *rows]) + "\n"


def real_rows(rows: list[dict]) -> list[dict]:
    return [r for r in rows if not r.get(dd.PLACEHOLDER)]


class VaultCase(unittest.TestCase):
    names = EN_NAMES

    def setUp(self):
        TEST_DIR.mkdir(parents=True, exist_ok=True)
        self.vault = Path(tempfile.mkdtemp(prefix=self.id().rsplit(".", 1)[-1] + "-", dir=TEST_DIR))
        self.transcripts = self.vault.parent / f"{self.vault.name}.projects"
        patches = [mock.patch.object(common, "VAULT", self.vault), mock.patch.object(common, "NAMES", self.names),
                   mock.patch.object(sm, "FILE", self.vault / "_system" / "output" / "session_mode.json"),
                   mock.patch.object(dd, "TRANSCRIPTS", self.transcripts),
                   mock.patch.object(dd, "INSTALLED_SKILLS", self.vault.parent / f"{self.vault.name}.skills")]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def write(self, relative: str, text: str) -> None:
        path = self.vault / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))

    def build(self, trace: dict | None = None, extras: dict | None = None) -> dict:
        return dd.build_datasets(TODAY, extras=extras or {}, trace=trace)


class ContractTest(VaultCase):
    def test_dataset_ids_follow_the_contract(self):
        self.assertEqual(dd.DATASETS, CONTRACT_IDS)

    def test_meta_row(self):
        self.assertEqual(self.build()["meta"], [{"key": "meta", "language": common.LANGUAGE, "generated": TODAY}])

    def test_meta_language(self):
        with mock.patch.object(dd.common, "LANGUAGE", "tr"):
            self.assertEqual(self.build()["meta"][0]["language"], "tr")


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
        self.assertFalse(any(r["broken"] for r in real_rows(self.build()["links"])))

    def test_session_records_are_only_counted(self):
        counts = {r["key"]: r["value"] for r in self.build()["counts"]}
        self.assertEqual(counts["sessions_waiting"], 1)
        self.assertEqual(counts["private_notes"], 4)   # profile, CLAUDE, hidden idea, sensitive name

    def test_private_text_never_reaches_any_dataset(self):
        dump = json.dumps(self.build(), ensure_ascii=False)
        for text in ("secret life", "raw text", "Hidden idea", "Passwords"):
            self.assertNotIn(text, dump)

    def test_private_weekly_summary_stays_out(self):
        self.write("research/2026-11-10-weekly-summary.md", note("research", "Week", "## Added\n- hidden week\n", privacy="private"))
        self.assertNotIn("hidden week", json.dumps(self.build()["weekly"]))


class SecretTest(VaultCase):
    def test_secret_in_summary_is_hidden(self):
        self.write("knowledge/k.md", note("concept", "Key", f"## In one sentence\napi_key = {SECRET}\n"))
        row = self.build()["notes"][0]
        self.assertNotIn("sk-ant", row["summary"])
        self.assertEqual(row["summary"], dd.HIDDEN_TEXT)

    def test_secret_in_handoff_is_hidden(self):
        card = "## 2026-11-10 10:00 · Work · 0123abcd\npassword = hunter2hunter2\n"
        self.write("inbox/handoff.md", note("entry", "Handoff") + "\n" + card)
        row = self.build()["handoff"][0]
        self.assertNotIn("hunter2", row["text"])

    def test_extras_pass_the_secret_scan_too(self):
        data = self.build(extras={"health": [{"key": "k", "summary": SECRET}]})
        self.assertEqual(data["health"][0]["summary"], dd.HIDDEN_TEXT)


class EverySourceCase(VaultCase):
    """A vault where every source of every data set exists and every text cell holds the same `text`."""

    def fill(self, s: str) -> dict:
        self.write("knowledge/a.md", note("concept", s, f"## In one sentence\n{s}\n## In practice\n{s}\n[[{s}]]",
                                          tags=f"[{s}]", aliases=f"[{s}]"))
        self.write("projects/demo/demo.md", note("project", s, f"## Goal\n{s}\n## Status\n{s}\n- [ ] {s}\n"))
        self.write("projects/demo/demo-progress.md", note("progress", s, "## Version history\n"
                   + table("| Version | Date | Highlights |", f"| {s} | 2026-11-09 | {s} |")
                   + f"\n## Log\n### 2026-11-09 — {s}\n- **{s}:** {s}\n", project='"[[demo]]"'))
        self.write("projects/demo/demo-rules.md", note("rule", "Demo rules", "## Data\n"
                   + table("| # | Rule | Why | Added |", f"| 1 | **{s}.** {s} | {s} | 2026-11-09 |")))
        self.write("log.md", f"# Log\n\n## [2026-11-09] setup | {s}\n- {s}\n")
        self.write("research/2026-11-10-weekly-summary.md", note("research", s, f"## {s}\n- {s}\n"))
        self.write("inbox/pending.md", note("entry", "Pending", f"## Open\n- [ ] P-001 | {s} | 2026-11-09 | {s} | [[{s}]] "
                                                                f"| chat: {s} | project: [[{s}]]\n"))
        self.write("inbox/handoff.md", note("entry", "Handoff") + f"\n## 2026-11-10 10:00 · {s} · 0123abcd\n{s}\n")
        self.write("_system/agents/scout.md", f"---\nname: scout\ndescription: {s}\nmodel: {s}\neffort: {s}\ncolor: {s}\n"
                                              f"tools: {s}\ndisallowedTools: {s}\n---\n")
        self.write("knowledge/agents-log/agent-scout.md", note("concept", f"{s} — page", "## Log\n"
                   + table("| Date | Mode | Model | Job | Result | Chat | Project |", "| 2026-11-09 | " + " | ".join([s] * 6) + " |")))
        self.write("_system/skills/expert-ml/SKILL.md", f"---\nname: {s}\ndescription: {s}\n---\n\nIdea sources: {s}\n"
                                                        f"https://{s}.example/x\n\n## Lessons\n- 2026-11-09 {s}\n")
        self.write("_system/skills/skills-registry.md", table("| Pack | Field | Usage | Last used |", f"| `expert-ml` | {s} | 3 | {s} |"))
        self.write("knowledge/trending/trending-projects.md", note("entry", "Trending", table(
            "| Project | What | Goal | Use | Trend | License | First seen | Source |",
            f"| [{s}](https://example.com/{s}) | {s} | {s} | {s} | 1,200 ★ · 2026-11-01 | {s} | 2026-11-01 | {s} |")))
        self.write("ideas/project-proposals.md", note("entry", "Proposals", table(
            "| Date | Proposal | What | Goal | Use | Criteria | Difficulty | Requirements | First step | Source | Status |",
            "| 2026-11-09 | " + " | ".join([s] * 10) + " |")))
        self.write("ideas/rejected-proposals.md", note("idea", "Rejected", table(
            "| Date | Proposal | User's words | Reason | Chosen instead | Status |", "| 2026-11-09 | " + " | ".join([s] * 5) + " |")))
        self.write("rules/general-rules.md", "# Rules\n\n" + table("| # | Rule | Why |", f"| 1 | **{s}.** {s} | {s} |"))
        self.write("rules/rule-violations.md", note("rule", "Violations", table(
            "| Date | Rule | What happened | Root cause | Fix and safeguard | Noticed by | Chat |",
            "| 2026-11-09 | " + " | ".join([s] * 6) + " |")))
        self.write("rules/lesson-candidates.md", note("rule", "Lessons", "## Pending candidates\n\n"
                   + table("| Candidate lesson | Evidence | Suggested place | Date |", f"| {s} | {s} | {s} | 2026-11-09 |")))
        self.write("councils/2026-11-09-c.md", note("council", f"Council: {s}", f"## Summary\n{s}\n", mode=s,
                                                     agents=f"[{s}]", result=s, decision_note=f'"[[{s}]]"'))
        self.write("_system/a.py", f'"""{s}"""\n')
        statuses = {"daily": {"state": s, "started_at": s, "finished_at": s}}
        with mock.patch.object(health, "hook_states", return_value=[("Stop", s, True)]), \
                mock.patch("task_status.read_statuses", return_value=statuses):
            system = dd.system_rows()
        cost_row = {k: s for k in ("key", "kind", "model", "unpriced_models", "chat", "folder", "agent")}
        with mock.patch("cost.rows", return_value=[{**cost_row, "date": "2026-11-09", "input": 1, "output": 1,
                                                    "cache_read": 0, "cache_write": 0, "cost_usd": 1.0}]):
            cost_rows = dd.cost_rows()
        result = health.Result(s, s, s, s, s, s)
        with mock.patch.object(health, "checks", return_value=[result]):
            health_rows = dd.health_rows()
        trace = {"chats": {"abcd1234": {"title": s, "folder": s}},
                 "notes": {"a": {"first": ["2026-11-09T10:00", "abcd1234"], "last": ["2026-11-09T10:00", "abcd1234"]}},
                 "lines": {}}
        return self.build(trace=trace, extras={"health": health_rows, "system": system, "cost": cost_rows})


class EveryTextFieldTest(EverySourceCase):
    def test_a_secret_in_every_text_field_never_leaves(self):
        data = self.fill(SECRET)
        self.assertEqual([d for d, rows in data.items() if not real_rows(rows)], [])   # every data set was really built
        self.assertNotIn("sk-ant", json.dumps(data, ensure_ascii=False))

    def test_every_data_set_has_rows_when_every_source_exists(self):
        data = self.fill("plain text")
        self.assertEqual([d for d, rows in data.items() if not real_rows(rows)], [])
        self.assertEqual({r["id"]: r for r in data["notes"]}["a"]["chat"], "plain text")


class PlaceholderTest(VaultCase):
    def test_empty_vault_gives_no_empty_dataset(self):
        data = self.build()
        self.assertEqual(tuple(data), dd.DATASETS)
        for dataset, rows in data.items():
            self.assertTrue(rows, dataset)

    def test_placeholder_rows_carry_one_marker(self):
        for dataset in ("pending", "versions", "weekly", "discoveries", "councils"):
            self.assertEqual(self.build()[dataset], [{"key": dd.PLACEHOLDER_KEY, dd.PLACEHOLDER: True}], dataset)

    def test_real_rows_have_no_marker(self):
        self.write("knowledge/a.md", note("concept", "A"))
        self.assertNotIn(dd.PLACEHOLDER, self.build()["notes"][0])


class ContentTest(VaultCase):
    def test_note_fields(self):
        self.write("projects/demo/demo.md", note("project", "Demo", "## Goal\nShip it.\n\n## Status\nGoing.\n- [ ] first\n- [x] second\n"))
        row = self.build()["notes"][0]
        self.assertEqual((row["id"], row["type"], row["folder"], row["summary"], row["detail"]),
                         ("demo", "project", "projects", "Ship it.", "Going. first second"))
        self.assertEqual((row["open_tasks"], row["chat"], row["chat_last"]), (1, "", ""))

    def test_tasks_only_from_work_notes(self):
        self.write("projects/demo/demo.md", note("project", "Demo", "- [ ] first\n- [x] second\n"))
        self.write("knowledge/c.md", note("concept", "C", "- [ ] checklist item\n"))
        tasks = self.build()["tasks"]
        self.assertEqual([(t["task"], t["done"], t["project"], t["chat"]) for t in tasks],
                         [("first", 0, "demo", ""), ("second", 1, "demo", "")])

    def test_log_entries_and_hidden_operations(self):
        self.write("log.md", "# Log\n\n## [2026-11-09] setup | Vault\n- Evidence: x\n\n## [2026-11-10] profile | Moved city\n- private detail\n")
        log = self.build()["log"]
        self.assertEqual([(r["key"], r["no"], r["date"], r["operation"]) for r in log],
                         [("1", 1, "2026-11-09", "setup"), ("2", 2, "2026-11-10", "profile")])
        self.assertEqual(log[1]["detail"], "")
        self.assertNotIn("Moved city", json.dumps(log))

    def test_log_project_from_a_linked_note_with_a_project(self):
        self.write("projects/demo/demo.md", note("project", "Demo"))
        self.write("projects/demo/demo-progress.md", note("progress", "Demo progress", project='"[[demo]]"'))
        self.write("log.md", "# Log\n\n## [2026-11-09] progress | Step\n- see [[demo-progress]]\n")
        self.assertEqual(self.build()["log"][0]["project"], "demo")

    def test_versions_from_the_progress_note(self):
        self.write("projects/demo/demo-progress.md", note("progress", "Demo", "## Version history\n"
                   + table("| Version | Date | Highlights |", "| **v1.0** | 2026-11-09 | first [[release]] |", "| v0.9 | soon | x |")
                   + "\n## Log\n", project='"[[demo]]"'))
        self.assertEqual(self.build()["versions"], [{"key": "demo:v1.0", "project": "demo", "version": "v1.0",
                                                     "date": "2026-11-09", "summary": "first release"}])

    def test_weekly_summary_takes_the_newest_file(self):
        self.write("research/2026-11-03-weekly-summary.md", note("research", "Old", "## Added\n- old item\n"))
        self.write("research/2026-11-10-weekly-summary.md", note("research", "New", "## Added\n- one\n- **two**\n\n## Health\nAll fine.\n"))
        self.assertEqual(self.build()["weekly"], [
            {"key": "2026-11-10:0", "date": "2026-11-10", "section": "Added", "text": "one • two", "order": 0},
            {"key": "2026-11-10:1", "date": "2026-11-10", "section": "Health", "text": "All fine.", "order": 1}])

    def test_counts_hold_every_contract_name(self):
        self.write("sources/paper.pdf", "x")
        self.write("sources/used.pdf", "x")
        self.write("sources/assets/image.png", "x")
        self.write("knowledge/summary.md", note("source", "Summary", source_file="sources/used.pdf"))
        self.write("rules/lesson-candidates.md", note("rule", "Lessons", "## Pending candidates\n\n"
                   + table("| Candidate lesson | Evidence | Suggested place | Date |", "| a | b | c | 2026-11-09 |", "| d | e | f | 2026-11-09 |")
                   + "\n## Rejected\n"))
        self.write("research/2026-11-10-weekly-summary.md", note("research", "Week", "## Quiz\n- Memory quiz: **13.5/15**\n"))
        self.write("log.md", "# Log\n\n## [2026-11-08] lint | Weekly\n- x\n")
        counts = {r["key"]: (r["value"], r["text"]) for r in self.build()["counts"]}
        self.assertEqual(list(counts), ["sessions_waiting", "sources_waiting", "stale_active", "private_notes",
                                        "last_maintenance", "quiz_score", "lesson_candidates_waiting", "data_date"])
        self.assertEqual((counts["sources_waiting"][0], counts["lesson_candidates_waiting"][0]), (1, 2))
        self.assertEqual((counts["quiz_score"][1], counts["last_maintenance"][1], counts["data_date"][1]),
                         ("13.5/15", "2026-11-08", TODAY))

    def test_pending_status(self):
        self.write("inbox/pending.md", note("entry", "Pending", "## Open\n"
                   "- [ ] P-002 | question | 2026-11-09 | Which one? | [[a]] | chat: X | project: [[demo]]\n"
                   "- [ ] P-003 | on-hold | 2026-11-08 | Later | [[a]] | chat: X | ⏸ 2026-11-09: wait\n"
                   "## Closed\n- [x] P-001 | task | 2026-11-01 | Done thing | [[a]] | chat: X | ✔ 2026-11-02: ok\n"))
        rows = {r["id"]: r for r in self.build()["pending"]}
        self.assertEqual({k: (r["status"], r["kind"]) for k, r in rows.items()},
                         {"P-002": ("open", "question"), "P-003": ("held", "on-hold"), "P-001": ("done", "task")})
        self.assertEqual((rows["P-002"]["project"], rows["P-001"]["closed"], rows["P-002"]["chat"]), ("demo", "2026-11-02", "X"))

    def test_pending_project_from_the_source_note_and_archive(self):
        self.write("projects/demo/demo-progress.md", note("progress", "Demo", project='"[[demo]]"'))
        self.write("inbox/pending.md", note("entry", "Pending", "## Open\n- [ ] P-002 | task | 2026-11-09 | Do | [[demo-progress]] | chat: X\n"))
        self.write("archive/pending/pending-2026-10.md", note("entry", "Archive", "- [x] P-001 | task | 2026-10-01 | Old | [[a]] | chat: Y | ✔ 2026-10-02 (ok)\n"))
        rows = {r["id"]: r for r in self.build()["pending"]}
        self.assertEqual((rows["P-002"]["project"], rows["P-001"]["status"], rows["P-001"]["closed"]), ("demo", "done", "2026-10-02"))

    def test_progress_entries(self):
        self.write("projects/demo/demo-progress.md", note("progress", "Demo — Progress", "## Log\n\n### 2026-11-09 — Start\n"
                   "- **Done:** the base\n- **Next step:** tests\n", project='"[[demo]]"'))
        rows = self.build()["progress"]
        self.assertEqual([(r["project"], r["date"], r["title"], r["label"], r["text"], r["chat"]) for r in rows],
                         [("demo", "2026-11-09", "Start", "Done", "the base", ""), ("demo", "2026-11-09", "Start", "Next step", "tests", "")])

    def test_broken_link(self):
        self.write("knowledge/a.md", note("concept", "A", "[[missing]] [[b]]"))
        self.write("knowledge/b.md", note("concept", "B", "[[a]]"))
        links = {(r["source"], r["target"]): r["broken"] for r in self.build()["links"]}
        self.assertEqual(links, {("a", "missing"): 1, ("a", "b"): 0, ("b", "a"): 0})

    def test_handoff_rows_carry_their_order(self):
        self.write("inbox/handoff.md", note("entry", "Handoff") + "\n## 2026-11-10 10:00 · Work · 0123abcd\nnew\n"
                   "\n## 2026-11-09 09:00 · Old · 4567abcd\nold\n")
        rows = self.build()["handoff"]
        self.assertEqual([(r["label"], r["session"], r["order"]) for r in rows], [("Work", "0123abcd", 0), ("Old", "4567abcd", 1)])

    def test_council_fields(self):
        self.write("councils/2026-11-09-plan.md", note("council", "Council: Plan the release", "## Summary\nShip it.\n",
                   mode="2", agents="[advisor, hater]", result="passed", calls="4", opus="1", project='"[[demo]]"',
                   decision_note='"[[demo-adr-001]]"'))
        self.assertEqual(self.build()["councils"], [{
            "key": "2026-11-09-plan", "id": "2026-11-09-plan", "date": "2026-11-01", "job": "Plan the release", "mode": "2",
            "agents": "advisor, hater", "result": "passed", "calls": 4, "opus": 1, "project": "demo",
            "decision_note": "demo-adr-001", "summary": "Ship it."}])


class AgentTest(VaultCase):
    def setUp(self):
        super().setUp()
        self.write("_system/agents/scout.md", "---\nname: scout\ndescription: Read-only agent (Level 1). Reads.\n"
                   "tools: Read, Skill\ndisallowedTools: Write\nmodel: haiku\neffort: low\nskills:\n  - scouting-method\n"
                   "color: cyan\n---\n\nUse `debugging` when stuck.\n")
        self.write("_system/agents/maintainer.md", "---\nname: maintainer\ndescription: Upkeep.\ntools: Read\n---\n\nUse `debugging`.\n")
        self.write("knowledge/agents-log/agent-scout.md", note("concept", "Scout — reads files", "## Log\n" + table(
            "| Date | Mode | Model | Job | Result | Chat | Project |",
            "| 2026-11-09 | 1 | Haiku | read files | worked | chat A | [[demo]] |",
            "| 2026-11-10 | 1 | haiku | read | partly | — | — |",
            "| 2026-11-08 | 2 | haiku | read | unnecessary | — | — |",
            "| 2026-11-07 | 2 | haiku | read | upgraded to opus | — | — |")))

    def test_agent_runs_from_agent_page(self):
        run = self.build()["agent_runs"][0]
        self.assertEqual((run["agent"], run["date"], run["mode"], run["model"], run["job"], run["result"], run["chat"], run["project"]),
                         ("scout", "2026-11-09", "1", "haiku", "read files", "worked", "chat A", "demo"))

    def test_agent_rows_with_statistics(self):
        agents = {r["key"]: r for r in self.build()["agents"]}
        self.assertEqual(list(agents), ["central", "maintainer", "scout"])
        scout = agents["scout"]
        self.assertEqual({k: scout[k] for k in ("name", "display", "model", "effort", "color", "level", "tools", "denied", "page",
                                                "total", "worked", "partly", "unnecessary", "upgraded", "last_date")},
                         {"name": "scout", "display": "Scout", "model": "haiku", "effort": "low", "color": "cyan", "level": "1",
                          "tools": "Read, Skill", "denied": "Write", "page": "agent-scout", "total": 4, "worked": 1,
                          "partly": 1, "unnecessary": 1, "upgraded": 1, "last_date": "2026-11-10"})
        self.assertEqual((agents["maintainer"]["model"], agents["maintainer"]["total"], agents["central"]["total"]), ("inherit", 0, 4))

    def test_turkish_results_are_counted(self):
        self.write("knowledge/agents-log/agent-scout.md", note("concept", "Scout", "## Günlük\n" + table(
            "| Tarih | Mod | Model | İş | Sonuç | Sohbet | Proje |", "| 2026-11-09 | 1 | haiku | oku | İşe yaradı | — | — |",
            "| 2026-11-09 | 1 | haiku | oku | kısmen | — | — |")))
        scout = {r["key"]: r for r in self.build()["agents"]}["scout"]
        self.assertEqual((scout["worked"], scout["partly"]), (1, 1))

    def test_expertise_rows(self):
        self.write("_system/skills/expert-ml/SKILL.md", "---\nname: expert-ml\ndescription: Data leakage. Metrics.\n---\n\n"
                   "## Lessons\n<!-- comment -->\n- 2026-11-01 — split first\n- keep a seed\n")
        self.assertEqual(self.build()["expertise"], [{"key": "expert-ml", "name": "expert-ml", "description": "Data leakage",
                                                      "lessons": 2, "last_lesson": "2026-11-01",
                                                      "lesson_text": "2026-11-01 — split first • keep a seed"}])

    def test_skill_rows(self):
        self.write("_system/skills/scouting-method/SKILL.md", "---\nname: scouting-method\ndescription: How to scout. More.\n---\n\n"
                   "See https://github.com/owner/repo/tree/main and https://claude.ai/x.\n\n## Idea sources\n"
                   "- obra/superpowers `systematic-debugging` (MIT, Jesse Vincent).\n\n## Lessons\n- 2026-11-02 a\n")
        self.write("_system/skills/debugging/SKILL.md", "---\nname: debugging\ndescription: Root cause first.\n---\n")
        self.write("_system/skills/idea/SKILL.md", "---\nname: idea\ndescription: Save an idea.\n---\n")
        self.write("_system/skills/expert-ml/SKILL.md", "---\nname: expert-ml\ndescription: ML.\n---\n")
        self.write("_system/skills/skills-registry.md", table("| Skill | What it does | Usage | Last used | Last error |",
                                                             "| `/idea` | Save it | 3 | 2026-11-09 | — |")
                   + "\n### Method skills\n" + table("| Skill | Agent | What | Usage | Last used |",
                                                     "| `debugging` | main chat | No fix first | 2 | — |"))
        (dd.INSTALLED_SKILLS / "idea").mkdir(parents=True, exist_ok=True)
        (dd.INSTALLED_SKILLS / "idea" / "SKILL.md").write_bytes(b"x")
        skills = {r["key"]: r for r in self.build()["skills"]}
        self.assertEqual({k: (r["kind"], r["command"]) for k, r in skills.items()},
                         {"debugging": ("method", "/debugging"), "expert-ml": ("expertise", "/expert-ml"),
                          "idea": ("workflow", "/idea"), "scouting-method": ("method", "/scouting-method")})
        self.assertEqual((skills["idea"]["what"], skills["idea"]["uses"], skills["idea"]["last_used"], skills["idea"]["installed"]),
                         ("Save it", 3, "2026-11-09", 1))
        self.assertEqual((skills["debugging"]["what"], skills["debugging"]["last_used"], skills["debugging"]["can_load"]),
                         ("No fix first", "", "scout"))
        method = skills["scouting-method"]
        self.assertEqual((method["what"], method["preloaded"], method["sources"], method["lessons"], method["last_lesson"],
                          method["installed"]),
                         ("How to scout", "scout", "owner/repo, obra/superpowers", 1, "2026-11-02", 0))
        self.assertEqual(method["lines"], 12)


class DiscoveryTest(VaultCase):
    def test_trending_row(self):
        self.write("knowledge/trending/trending-projects.md", note("entry", "Trending", table(
            "| Project | What | Goal | Use | Trend | License | First seen | Source |",
            "| [tool](https://github.com/o/tool) | a **tool** | goal | use | 12.3k ★ · 2026-11-01; 13.5k ★ · 2026-11-08 (unverified) "
            "| MIT | 2026-11-01 | GitHub Trending (weekly) |")))
        row = self.build()["discoveries"][0]
        self.assertEqual({k: row[k] for k in ("key", "kind", "name", "url", "what", "stars", "rating", "unverified", "movement",
                                              "trending", "license", "date", "source")},
                         {"key": "trending#0", "kind": "trending", "name": "tool", "url": "https://github.com/o/tool",
                          "what": "a tool", "stars": 13500, "rating": "high", "unverified": 1,
                          "movement": "+1,200 ★ (7 days, ~171/day)", "trending": "13.5k ★ · 2026-11-08 (unverified)",
                          "license": "MIT", "date": "2026-11-01", "source": "GitHub Trending (weekly)"})

    def test_turkish_star_format_and_single_measure(self):
        self.write("knowledge/trending/trending-projects.md", note("entry", "Gündem", table(
            "| Proje | Ne | Hedef | Fayda | Gündem | Lisans | İlk görülme | Kaynak |",
            "| araç | ne | hedef | fayda | 298,1 bin ★ · 2026-10-12 | MIT | 2026-10-12 | GitHub |")))
        row = self.build()["discoveries"][0]
        self.assertEqual((row["stars"], row["rating"], row["movement"], row["unverified"]),
                         (298100, "very_high", "single measure; growth not known yet", 0))

    def test_proposal_and_rejected_rows(self):
        self.write("ideas/project-proposals.md", note("entry", "Proposals", table(
            "| Date | Proposal | What | Goal | Use | Criteria | Difficulty | Requirements | First step | Source | Status |",
            "| 2026-11-09 | Weather bot | a bot | alerts | learn | ✓ ✓ ✓ ✗ | medium | Python | read the API | [[a]] | proposed |")))
        self.write("ideas/rejected-proposals.md", note("idea", "Rejected", table(
            "| Date | Proposal | User's words | Reason | Chosen instead | Status |",
            "| 2026-11-08 | Chat app | not now | no time | the bot | rejected |")))
        rows = {r["kind"]: r for r in self.build()["discoveries"]}
        proposal, rejected = rows["proposal"], rows["rejected"]
        self.assertEqual((proposal["name"], proposal["rating"], proposal["criteria"], proposal["needs"], proposal["first_step"],
                          proposal["source"], proposal["status"]),
                         ("Weather bot", "medium", "✓ ✓ ✓ ✗", "Python", "read the API", "a", "proposed"))
        self.assertEqual((rejected["key"], rejected["name"], rejected["words"], rejected["reason"], rejected["instead"], rejected["status"]),
                         ("rejected#0", "Chat app", "not now", "no time", "the bot", "rejected"))


class RuleTest(VaultCase):
    def test_general_project_and_violation_rows(self):
        self.write("rules/general-rules.md", "# Rules\n\n" + table("| # | Rule | Why |", "| 1 | **Ask first.** Then act. | Safety |")
                   + "\n## Optional rules\n" + table("| # | Rule | Why |", "| 9 | Usage limit. Stay below it. | Cost |"))
        self.write("projects/demo/demo-rules.md", note("rule", "Demo rules", "## Data\n"
                   + table("| # | Rule | Why | Added |", "| 2 | Units in names. | Clarity | 2026-11-01 |")))
        self.write("rules/rule-violations.md", note("rule", "Violations", table(
            "| Date | Rule | What happened | Root cause | Fix and safeguard | Noticed by | Chat |",
            "| 2026-11-09 | #22 | deleted a file | hurry | asked first | user | chat A |")))
        rows = {r["key"]: r for r in self.build()["rules"]}
        self.assertEqual(list(rows), ["general#1", "general#9", "demo#2", "violation#0"])
        self.assertEqual((rows["general#1"]["title"], rows["general#1"]["text"], rows["general#1"]["why"], rows["general#1"]["kind"]),
                         ("Ask first", "Then act.", "Safety", "rule"))
        self.assertEqual((rows["general#9"]["section"], rows["general#9"]["title"], rows["general#9"]["text"]),
                         ("Optional rules", "Usage limit", "Stay below it."))
        self.assertEqual((rows["demo#2"]["source"], rows["demo#2"]["section"], rows["demo#2"]["date"], rows["demo#2"]["number"]),
                         ("demo", "Data", "2026-11-01", 2))
        violation = rows["violation#0"]
        self.assertEqual((violation["kind"], violation["number"], violation["rule"], violation["text"], violation["why"],
                          violation["fix"], violation["noticed_by"], violation["chat"]),
                         ("violation", 22, "#22", "deleted a file", "hurry", "asked first", "user", "chat A"))


class ExtrasTest(VaultCase):
    def test_health_rows(self):
        results = [health.Result("hooks", "Hooks", "ok", "fine", "d", "a", 3), health.Result("x", "X", "warning", "s")]
        with mock.patch.object(health, "checks", return_value=results):
            rows = dd.health_rows()
        self.assertEqual(rows[0], {"key": "hooks", "check": "Hooks", "status": "ok", "summary": "fine", "details": "d",
                                   "advice": "a", "count": 3, "order": 0})
        self.assertEqual(rows[1]["order"], 1)

    def test_system_rows(self):
        self.write("_system/tool.py", '"""Does a thing.\n\nMore."""\nimport os\n')
        self.write("_system/tool_test.py", "import tool\n")
        self.write("_system/helper.py", "x = 1\n")
        self.write("_system/other_test.py", "import helper\n")
        self.write("_system/run_tests.py", '"""Runs the tests."""\n')
        self.write("rules/lesson-candidates.md", note("rule", "L", "## Pending candidates\n\n"
                   + table("| Candidate lesson | Evidence | Suggested place | Date |", "| Check twice | [[a]] | rules | 2026-11-09 |")))
        self.write("research/2026-11-08-weekly-summary.md", note("research", "Week"))
        statuses = {"daily": {"state": "done", "started_at": "2026-11-10T08:00:00", "finished_at": "2026-11-10T08:10:00"}}
        with mock.patch.object(health, "hook_states", return_value=[("Stop", "context_check.py", True), ("Stop", "x.py", False)]), \
                mock.patch("task_status.read_statuses", return_value=statuses):
            rows = {r["key"]: r for r in dd.system_rows()}
        tool = rows["tool:tool.py:"]
        self.assertEqual((tool["what"], tool["lines"], tool["test"], tool["evidence"], tool["status"]),
                         ("Does a thing.", 4, 1, "tool_test.py", ""))
        self.assertEqual((rows["tool:helper.py:"]["test"], rows["tool:helper.py:"]["evidence"]), (1, "other_test.py"))
        self.assertEqual(rows["tool:run_tests.py:"]["status"], "runner")
        self.assertEqual((rows["hook:context_check.py:Stop"]["status"], rows["hook:x.py:Stop"]["status"]), ("installed", "missing"))
        self.assertTrue(rows["hook:context_check.py:Stop"]["what"])
        self.assertEqual((rows["task:daily:"]["status"], rows["task:daily:"]["finished"]), ("done", "2026-11-10T08:10:00"))
        self.assertEqual((rows["task:weekly:"]["status"], rows["task:weekly:"]["finished"]), ("done", "2026-11-08"))
        candidate = rows["lesson_candidate:candidate-1:#1"]
        self.assertEqual((candidate["what"], candidate["evidence"], candidate["place"], candidate["date"]),
                         ("Check twice", "a", "rules", "2026-11-09"))
        self.assertEqual([r["order"] for r in rows.values()], list(range(len(rows))))

    def test_unreadable_settings_give_unknown_hooks(self):
        with mock.patch.object(health, "hook_states", side_effect=ValueError("bad")), \
                mock.patch("task_status.read_statuses", return_value={}):
            hooks = [r for r in dd.system_rows() if r["kind"] == "hook"]
        self.assertEqual(len(hooks), len(health.EXPECTED_HOOKS))
        self.assertEqual({r["status"] for r in hooks}, {"unknown"})

    def test_cost_rows_follow_the_contract(self):
        old = {"key": "k1", "kind": "session", "model": "m", "date": "2026-11-09", "cost_usd": 1.5, "folder": "notes",
               "chat": "title", "agent": "", "input": 1, "output": 2, "cache_read": 3, "cache_write": 4, "unpriced_models": ""}
        running = {**old, "key": "k2", "date": "9999-01-01"}
        with mock.patch("cost.rows", return_value=[old, running]):
            self.assertEqual(dd.cost_rows(), [{**old, "order": 0}])


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
        self.assertEqual((data["pending"][0]["id"], data["pending"][0]["chat"]), ("B-001", "X"))
        self.assertEqual({r["key"]: r["value"] for r in data["counts"]}["sessions_waiting"], 1)

    def test_turkish_progress_heading_and_versions(self):
        self.write("projeler/demo/demo-ilerleme.md", note("progress", "Demo", "## Sürüm geçmişi\n"
                   + table("| Sürüm | Tarih | Öne çıkanlar |", "| v1 | 2026-11-09 | ilk |")
                   + "\n## Günlük\n\n### 2026-11-09\n- **Yapıldı:** temel\n", project='"[[demo]]"'))
        data = self.build()
        self.assertEqual(data["progress"][0]["label"], "Yapıldı")
        self.assertEqual((data["versions"][0]["version"], data["versions"][0]["summary"]), ("v1", "ilk"))

    def test_turkish_files_of_the_other_data_sets(self):
        self.write("arastirmalar/2026-11-10-haftalik-ozet.md", note("research", "Hafta", "## Eklenenler\n- bir\n"))
        self.write("kurallar/genel-kurallar.md", "# Kurallar\n\n" + table("| # | Kural | Neden |", "| 1 | **Önce sor.** Sonra yap. | Güvenlik |"))
        self.write("kurallar/kural-ihlalleri.md", note("rule", "İhlaller", table(
            "| Tarih | Kural | Ne oldu | Kök neden | Düzeltme | Fark eden | Sohbet |", "| 2026-11-09 | #22 | sildi | acele | sordu | kullanıcı | X |")))
        self.write("projeler/demo/demo-kurallar.md", note("rule", "Demo kuralları", table("| # | Kural | Neden |", "| 1 | Birim yaz. | Açıklık |")))
        self.write("fikirler/proje-onerileri.md", note("entry", "Öneriler", table(
            "| Tarih | Öneri | Ne | Hedef | Fayda | Ölçütler | Zorluk | Gerekenler | İlk adım | Kaynak | Durum |",
            "| 2026-11-09 | Bot | bot | uyarı | öğren | ✓ ✓ ✓ ✓ | orta | Python | oku | x | öneri |")))
        self.write("bilgi/gundem/gundemdeki-projeler.md", note("entry", "Gündem", table(
            "| Proje | Ne | Hedef | Fayda | Gündem | Lisans | İlk görülme | Kaynak |", "| araç | ne | h | f | 1.500 ★ · 2026-11-01 | MIT | 2026-11-01 | G |")))
        self.write("_sistem/ajanlar/kasif.md", "---\nname: kasif\ndescription: Okur (Seviye 1).\nmodel: haiku\n---\n")
        self.write("bilgi/ajanlar/ajan-kasif.md", note("concept", "Kaşif — okur", "## Günlük\n" + table(
            "| Tarih | Mod | Model | İş | Sonuç | Sohbet | Proje |", "| 2026-11-09 | 1 | haiku | oku | işe yaradı | X | — |")))
        self.write("_sistem/beceriler/temiz-kod/SKILL.md", "---\nname: temiz-kod\ndescription: Temiz kod.\n---\n")
        self.write("_sistem/beceriler/beceriler.md", "### Yöntem becerileri\n" + table(
            "| Beceri | Ajan | Ne | Kullanım | Son kullanım |", "| `temiz-kod` | hepsi | Kurallar | 5 | 2026-11-09 |"))
        data = self.build()
        self.assertEqual(data["weekly"][0]["text"], "bir")
        self.assertEqual([r["key"] for r in data["rules"]], ["general#1", "demo#1", "violation#0"])
        self.assertEqual({r["kind"]: r["rating"] for r in data["discoveries"]}, {"trending": "medium", "proposal": "high"})
        kasif = {r["key"]: r for r in data["agents"]}["kasif"]
        self.assertEqual((kasif["display"], kasif["level"], kasif["worked"]), ("Kaşif", "1", 1))
        skill = data["skills"][0]
        self.assertEqual((skill["kind"], skill["what"], skill["uses"]), ("method", "Kurallar", 5))


class ChatTraceTest(VaultCase):
    def transcript(self, sid: str, *lines: dict, newline: bool = True) -> Path:
        path = self.transcripts / "project" / f"{sid}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        old = path.read_bytes() if path.is_file() else b""
        text = "\n".join(json.dumps(line, ensure_ascii=False) for line in lines) + ("\n" if newline else "")
        path.write_bytes(old + text.encode("utf-8"))
        return path

    def title(self, sid: str, title: str) -> dict:
        return {"type": "custom-title", "customTitle": title, "sessionId": sid}

    def tool(self, sid: str, tool: str, stamp: str, **tool_input) -> dict:
        return {"type": "assistant", "sessionId": sid, "cwd": str(self.vault), "timestamp": stamp,
                "message": {"content": [{"type": "tool_use", "name": tool, "input": tool_input}]}}

    def vault_file(self, relative: str) -> str:
        return str(self.vault / relative)

    def test_note_gets_the_chat_that_opened_it_and_the_last_one(self):
        self.write("projects/demo/demo.md", note("project", "Demo", "- [ ] write the tests today\n"))
        self.transcript("aaaa1111-x", self.title("aaaa1111-x", "First chat"),
                        self.tool("aaaa1111-x", "Write", "2026-11-09T10:00:00Z", file_path=self.vault_file("projects/demo/demo.md"),
                                  content="# Demo\n- [ ] write the tests today\n"))
        self.transcript("bbbb2222-y", self.title("bbbb2222-y", "Second chat"),
                        self.tool("bbbb2222-y", "Edit", "2026-11-09T11:00:00Z", file_path=self.vault_file("projects/demo/demo.md"),
                                  old_string="# Demo", new_string="# Demo\n"))
        data = self.build(trace=dd.update_chat_trace(save=False))
        row = data["notes"][0]
        self.assertEqual((row["chat"], row["chat_last"]), ("First chat", "Second chat"))
        self.assertEqual(data["tasks"][0]["chat"], "First chat")

    def test_log_line_written_by_a_command(self):
        self.write("log.md", "# Log\n\n## [2026-11-09] setup | Vault ready\n- x\n")
        self.transcript("cccc3333-z", self.title("cccc3333-z", "Setup chat"),
                        self.tool("cccc3333-z", "PowerShell", "2026-11-09T10:00:00Z",
                                  command='Add-Content log.md "## [2026-11-09] setup | Vault ready"'))
        self.assertEqual(self.build(trace=dd.update_chat_trace(save=False))["log"][0]["chat"], "Setup chat")

    def test_unrecorded_chat_is_not_traced(self):
        self.write("knowledge/a.md", note("concept", "A"))
        sm.set_mode("dddd4444-full", sm.UNRECORDED)
        self.transcript("dddd4444-full", self.title("dddd4444-full", "Hidden chat"),
                        self.tool("dddd4444-full", "Write", "2026-11-09T10:00:00Z", file_path=self.vault_file("knowledge/a.md"), content="x"))
        trace = dd.update_chat_trace(save=False)
        self.assertEqual(trace["chats"], {})
        self.assertNotIn("Hidden chat", json.dumps(self.build(trace=trace)))

    def test_trace_of_a_chat_marked_unrecorded_later_is_not_shown(self):
        self.write("knowledge/a.md", note("concept", "A"))
        sm.set_mode("eeee5555-full", sm.UNRECORDED)
        trace = {"chats": {"eeee5555": {"title": "Later hidden", "folder": "f"}}, "lines": {},
                 "notes": {"a": {"first": ["2026-11-09T10:00", "eeee5555"], "last": ["2026-11-09T10:00", "eeee5555"]}}}
        self.assertEqual(self.build(trace=trace)["notes"][0]["chat"], "")

    def test_private_files_are_not_traced(self):
        self.transcript("ffff6666-a", self.title("ffff6666-a", "Chat"),
                        *[self.tool("ffff6666-a", "Write", "2026-11-09T10:00:00Z", file_path=self.vault_file(p), content="- a private line here")
                          for p in ("me/profile.md", "CLAUDE.md", "inbox/sessions/s.md", "knowledge/my-secret-notes.md", "knowledge/ok.md")])
        trace = dd.update_chat_trace(save=False)
        self.assertEqual(set(trace["notes"]), {"ok"})

    def test_a_note_marked_private_is_not_traced(self):
        self.write("ideas/zzhididea.md", note("idea", "Hidden", privacy="private"))
        self.transcript("fefe6666-a", self.title("fefe6666-a", "Chat"),
                        self.tool("fefe6666-a", "Write", "2026-11-09T10:00:00Z", file_path=self.vault_file("ideas/zzhididea.md"),
                                  content="- a private line here"))
        dd.update_chat_trace(save=True)
        self.assertNotIn("zzhid", (self.vault / "_system" / "chat_trace.json").read_text(encoding="utf-8"))

    def test_secret_in_a_chat_title_is_hidden(self):
        self.transcript("abab7777-a", self.title("abab7777-a", f"token {SECRET}"),
                        self.tool("abab7777-a", "Write", "2026-11-09T10:00:00Z", file_path=self.vault_file("knowledge/a.md"), content="x"))
        trace = dd.update_chat_trace(save=False)
        self.assertEqual(trace["chats"]["abab7777"]["title"], dd.HIDDEN_TEXT)

    def test_only_chats_that_write_to_the_vault_are_kept(self):
        other = {**self.title("baba1111-a", "Unrelated chat"), "cwd": "D:/work/other-project"}
        self.transcript("baba1111-a", other)
        self.transcript("baba2222-b", self.title("baba2222-b", "Vault chat"),
                        self.tool("baba2222-b", "Write", "2026-11-09T10:00:00Z", file_path=self.vault_file("knowledge/a.md"), content="x"))
        trace = dd.update_chat_trace(save=True)
        saved = (self.vault / "_system" / "chat_trace.json").read_text(encoding="utf-8")
        self.assertEqual(set(trace["chats"]), {"baba2222"})
        self.assertNotIn("Unrelated chat", saved)
        self.assertNotIn("other-project", saved)

    def test_title_read_before_the_chat_writes_is_kept(self):
        self.transcript("acac3333-a", self.title("acac3333-a", "Late writer"))
        dd.update_chat_trace(save=True)
        saved = (self.vault / "_system" / "chat_trace.json").read_text(encoding="utf-8")
        self.assertNotIn("Late writer", saved)
        self.transcript("acac3333-a",   # appended: the title line was read in the run before
                        self.tool("acac3333-a", "Write", "2026-11-09T10:00:00Z", file_path=self.vault_file("knowledge/a.md"), content="x"))
        trace = dd.update_chat_trace(save=True)
        self.assertEqual(trace["chats"]["acac3333"]["title"], "Late writer")

    def save_trace_of_one_chat(self) -> None:
        trace = {"chats": {"cdcd1111": {"title": "Saved chat", "folder": ""}}, "lines": {},
                 "notes": {"a": {"first": ["2026-11-09T10:00", "cdcd1111"], "last": ["2026-11-09T10:00", "cdcd1111"]}}}
        self.write("_system/chat_trace.json", json.dumps(trace))

    def test_broken_position_file_keeps_the_saved_trace(self):
        self.save_trace_of_one_chat()
        self.write("_system/output/chat_trace_position.json", "{broken")
        self.transcript("cdcd2222-b", self.title("cdcd2222-b", "New chat"),
                        self.tool("cdcd2222-b", "Write", "2026-11-09T11:00:00Z", file_path=self.vault_file("knowledge/b.md"), content="x"))
        trace = dd.chat_trace(save=True)
        self.assertEqual({sid: chat["title"] for sid, chat in trace["chats"].items()},
                         {"cdcd1111": "Saved chat", "cdcd2222": "New chat"})

    def test_position_that_is_not_a_whole_number_reads_from_the_start(self):
        path = self.transcript("cece3333-c", self.title("cece3333-c", "Chat"),
                               self.tool("cece3333-c", "Write", "2026-11-09T10:00:00Z", file_path=self.vault_file("knowledge/a.md"), content="x"))
        for bad in ("abc", None, 1.5, -3, True):
            with self.subTest(position=bad):
                self.write("_system/output/chat_trace_position.json", json.dumps({str(path): bad}))
                self.assertEqual(dd.update_chat_trace(save=False)["chats"]["cece3333"]["title"], "Chat")

    def test_reading_is_incremental_and_saved(self):
        path = self.transcript("acac8888-a", self.title("acac8888-a", "Chat"),
                               self.tool("acac8888-a", "Write", "2026-11-09T10:00:00Z", file_path=self.vault_file("knowledge/a.md"), content="x"))
        dd.update_chat_trace(save=True)
        self.transcript("acac8888-a", self.tool("acac8888-a", "Write", "2026-11-09T12:00:00Z", file_path=self.vault_file("knowledge/b.md"), content="x"))
        self.transcript("acac8888-a", {"type": "assistant", "sessionId": "acac8888-a"}, newline=False)   # still being written
        dd.update_chat_trace(save=True)
        saved = json.loads((self.vault / "_system" / "chat_trace.json").read_text(encoding="utf-8"))
        positions = json.loads((self.vault / "_system" / "output" / "chat_trace_position.json").read_text(encoding="utf-8"))
        self.assertEqual(set(saved["notes"]), {"a", "b"})
        self.assertEqual(positions[str(path)], path.stat().st_size - len(json.dumps({"type": "assistant", "sessionId": "acac8888-a"})))

    def test_dry_run_writes_nothing_to_the_vault(self):
        self.transcript("adad9999-a", self.title("adad9999-a", "Chat"))
        with mock.patch.object(dd, "collect_extras", return_value={}), contextlib.redirect_stdout(io.TextIOWrapper(io.BytesIO(), encoding="utf-8")):
            dd.main(["--dry"])
        self.assertFalse((self.vault / "_system" / "chat_trace.json").exists())
        self.assertFalse((self.vault / "_system" / "output" / "chat_trace_position.json").exists())
        self.assertTrue((self.vault / "_system" / "output" / "dashboard" / "notes.json").is_file())

    def test_folder_of_a_chat_in_the_home_folder_is_not_kept(self):
        self.assertEqual(dd.chat_folder(str(Path.home())), "")
        self.assertEqual(dd.chat_folder(str(Path.home() / "notes" / ".claude" / "worktrees" / "w1")), "notes")


class WriteTest(VaultCase):
    def test_write_outputs_and_manifest(self):
        self.write("knowledge/a.md", note("concept", "A"))
        out = self.vault / "_system" / "output" / "dashboard"
        manifest = dd.write_outputs(self.build(), out)
        self.assertEqual(set(manifest), set(dd.DATASETS))
        self.assertEqual(json.loads((out / "manifest.json").read_text(encoding="utf-8")), manifest)
        self.assertEqual(json.loads((out / "notes.json").read_text(encoding="utf-8"))[0]["id"], "a")


class ReviewFixTest(VaultCase):
    def test_private_note_name_does_not_leak_through_pending(self):
        self.write("me/profile.md", note("profile", "Profile"))
        self.write("inbox/pending.md", note("entry", "Pending", "## Open\n- [ ] P-001 | question | 2026-11-09 | Ask | [[profile]] | chat: X | project: [[profile]]\n"))
        row = self.build()["pending"][0]
        self.assertEqual((row["source"], row["project"]), ("", ""))


GITHUB_TOKEN = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"  # secret-scan: allow (fake key on purpose)
CUT_KEEPS = 12   # characters of the key that stay before the cut; too few to be found by the scan on their own


def cut_at(limit: int, key: str) -> str:
    """A text whose key starts just before `limit`, so a cut at `limit` keeps only the key's first characters."""
    return "x" * (limit - 1 - CUT_KEEPS) + " " + key


class IndependentReviewTest(VaultCase):
    def test_rule_files_of_private_projects_stay_out(self):
        self.write("projects/hidden/hidden.md", note("project", "Hidden", privacy="private"))
        self.write("projects/hidden/hidden-rules.md", note("rule", "R", table("| # | Rule | Why |", "| 1 | **ZZONE.** body | why |")))
        self.write("projects/demo/demo-rules.md", note("rule", "R", table("| # | Rule | Why |", "| 1 | **ZZTWO.** body | why |"),
                                                       privacy="private"))
        dump = json.dumps(self.build()["rules"])
        self.assertNotIn("ZZONE", dump)
        self.assertNotIn("ZZTWO", dump)
        self.assertNotIn("hidden", dump)

    def test_private_agent_page_stays_out(self):
        self.write("knowledge/agents-log/agent-scout.md", note("concept", "Scout", "## Log\n" + table(
            "| Date | Mode | Model | Job | Result | Chat | Project |", "| 2026-11-09 | 1 | m | ZZJOB | worked | c | — |"),
            privacy="private"))
        self.assertNotIn("ZZJOB", json.dumps(self.build()))

    def test_secret_cut_at_the_limit_is_hidden(self):
        for key in (SECRET, GITHUB_TOKEN):
            with self.subTest(key=key[:4]):
                self.write("knowledge/a.md", note("concept", "A", f"## In one sentence\n{cut_at(dd.SUMMARY_CHARS, key)}\n"))
                self.write("projects/demo/demo-progress.md", note("progress", "P", "## Log\n### 2026-11-09 — t\n"
                           f"- **Did:** {cut_at(dd.PROGRESS_CHARS, key)}\n", project='"[[demo]]"'))
                self.write("log.md", f"# Log\n\n## [2026-11-09] setup | t\n- {cut_at(dd.LOG_CHARS, key)}\n")
                self.write("councils/2026-11-09-c.md", note("council", "Council: c", f"## Summary\n{cut_at(dd.COUNCIL_SUMMARY_CHARS, key)}\n"))
                self.write("research/2026-11-10-weekly-summary.md", note("research", "W", f"## Added\n- {cut_at(dd.LIST_CHARS, key)}\n"))
                self.write("inbox/handoff.md", note("entry", "Handoff") + "\n## 2026-11-10 10:00 · Work · 0123abcd\n"
                           + cut_at(dd.HANDOFF_CHARS, key) + "\n")
                self.write("rules/general-rules.md", "# Rules\n\n" + table("| # | Rule | Why |", f"| 1 | {cut_at(dd.RULE_TITLE_CHARS, key)} | w |"))
                dump = json.dumps(self.build(), ensure_ascii=False)
                self.assertNotIn(key[:4], dump)

    def test_private_note_names_do_not_leak_into_other_data_sets(self):
        self.write("ideas/zzhididea.md", note("idea", "Hidden", privacy="private"))
        self.write("projects/zzhidproj/zzhidproj.md", note("project", "Secret project", privacy="private"))
        self.write("knowledge/pub.md", note("concept", "About [[zzhididea]]", "## In one sentence\nSee [[zzhididea|it]] now.\n",
                                            project='"[[zzhidproj]]"'))
        self.write("ideas/plan.md", note("idea", "Plan", "- [ ] ask [[zzhididea]] first\n", project='"[[zzhidproj]]"'))
        self.write("projects/demo/plan-progress.md", note("progress", "P", "## Version history\n"
                   + table("| Version | Date | Highlights |", "| v1 | 2026-11-09 | from [[zzhididea]] |")
                   + "\n## Log\n### 2026-11-09 — [[zzhididea]]\n- **Did:** read [[zzhididea]]\n", project='"[[zzhidproj]]"'))
        self.write("councils/2026-11-09-c.md", note("council", "Council: c", "## Summary\nOn [[zzhididea]].\n",
                                                     project='"[[zzhidproj]]"', decision_note='"[[zzhididea]]"'))
        self.write("log.md", "# Log\n\n## [2026-11-09] idea | About [[zzhididea]]\n- body [[zzhididea]]\n")
        self.write("inbox/pending.md", note("entry", "Pending", "## Open\n- [ ] P-001 | question | 2026-11-09 | Ask about [[zzhididea]] | [[pub]]\n"))
        self.write("research/2026-11-10-weekly-summary.md", note("research", "W", "## Added\n- [[zzhididea]]\n"))
        self.write("knowledge/agents-log/agent-scout.md", note("concept", "Scout", "## Log\n" + table(
            "| Date | Mode | Model | Job | Result | Chat | Project |", "| 2026-11-09 | 1 | m | on [[zzhididea]] | worked | c | [[zzhidproj]] |")))
        data = self.build()
        self.assertNotIn("zzhid", json.dumps(data, ensure_ascii=False))
        self.assertEqual(data["pending"][0]["text"], f"Ask about {dd.HIDDEN_TEXT}")
        self.assertEqual({r["id"]: r["project"] for r in data["notes"]}["pub"], "")

    def test_private_note_names_do_not_leak_into_handoff_lessons_or_discoveries(self):
        self.write("ideas/zzhididea.md", note("idea", "Hidden", privacy="private"))
        self.write("inbox/handoff.md", note("entry", "Handoff") + "\n## 2026-11-10 10:00 · Work · 0123abcd\nsee [[zzhididea]]\n")
        self.write("_system/skills/expert-ml/SKILL.md", "---\nname: expert-ml\ndescription: d\n---\n\n## Lessons\n"
                                                        "- 2026-11-09 from [[zzhididea|it]]\n")
        self.write("ideas/project-proposals.md", note("entry", "Proposals", table(
            "| Date | Proposal | What | Goal | Use | Criteria | Difficulty | Needs | First step | Source | Status |",
            "| 2026-11-09 | p | [[zzhididea]] | g | u | c | d | n | f | s | proposed |")))
        data = self.build()
        self.assertNotIn("zzhid", json.dumps({k: data[k] for k in ("handoff", "expertise", "skills", "discoveries")},
                                             ensure_ascii=False))
        self.assertIn(dd.HIDDEN_TEXT, data["handoff"][0]["text"])

    def test_every_spelling_of_a_private_link_is_hidden(self):
        self.write("ideas/zzhididea.md", note("idea", "Hidden", privacy="private"))
        self.write("log.md", "# Log\n\n## [2026-11-09] idea | a [[ZZHidIdea]] b [[ideas/zzhididea]] c [[zzhididea.md]] "
                             "d ![[zzhididea]] e [[ideas\\zzhididea#part|alias]]\n")
        self.write("knowledge/pub.md", note("concept", "Pub", "[[ZZHidIdea]] [[ideas/zzhididea]] [[zzhididea.md]]"))
        data = self.build()
        self.assertNotIn("zzhid", json.dumps(data, ensure_ascii=False).lower())
        self.assertNotIn("!" + dd.HIDDEN_TEXT, data["log"][0]["title"])

    def test_quiz_score_of_a_private_weekly_summary_stays_out(self):
        self.write("research/2026-11-10-weekly-summary.md", note("research", "W", "Memory quiz: 9/10\n", privacy="private"))
        self.assertEqual({r["key"]: r["text"] for r in self.build()["counts"]}["quiz_score"], "")

    def test_link_to_a_session_record_is_not_shown(self):
        self.write("inbox/sessions/2026-11-10-x.md", note("session", "Raw session"))
        self.write("knowledge/a.md", note("concept", "A", "[[2026-11-10-x]]"))
        self.assertEqual(real_rows(self.build()["links"]), [])


if __name__ == "__main__":
    unittest.main()
