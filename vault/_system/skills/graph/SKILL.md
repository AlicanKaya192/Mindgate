---
name: graph
description: Use when you are asked how two notes in the vault are connected ("what is between A and B"), what the neighbours of a note are, which clusters of notes are joined to each other by only a few notes; or when, in a Python project, a question such as "who calls this function, which module depends on which, is there an import cycle" must be answered without reading file by file. The main chat and the scout load it.
---

Method skill (not an agent). Two scripts; both run on the standard library, do not go out to the network and do not write to the vault. Linked rules: #24 (check the output at the source), #23.

## Note graph: `_system/graph.py`
From the vault root (`{{PY}} -I`):
- `graph.py path <A> <B>`: the shortest path; at each step the link direction (`→` from A, `←` to A, `↔` both ways).
- `graph.py neighbors <X>`: outgoing and incoming links.
- `graph.py communities [--count N]`: note communities and the bridge notes between communities. Bridges are ranked by participation coefficient: a note whose links are spread evenly across communities comes first.
- A name can be a file name, a title or an alias; case and accents do not matter. If nothing is found, the 3 closest names are suggested.
- `--all`: index, log, pending, handoff and entry pages are left out by default; they link to every note and make a path meaningless.
- `--refresh`: rebuild the graph data from the vault first. If the vault changed in this chat, refresh first.
- Private notes (`me/`, `rules/`, `privacy: private`) never enter the graph; a "no path" result can be because of this too.

When it helps:
- When answering a question (§7.5): to show through which notes two topics are connected.
- In lint (§7.7): to see the bridge notes and the clusters joined by a single note, and to propose missing links. The proposal is shown to the user; the link is not added by itself.

## Code map: `_system/code_map.py`
- `code_map.py <folder> [--exclude <path>]...`: counts of modules, classes and functions, the most imported modules, import cycles, the most called. JSON output goes to `_system/output/code_map/<folder>.json` (outside git).
- `code_map.py <folder> --find <name>`: the `file:line` of the definition and its callers.
- Files are only parsed with `ast`; none is run or imported. Virtual environments, `.git`, `build` and `dist` are skipped. Files with syntax errors and files over 2 MB appear in the "skipped" list.
- **Give the root of the project as the folder**, not a subfolder; otherwise `from app.x import y` cannot be resolved. Leave non-application folders out with `--exclude` (for example content and plan folders: `--exclude content --exclude Plan`; in a big project the module count drops from thousands to hundreds and it finishes in a few seconds).
- Edge labels:
  - `extracted`: explicit in the source (a name in the same module, an imported name or module, a `self`/`cls` method).
  - `guessed`: `variable.method()` and the project has only one method with that name. It can be confused with a method of an outside library; open its line before you use it.
  - `ambiguous`: a call that fits more than one definition; no edge is made, it is only counted.
- Python only. C# and other languages are out of scope.

## Verify before finishing
- [ ] You opened every path, edge or caller that the decision rests on at its line in the source file (#24); a `guessed` edge alone is not proof.
- [ ] If the vault changed in this chat, you ran with `graph.py --refresh`.
- [ ] You wrote the command and the `--exclude`/`--all` options you used into the report.

## Idea sources
- graphify (Apache-2.0): knowledge graph, leaving file hubs out of the most central nodes, an extracted/guessed label on edges. Read from a downloaded copy; no code was taken (#35).
- Participation coefficient: Guimerà and Amaral (2005), *Functional cartography of complex metabolic networks*, Nature 433.

## Lessons
<!-- The central agent adds verified lessons here: general and reusable, without project names or dates. -->
- In a desktop project that used a GUI framework, hundreds of "guessed" calls were attached to a single `connect` method; the calls were really framework signals (`timer.timeout.connect`). Guessing was narrowed to the `variable.method()` form only, and the "most called" list counts only extracted edges.
