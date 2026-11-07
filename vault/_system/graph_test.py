"""graph.py tests: shortest path, neighbours, name resolution, hub filter, community and bridge, building the data from
the vault. No network; writes only under _system/output/test_graph/."""
import contextlib
import io
import json
import shutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
import graph  # noqa: E402

ROOT = common.OUTPUT / "test_graph"


def note(note_id: str, title: str = "", kind: str = "concept", aliases: str = "") -> dict:
    return {"id": note_id, "title": title or note_id, "type": kind, "aliases": aliases}


def link(source: str, target: str, broken: int = 0) -> dict:
    return {"source": source, "target": target, "broken": broken}


def build(notes: list[dict], links: list[dict], everything: bool = False) -> graph.Graph:
    excluded = set() if everything else graph.hub_notes(notes)
    return graph.build_graph(notes, links, excluded)


class PathTest(unittest.TestCase):
    def test_two_step_path_is_found(self):
        g = build([note("a"), note("b"), note("c")], [link("a", "c"), link("c", "b")])
        self.assertEqual(graph.shortest_path(g, "a", "b"), ["a", "c", "b"])

    def test_link_direction_is_shown(self):
        g = build([note("a"), note("b")], [link("b", "a")])
        self.assertEqual(graph.direction(g, "a", "b"), "←")
        self.assertEqual(graph.direction(g, "b", "a"), "→")

    def test_two_way_link(self):
        g = build([note("a"), note("b")], [link("a", "b"), link("b", "a")])
        self.assertEqual(graph.direction(g, "a", "b"), "↔")

    def test_unconnected_notes_give_empty_list(self):
        g = build([note("a"), note("b")], [])
        self.assertEqual(graph.shortest_path(g, "a", "b"), [])

    def test_same_note_gives_single_element_path(self):
        g = build([note("a")], [])
        self.assertEqual(graph.shortest_path(g, "a", "a"), ["a"])

    def test_broken_link_stays_out_of_graph(self):
        g = build([note("a"), note("b")], [link("a", "b", broken=1)])
        self.assertEqual(graph.shortest_path(g, "a", "b"), [])

    def test_self_link_is_not_a_neighbor(self):
        g = build([note("a")], [link("a", "a")])
        self.assertEqual(g.neighbors("a"), set())

    def test_target_missing_from_note_list_is_skipped(self):
        g = build([note("a")], [link("a", "private-note")])
        self.assertNotIn("private-note", g.titles)
        self.assertEqual(g.neighbors("a"), set())


class HubTest(unittest.TestCase):
    NOTES = [note("a"), note("b"), note("index"), note("projects", kind="entry")]

    def test_path_through_hub_absent_by_default(self):
        g = build(self.NOTES, [link("index", "a"), link("index", "b")])
        self.assertEqual(graph.shortest_path(g, "a", "b"), [])

    def test_all_includes_hub(self):
        g = build(self.NOTES, [link("index", "a"), link("index", "b")], everything=True)
        self.assertEqual(graph.shortest_path(g, "a", "b"), ["a", "index", "b"])

    def test_entry_page_counts_as_hub(self):
        self.assertEqual(graph.hub_notes(self.NOTES), {"index", "projects"})


class NameResolutionTest(unittest.TestCase):
    def setUp(self):
        self.g = build([note("solution-note", title="Çözüm Notu", aliases="Main fix, Fix"), note("data-leakage")], [])

    def test_file_name_directly(self):
        self.assertEqual(graph.find(self.g, "data-leakage"), "data-leakage")

    def test_title_with_accents(self):
        self.assertEqual(graph.find(self.g, "çözüm notu"), "solution-note")

    def test_by_alias(self):
        self.assertEqual(graph.find(self.g, "fix"), "solution-note")

    def test_not_found_gives_none_and_suggestion(self):
        self.assertIsNone(graph.find(self.g, "data-leakag"))
        self.assertIn("data-leakage", graph.suggestions(self.g, "data-leakag"))

    def test_alias_of_another_note_does_not_override_an_id(self):
        g = build([note("atlas", title="Atlas: maintenance tool"), note("maintenance-draft", aliases="Atlas")], [])
        self.assertEqual(graph.find(g, "Atlas"), "atlas")
        self.assertEqual(graph.suggestions(g, "atlsa")[0], "atlas")


class CommunityTest(unittest.TestCase):
    def cluster(self, prefix: str) -> list[dict]:
        names = [f"{prefix}{i}" for i in range(4)]
        return [link(x, y) for i, x in enumerate(names) for y in names[i + 1:]]

    def setUp(self):
        names = [f"{p}{i}" for p in "ab" for i in range(4)] + ["bridge"]
        links = self.cluster("a") + self.cluster("b") + [link("bridge", "a0"), link("bridge", "b0")]
        self.g = build([note(n) for n in names], links)

    def test_two_clusters_are_separate_communities(self):
        groups = graph.communities(self.g)
        a_group = next(t for t in groups if "a1" in t)
        b_group = next(t for t in groups if "b1" in t)
        self.assertNotEqual(a_group, b_group)
        self.assertTrue({"a0", "a1", "a2", "a3"} <= a_group)
        self.assertTrue({"b0", "b1", "b2", "b3"} <= b_group)

    def test_result_is_the_same_every_time(self):
        self.assertEqual(graph.communities(self.g), graph.communities(self.g))

    def test_bridge_note_is_found(self):
        found = graph.bridges(self.g, graph.communities(self.g))
        self.assertEqual(found[0][0], "bridge")
        self.assertEqual(found[0][1], 2)

    def test_empty_graph(self):
        empty = build([], [])
        self.assertEqual(graph.communities(empty), [])
        self.assertEqual(graph.bridges(empty, []), [])


class LoadFromFileTest(unittest.TestCase):
    def setUp(self):
        ROOT.mkdir(parents=True, exist_ok=True)
        (ROOT / "notes.json").write_text(json.dumps([note("a"), note("b")]), encoding="utf-8")
        (ROOT / "links.json").write_text(json.dumps([link("a", "b")]), encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(ROOT, ignore_errors=True)

    def test_reads_json_files(self):
        notes, links = graph.read_data(ROOT)
        self.assertEqual([n["id"] for n in notes], ["a", "b"])
        self.assertEqual(len(links), 1)

    def test_missing_file_gives_meaningful_error(self):
        with self.assertRaises(graph.DataMissing):
            graph.read_data(ROOT / "missing")


VAULT_NOTES = {
    "knowledge/a.md": "---\ntype: concept\naliases: [Alpha, First]\n---\n# Note A\nSee [[b]], [[c|the C note]] and [[missing]].\n"
                      "```\n[[in-code]]\n```\n![[picture.png]] [[me-note]]\n",
    "knowledge/b.md": "---\ntype: concept\n---\n# Note B\nBack to [[knowledge/a.md|A]] and [[a#Heading]].\n",
    "knowledge/c.md": "---\ntype: concept\nprivacy: private\n---\n# Private C\n[[a]]\n",
    "me/me-note.md": "# Me\n[[a]]\n",
    "rules/rule.md": "# Rule\n[[a]]\n",
    "inbox/sessions/s.md": "# Session\n[[a]]\n",
    "_system/tool.md": "# Tool\n[[a]]\n",
    "knowledge/secret-stuff/x.md": "# X\n[[a]]\n",
    "index.md": "---\ntype: entry\n---\n# Index\n[[a]] [[b]]\n",
}


class BuildDataTest(unittest.TestCase):
    def setUp(self):
        self.vault = ROOT / "vault"
        for relative, text in VAULT_NOTES.items():
            path = self.vault.joinpath(*(common.name(segment) for segment in relative.split("/")))   # install language
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        self.notes, self.links = graph.build_data(self.vault)

    def tearDown(self):
        shutil.rmtree(ROOT, ignore_errors=True)

    def test_private_and_system_notes_stay_out(self):
        self.assertEqual(sorted(n["id"] for n in self.notes), ["a", "b", "index"])

    def test_links_to_hidden_notes_are_dropped_and_missing_ones_marked_broken(self):
        pairs = {(lk["source"], lk["target"], lk["broken"]) for lk in self.links}
        self.assertIn(("a", "b", 0), pairs)
        self.assertIn(("b", "a", 0), pairs)
        self.assertIn(("a", "missing", 1), pairs)
        targets = {lk["target"] for lk in self.links}
        self.assertFalse(targets & {"c", "me-note", "in-code", "picture", "picture.png"})

    def test_title_aliases_and_type_are_read(self):
        a = next(n for n in self.notes if n["id"] == "a")
        self.assertEqual((a["title"], a["aliases"], a["type"]), ("Note A", "Alpha, First", "concept"))
        g = build(self.notes, self.links)
        self.assertEqual(graph.find(g, "alpha"), "a")
        self.assertNotIn("index", g.titles)

    def test_refresh_writes_data_that_read_data_loads(self):
        graph.refresh_data(ROOT / "data", self.vault)
        notes, links = graph.read_data(ROOT / "data")
        self.assertEqual((notes, links), (self.notes, self.links))


class RefreshErrorTest(unittest.TestCase):
    def setUp(self):
        self.old = graph.refresh_data

        def failing():
            raise PermissionError("output folder is not writable")
        graph.refresh_data = failing

    def tearDown(self):
        graph.refresh_data = self.old

    def test_failed_refresh_returns_error_code(self):
        with contextlib.redirect_stderr(io.StringIO()) as error:
            self.assertEqual(graph.main(["--refresh", "communities"]), 1)
        self.assertIn("not writable", error.getvalue())


if __name__ == "__main__":
    unittest.main()
