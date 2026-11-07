# Skill Library

Claude Code skills. The source files are here (`_system/skills/<name>/SKILL.md`, in git); the folders `~/.claude/skills/<name>` are linked here (a **junction** on Windows, a symlink elsewhere), so there is a single copy. A simple form of procedural memory: a job that repeats = a single command.

**Usage counter:** Every time a skill is used its usage count goes up; if an error occurs it is written to the "last error" column. A skill that gives the same error three times is rewritten in the weekly upkeep (the "fix the skill on failure" idea of Memento-Skills, with human approval).

| Skill | What it does | Usage | Last used | Last error |
|---|---|---|---|---|
| `/keep-records` | Scan the session logs, review the conversation, write to the vault, log, commit | 0 | — | — |
| `/new-project` | Project folder + main page, progress, rules, ADR; index, log, profile | 0 | — | — |
| `/problem` | Problem/solution note (search first, add a repeat if it exists), project link, index, log | 0 | — | — |
| `/idea` | Write the idea straight to the inbox: the user's own sentence + a short assessment + links | 0 | — | — |
| `/interview` | Asks the user questions one at a time until the topic is finished, writes the answers into the related notes (searches the vault first; no sensitive information) | 0 | — | — |
| `/style` | Extracts an animated explainer video style prompt from a reference image, tests it in a fresh session, makes a video in that style (adapted from a public /stil skill text) | 0 | — | — |

### Expertise packs (rule #28)
Loaded by themselves (when the work touches that field). Specialization builds up in the **Lessons** section of each pack; a lesson is added only by the central agent and after it is verified. Agents and their usage: the agent pages under `knowledge/agents-log/`.

| Pack | Field | Usage | Last used |
|---|---|---|---|
| `expert-architecture` | Structure, module boundary, ADR, file ownership | 0 | — |
| `expert-design` | Visual design, design system, typography, color, WCAG 2.2 | 0 | — |
| `expert-frontend` | Interface (UI), user experience (UX), accessibility | 0 | — |
| `expert-backend` | API, business logic, database, migration | 0 | — |
| `expert-security` | OWASP, secrets, dependencies, threat model | 0 | — |
| `expert-server` | Deployment, port, TLS, CI | 0 | — |
| `expert-docker` | Dockerfile, compose, image security | 0 | — |
| `expert-ml` | Data leakage, metrics, reproducibility | 0 | — |
| `expert-seo` | Technical SEO, on-page, JSON-LD, site structure, visibility in AI search | 0 | — |
| `expert-content` | Blog, LinkedIn, README text in the user's voice; removing AI traces, seven-pass editing | 0 | — |
| `expert-language` | Turkish and English spelling, punctuation, context; removing AI traces from text; `references/tdk.md`, `references/ai-traces.md` | 0 | — |
| `expert-writing` | Game narrative, character, dialogue, story, interface text, technical documents, design briefs | 0 | — |
| `expert-geodata` | Public live geographic data (aircraft, ships, satellite passes, earthquakes, maps) and OSINT-style event and infrastructure research | 0 | — |

### Method skills
Preloaded for an agent at its start through the `skills:` field of the agent definition. The main chat can load the same skill when doing the same job.

| Skill | Agent | What | Usage | Last used |
|---|---|---|---|---|
| `scouting-method` | scout | Code exploration steps, source order, quote → claim, verification before finishing | 0 | — |
| `review-method` | reviewer | Diff-focused passes, confidence score (threshold 80), false-positive elimination, report | 0 | — |
| `obsidian-writing` | maintainer | Obsidian syntax, summary of vault rules, verification before finishing | 0 | — |
| `clean-code` | all (rule #30) | Clean code rules: names, functions, comments, error handling, SRP, DRY/YAGNI/KISS, format, tests; checklist before finishing | 0 | — |
| `verification` | reviewer, maintainer (the scout and the main chat can load it) | Evidence first, then the claim: a claim → evidence needed table, verifying an agent report with the diff | 0 | — |
| `debugging` | main chat (the reviewer can load it) | No fix before the root cause; 4 phases, the 3-attempts rule, problem note | 0 | — |
| `test-writing` | main chat (the reviewer can load it) | Red-green-refactor (without deleting, #22), a good test, regression, explore first in the web interface | 0 | — |
| `task-writing` | main chat | Implementation plan, task specification for an agent (results that do not count, output contract), parallel dispatch, applying a review report | 0 | — |
| `evaluation-method` | main chat (the reviewer can load it) | Direct scoring or A/B, bias safeguards, rubric, metric choice, skill and prompt measurement | 0 | — |
| `context-management` | main chat (the maintainer can load it) | Mandatory sectioned summary, probe questions, putting big output in a file, signs of context degradation | 0 | — |
| `skill-writing` | main chat | Reviewing and adapting a skill from outside, SKILL.md structure, testing, linking | 0 | — |
| `external-source-review` | main chat | Reviewing an external repository, skill or second-brain system: inventory, scan, reading with scouts, verification, A/B/C/D classification, red flags (turned into a skill from three repetitions, §10.2) | 0 | — |
| `orchestration` | main chat | Choosing among three modes, council folder, blind first round, at most two rounds, conflict labels, one-page final report | 0 | — |
| `advisor-method` | advisor | Direction and scope at the start, acceptance criteria at the end; four viewpoints, three severity levels | 0 | — |
| `counter-view-method` | hater | Pre-mortem, evidenced objection, stopping criterion, the strongest unanswered objection | 0 | — |
| `news-method` | news | Narrowing the question, source order, two-source verification with SIFT | 0 | — |
| `external-agent` | main chat | Using an installed external coding agent (Codex and the like) off by default, with permission per task | 0 | — |
| `reverse-engineering` | main chat | Understanding a program, package or file format without source code: authority and limits first, path by target, summary first, observation/inference/unknown, findings ledger | 0 | — |
| `graph` | main chat, scout | Note graph (`graph.py`: shortest path, neighbours, communities, bridge notes) and Python code map (`code_map.py`: import graph, cycles, callers; extracted/guessed label). Standard library, no network | 0 | — |
| `synthetic-customer-test` | main chat | Testing an idea, offer or price on a panel of evidence-based virtual customers: independent questions, a decision rule, a real-world test (not evidence of demand) | 0 | — |

## Adding a new skill
Detailed method: the `skill-writing` skill (including adapting a skill from outside and testing).

1. Write `_system/skills/<name>/SKILL.md`: frontmatter `name`, `description` (including when it is to be used); the body numbered steps; the vault path and the schema reference; strict rules.
2. Open the `~/.claude/skills/<name>` link (on Windows: `cmd /c mklink /J "%USERPROFILE%\.claude\skills\<name>" "<vault>\_system\skills\<name>"`; elsewhere: `ln -s`).
3. Add a row to this table; add an `install` entry to `log.md`. Optional dashboard: not in v1.
