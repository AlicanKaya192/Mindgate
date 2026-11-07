"""Vault note graph: shortest path between two notes, neighbours, communities and bridge notes.

Why: to answer "how are A and B connected?" and "which clusters of notes are joined by only a few notes?" beyond a
plain link count. The graph data is built from the vault's notes and wiki links and kept in
`_system/output/graph/notes.json` and `links.json` (outside git); private notes never enter it. No outside
dependency, no network, no note is changed.

Usage (from the vault root):
  graph.py path <A> <B>          shortest path between two notes, with the link direction at each step
  graph.py neighbors <X>         outgoing and incoming links of the note
  graph.py communities [--count N]  note communities and the bridge notes between them
Common options:
  --all      also counts index, log, pending, handoff and entry pages
  --refresh  first rebuilds the graph data from the vault
"""
import argparse
import difflib
import json
import re
import sys
from collections import Counter, deque
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the -I flag does not add the script folder to the path
from common import OUTPUT, VAULT, ascii_lower, atomic_write, frontmatter, name, sensitive_path  # noqa: E402

GRAPH_DIR = OUTPUT / "graph"
# Index pages link to every note and make paths meaningless (the counterpart of leaving "file hubs" out)
HUB_PAGES = {"index", "log", name("pending"), name("handoff")}
HUB_TYPES = {"entry"}
MAX_ROUNDS = 100           # label propagation stops after at most this many rounds
SUGGESTION_COUNT = 3
SUGGESTION_CUTOFF = 0.6
# Folders that never enter the graph: system files, raw session logs and private notes (me, rules)
EXCLUDED_FOLDERS = {name("_system"), name("_templates"), name("me"), name("rules")}
SESSION_FOLDER = (name("inbox"), name("sessions"))
WIKI_LINK = re.compile(r"(?<!!)\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]")
CODE_BLOCK = re.compile(r"```.*?```", re.S)


class DataMissing(Exception):
    """notes.json or links.json was not found."""


@dataclass
class Graph:
    titles: dict[str, str] = field(default_factory=dict)
    outgoing: dict[str, set[str]] = field(default_factory=dict)
    incoming: dict[str, set[str]] = field(default_factory=dict)
    names: dict[str, str] = field(default_factory=dict)   # plain id, title or alias -> note id

    def neighbors(self, note: str) -> set[str]:
        return self.outgoing.get(note, set()) | self.incoming.get(note, set())


def plain(text: str) -> str:
    return ascii_lower(text).strip()


def hub_notes(notes: list[dict]) -> set[str]:
    return {n["id"] for n in notes if n["id"] in HUB_PAGES or n.get("type") in HUB_TYPES}


def build_graph(notes: list[dict], links: list[dict], excluded: set[str]) -> Graph:
    g = Graph()
    chosen = [n for n in notes if n["id"] not in excluded]
    for n in chosen:
        g.titles[n["id"]] = n.get("title") or n["id"]
        g.outgoing[n["id"]], g.incoming[n["id"]] = set(), set()
        g.names[plain(n["id"])] = n["id"]
    # Titles and aliases after the ids: another note's alias ("Atlas") must not override an id ("atlas")
    for n in chosen:
        aliases = [a for a in str(n.get("aliases", "")).split(",") if a.strip()]
        for alias in [n.get("title", ""), *aliases]:
            g.names.setdefault(plain(alias), n["id"])
    for link in links:
        source, target = link["source"], link["target"]
        if link.get("broken") or source == target or source not in g.titles or target not in g.titles:
            continue
        g.outgoing[source].add(target)
        g.incoming[target].add(source)
    return g


# ---------- graph data from the vault ----------
def is_included(relative: Path) -> bool:
    parts = relative.parts
    if parts[0] in EXCLUDED_FOLDERS or parts[:2] == SESSION_FOLDER or any(p.startswith(".") for p in parts[:-1]):
        return False
    return not sensitive_path(relative.as_posix())


def link_targets(body: str) -> list[str]:
    """Wiki link targets of a note body; folder part and `.md` dropped, links in code blocks and embeds skipped."""
    targets = []
    for raw in WIKI_LINK.findall(CODE_BLOCK.sub(" ", body)):
        target = raw.strip().replace("\\", "/").rsplit("/", 1)[-1]
        stem, dot, ext = target.rpartition(".")
        if dot and ext.lower() != "md":
            continue   # an attachment (image, PDF), not a note
        targets.append(stem if dot else target)
    return list(dict.fromkeys(t for t in targets if t))


def build_data(vault: Path = VAULT) -> tuple[list[dict], list[dict]]:
    """(notes, links) of the vault. A link to a note that does not exist is marked broken; a link to a note that
    stays out of the graph (private, system) is dropped later, so its name never reaches the output."""
    all_ids, notes, links = set(), [], []
    for path in sorted(vault.rglob("*.md")):
        relative = path.relative_to(vault)
        all_ids.add(path.stem)
        if not is_included(relative):
            continue
        fields, body = frontmatter(path.read_text(encoding="utf-8"))
        if str(fields.get("privacy", "")).lower() == "private":
            continue
        title = re.search(r"^# (.+)$", body, re.M)
        aliases = fields.get("aliases") or []
        notes.append({"id": path.stem, "title": title.group(1).strip() if title else path.stem,
                      "type": str(fields.get("type", "")),
                      "aliases": ", ".join(aliases) if isinstance(aliases, list) else str(aliases)})
        links += [{"source": path.stem, "target": t} for t in link_targets(body)]
    included = {n["id"] for n in notes}
    links = [{**link, "broken": int(link["target"] not in all_ids)} for link in links
             if link["target"] in included or link["target"] not in all_ids]
    return notes, links


def refresh_data(directory: Path = GRAPH_DIR, vault: Path = VAULT) -> None:
    notes, links = build_data(vault)
    atomic_write(directory / "notes.json", json.dumps(notes, ensure_ascii=False))
    atomic_write(directory / "links.json", json.dumps(links, ensure_ascii=False))


def read_data(directory: Path = GRAPH_DIR) -> tuple[list[dict], list[dict]]:
    try:
        notes = json.loads((directory / "notes.json").read_text(encoding="utf-8"))
        links = json.loads((directory / "links.json").read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise DataMissing(f"{error.filename} is missing; run `graph.py --refresh <command>` first") from error
    return notes, links


# ---------- queries ----------
def find(g: Graph, query: str) -> str | None:
    return query if query in g.titles else g.names.get(plain(query))


def suggestions(g: Graph, query: str) -> list[str]:
    close = difflib.get_close_matches(plain(query), g.names, n=SUGGESTION_COUNT * 2, cutoff=SUGGESTION_CUTOFF)
    return list(dict.fromkeys(g.names[c] for c in close))[:SUGGESTION_COUNT]


def shortest_path(g: Graph, start: str, end: str) -> list[str]:
    """Undirected breadth-first search; neighbours are visited in sorted order, so the same data gives the same path."""
    previous: dict[str, str | None] = {start: None}
    queue = deque([start])
    while queue:
        note = queue.popleft()
        if note == end:
            path = []
            while note is not None:
                path.append(note)
                note = previous[note]
            return path[::-1]
        for neighbor in sorted(g.neighbors(note)):
            if neighbor not in previous:
                previous[neighbor] = note
                queue.append(neighbor)
    return []


def direction(g: Graph, x: str, y: str) -> str:
    forward, backward = y in g.outgoing.get(x, set()), x in g.outgoing.get(y, set())
    return "↔" if forward and backward else "→" if forward else "←"


def communities(g: Graph) -> list[set[str]]:
    """Label propagation: every note takes the label seen most often among its neighbours.
    On a tie the current label is kept, otherwise the alphabetically smallest is chosen; the result is always the same."""
    label = {note: note for note in g.titles}
    for _ in range(MAX_ROUNDS):
        changed = False
        for note in sorted(label):
            counts = Counter(label[n] for n in g.neighbors(note))
            if not counts:
                continue
            most = max(counts.values())
            tied = {lab for lab, c in counts.items() if c == most}
            new = label[note] if label[note] in tied else min(tied)
            if new != label[note]:
                label[note], changed = new, True
        if not changed:
            break
    groups: dict[str, set[str]] = {}
    for note, lab in label.items():
        groups.setdefault(lab, set()).add(note)
    return sorted(groups.values(), key=lambda t: (-len(t), min(t)))


def bridges(g: Graph, groups: list[set[str]]) -> list[tuple[str, int, float]]:
    """Notes that link to more than one community, ranked by participation coefficient:
    1 - Σ(k_c / k)². A note whose links are spread evenly across communities comes first."""
    group_of = {note: i for i, t in enumerate(groups) for note in t}
    result = []
    for note in g.titles:
        neighbors = g.neighbors(note)
        counts = Counter(group_of[n] for n in neighbors)
        if len(counts) < 2:
            continue
        participation = 1 - sum((c / len(neighbors)) ** 2 for c in counts.values())
        result.append((note, len(counts), round(participation, 3)))
    return sorted(result, key=lambda r: (-r[2], -r[1], r[0]))


# ---------- command line ----------
def resolve_note(g: Graph, query: str) -> str:
    note = find(g, query)
    if note:
        return note
    close = suggestions(g, query)
    extra = f" Did you mean: {', '.join(close)}" if close else ""
    raise SystemExit(f"No note named '{query}' in the graph (it may be private or a hub note; --all).{extra}")


def print_path(g: Graph, a: str, b: str) -> None:
    path = shortest_path(g, a, b)
    if not path:
        print(f"No path between {a} and {b}.")
        return
    print(f"Shortest path ({len(path) - 1} steps):")
    print(f"  {path[0]}")
    for previous, note in zip(path, path[1:]):
        print(f"  {direction(g, previous, note)} {note}")


def print_neighbors(g: Graph, note: str) -> None:
    print(f"{note} — {g.titles[note]}")
    print(f"Outgoing ({len(g.outgoing[note])}): {', '.join(sorted(g.outgoing[note])) or '—'}")
    print(f"Incoming ({len(g.incoming[note])}): {', '.join(sorted(g.incoming[note])) or '—'}")


def print_communities(g: Graph, count: int) -> None:
    groups = communities(g)
    large = [t for t in groups if len(t) > 1]
    print(f"{len(g.titles)} notes, {len(large)} communities ({len(groups) - len(large)} single notes apart).")
    for i, t in enumerate(large[:count], 1):
        leading = sorted(t, key=lambda n: (-len(g.neighbors(n)), n))[:5]
        print(f"  {i}. {len(t)} notes — {', '.join(leading)}")
    print("Bridge notes (community count, participation):")
    for note, number, participation in bridges(g, groups)[:count]:
        print(f"  {note} ({number}, {participation})")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Vault note graph queries")
    p.add_argument("--all", action="store_true", help="also count hub pages (index, log, entry pages …)")
    p.add_argument("--refresh", action="store_true", help="first rebuild the graph data from the vault")
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("path")
    s.add_argument("a")
    s.add_argument("b")
    sub.add_parser("neighbors").add_argument("note")
    sub.add_parser("communities").add_argument("--count", type=int, default=10)
    args = p.parse_args(argv)

    try:
        if args.refresh:
            refresh_data()
        notes, links = read_data()
    except OSError as error:
        print(f"ERROR: the graph data could not be built or read ({type(error).__name__}: {error})", file=sys.stderr)
        return 1
    except DataMissing as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    g = build_graph(notes, links, set() if args.all else hub_notes(notes))
    if args.command == "path":
        print_path(g, resolve_note(g, args.a), resolve_note(g, args.b))
    elif args.command == "neighbors":
        print_neighbors(g, resolve_note(g, args.note))
    else:
        print_communities(g, args.count)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")   # the note-not-found message can carry non-ASCII characters too
    sys.exit(main())
