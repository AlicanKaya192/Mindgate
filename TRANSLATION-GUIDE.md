# Mindgate translation and generalization guide

Every file in `locales/tr/` is the Turkish original copied from a private, working second-brain vault. Each one produces two outputs:

1. **English base** at the same relative path under the repository root (e.g. `locales/tr/vault/_system/skills/idea/SKILL.md` → `vault/_system/skills/idea/SKILL.md`).
2. **Generalized Turkish** written back in place in `locales/tr/` (same file).

Python code exists only in English (`vault/_system/*.py`, skill `scripts/`); its Turkish copy in `locales/tr/` is source material only and is not shipped.

## 1. Names
- All names come from `locales/tr/names.json` (English → Turkish). In English files use English names; in Turkish files use Turkish names.
- Folder and file references inside text follow the same map: `gelen/bekleyenler.md` → `inbox/pending.md`, `kurallar/genel-kurallar.md` → `rules/general-rules.md`, `_sistem/kayit.py` → `_system/records.py`, `/fikir` → `/idea`, agent `kasif` → `scout`.
- Wiki links `[[note-name]]` follow the same map when the target is a system file; links to personal notes are removed (see §3).

## 2. Placeholders
| Placeholder | Meaning |
|---|---|
| `{{VAULT}}` | absolute path of the user's vault |
| `{{HOME}}` | the user's home folder (contains `.claude`) |
| `{{PY}}` | the Python command chosen at install (e.g. `py -3.14`, `python3`) |
| `{{USER}}` | how the vault refers to its owner in generated notes; in instructions write "the user" / "kullanıcı" instead |
| `{{LANG}}` | `en` or `tr` |

Never leave a real absolute path, user name, machine name, e-mail or URL that identifies a person.

## 3. Generalization (no personal content)
- The owner's name becomes "the user" (EN) / "kullanıcı" (TR). Quotes of the owner ("the owner said …") are removed; keep only the rule or reason, written neutrally.
- Project names, course names, people, dates of personal events, dashboard IDs: removed. If an example is needed, write a neutral one ("in one project a build script deleted …").
- **Rules (`rules/general-rules.md`):** keep number, title and rule text; rewrite the "why" column as a general reason anyone would accept; drop the source quote and personal dates. Rules that only make sense for one person or one machine (shared account fingerprint, usage limits, specific apps) are moved to an "Optional rules" section the installer can offer.
- **Lessons (`## Lessons` / `## Dersler` in skills):** keep a lesson only if it is a general, reusable lesson; rewrite it without project names and dates (`— {project} —` part removed). Otherwise drop it. An empty Lessons section keeps its comment line.
- Dashboard (claude.ai artifact) is not part of v1: remove steps that publish or update it; keep a one-line note "optional dashboard: not included in v1".
- The daily task must not push by default and must scan only sessions that belong to the vault unless the user opted in (installer asks).

## 4. Style
- English: plain, direct, short sentences; no marketing; no AI-sounding filler. Keep the original's structure (headings, tables, numbered steps).
- Turkish: TDK spelling; English technical terms with Turkish in parentheses on first use, as in the originals.
- Keep frontmatter keys exactly as `names.json`/code expects (see §5).

## 5. Code (Python)
- File names from `scripts_en_only`; identifiers, comments, docstrings and messages in English.
- Folder/file names are never hard-coded: read them through `common.py` (`name("inbox")`, `path("inbox", "pending.md")`), which loads the active name map from `_system/config.json`.
- Frontmatter keys and values used by code are English in both languages (`type`, `status`, `project`, `tags`, `aliases`, `created`, `updated`; values such as `idea`, `active`, `open`, `solved`) — they are data schema, like code.
- Behaviour must not change except where this guide says so; tests are translated with the code and must pass.

## 5a. Shared terms (fixed; code and text must use exactly these)
- Frontmatter keys: `type`, `status`, `project`, `tags`, `aliases`, `created`, `updated`, `source_type`, `source_format`, `source_url`, `source_file`, `authors`, `year`, `source_notes`, `published_url`, `privacy`, `invalid`, `replaced_by`, `invalid_reason`; council notes: `mode`, `agents`, `result`, `calls`, `opus`, `decision_note`.
- `status` values: `active`, `paused`, `done`, `archived`, `open`, `solved`, `draft`, `accepted`, `proposed`, `superseded`, `ready`, `published`. Council `result`: `passed`, `conditional`, `failed`, `running`. `source_type`: `stated`, `inferred`, `verified`. `privacy`: `private`.
- `tags` are free text in the vault language; code reads only the `security` tag (TR: `guvenlik`) — code must accept both.
- Template placeholders: `{{date}}` and `{{title}}` are Obsidian built-ins and stay identical in both languages. Other placeholders are hints for the writer: English names in English files (`{{project}}`, `{{count}}`, `{{task}}`), Turkish names in Turkish files.
- `graph.py path | neighbors | communities` (`--all`, `--refresh`); `code_map.py --find | --exclude`, edge labels `extracted | guessed | ambiguous`, output `_system/output/code_map/`; `records.py pending add --type`, `records.py log --operation --title --evidence --learned`, `records.py index --section --line`. Log operations (EN): `setup, idea, project, progress, problem, decision, experiment, ingest, research, query, lint, rule, profile, release, pending, done, learning, violation`.
- Script sub-commands: `session_log.py scan | process`, `records.py pending add | close | hold`, `records.py log | index | handoff write`.
- Council working folder: `_system/output/council/YYYY-MM-DD-<name>/` with `task.md`, `round1/`, `round2/`, `decision.md`, `report.md`.
- Pending-item ids: `P-001` (EN) / `B-001` (TR) — code accepts both prefixes.
- More CLI names used by the texts (code must match): `records.py pending add | close | hold`, `records.py handoff write`, `session_log.py remind | scan | process`, `session_mode.py set <session> recorded | unrecorded`, `task_status.py start | finish | wait`, `install_instructions.py install`, `health.py --full | --save-baseline`, `cost.py --days`, `site_guard.py after`. Values read by code (English in both languages): pending types `question, approval, decision, task, notice, on-hold`; log body lines `- Evidence:` and `- Learned:`; secret-scan allow marker `secret-scan: allow`; task states `finished_today, running`; note type `entry` (folder entry pages). Localized headings that code looks for must be matched in both languages: `Attempted solutions` / `Denenen çözümler`, `Closed` / `Kapananlar`.
- Files under `_system/` not in names.json stay English in both installs (`memory-quiz.md`, `health_baseline.json`, `output/…`). Content note `blocked-sites` (TR `engelli-siteler`) is read by `command_guard.py` through `name()`.
- expert-design scripts: flags `--output --record --baseline --note --widths --external-url`; files `summary.json`, `design-record.json`. `context_check.py stop`; `config.json` key `context` (was `otomatik_baglam`). Evidence marker `[EVIDENCE NEEDED]` (TR `[KANIT GEREK]`).

## 6. Leak check
Before any commit: `python _system/secret_scan.py` and the private blocklist scan (`.yerel/`, never committed) must report zero matches.
