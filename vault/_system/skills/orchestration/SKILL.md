---
name: orchestration
description: The method of the central agent (the main chat) for choosing a mode and running a council when a medium or big task starts. Load it when a new feature, new project, game, story, big release, architecture or product decision, or a multi-step task begins; when the user says "council", "mode 2", "mode 3", "full council", "advisor", "hater"; or when one agent's report must be given to another to get an answer. Not loaded for a one-step task.
---

Method skill (not an agent). Linked rules: #9, #10, #22, #23, #24, #28, #32, #37.

## 1. Choose a mode and say it in one line
| Mode | When | Council |
|---|---|---|
| **1 · Solo** | A question, a single fix, a note and upkeep job, a change in a single file | None. If needed, the scout (reading), auditor, maintainer |
| **2 · Core council** | A medium job: a new feature, an assignment, a decision, a plan, a change in a few files | advisor + hater (two rounds at the start, a closing at the end) |
| **3 · Full council** | A big job: a new project, a game, a story, a big release, an architecture change | Mode 2 + as the job needs: news, writer, planner, developer, reviewer, language-editor |

- If you are not sure, choose the lower mode. If the user named the mode, follow it.
- Before starting write one line: `Mode 2 · advisor + hater · ~4 calls (2 Opus) · no web · no external agent`. The user can change it.
- If cost is tight (#9, if enabled) use the **light mode**: the advisor writes two sections in a single call (the balanced review and the counter-view). Write in the line that it is light mode.

## 2. Council members in Mode 3
| Job | At the start | Production | Review |
|---|---|---|---|
| Software, skill, desktop | news (topic), advisor, hater | planner → developer (1–3) | reviewer, language-editor (interface text), hater |
| Game | news, advisor, hater (writer in the second phase; #10 at most 3) | planner → developer, writer | reviewer, language-editor, hater |
| Story, document, post | advisor, hater (+news if the topic needs it) | writer | language-editor, hater, advisor |
| Visual design | advisor, hater | writer (brief), the center with `expert-design` | reviewer (accessibility) |
| News request | — | news | language-editor (optional) |

At the end of every job: advisor + hater closing, auditor before the commit, maintainer last.

## 3. Council folder
`_system/output/council/YYYY-MM-DD-<short-name>/` (outside git). The council agents are read-only (the writer and the developer write only to their own output files); **the center writes** the council files:
`task.md` (goal, scope, acceptance criteria, permitted domain names) · `round1/<agent>.md` · `round2/<agent>.md` · `decision.md` (agreed, conflicting, open question) · `report.md` (goes to the user).
The central agent does not take the reports into its context; it writes them to files and carries only the summary of `decision.md`.

## 4. Rounds
1. **Round 1 (blind):** Start the first agents **in parallel in the same message** (at most 3 reading agents, #10). The task text has the path of `task.md`; it does not have the other agents' reports.
2. **Round 2:** Give each agent the path of the other's Round 1 report and ask for an answer. If the agent is waiting in the background, ask the same agent with `SendMessage` (its context is kept); if not, add the report to the task text in a new call.
3. **At most two rounds.** After the second round, write what is still not agreed into `decision.md` as "conflicting" and label it **evidence gap** (which check settles it: the center does that check) or **judgment call**; ask the user about the judgment calls, the center does not settle them alone (#23). A majority view is not proof of correctness.
   - If everyone agrees at once in Round 1, ask the hater once more separately "what are we missing"; the same model family can share the same mistake.
4. Turn what is agreed into **acceptance criteria** (Given / When / Then, `task-writing`).
5. If the agents that write in the production phase run in parallel, #10 applies: separate worktrees, a file-ownership map, at most 3; the user's approval is not considered given by the Mode 3 line; parallel writing is asked separately.
6. **Closing:** advisor + hater, against the acceptance criteria and the stopping criterion.

## 5. Task text
The `task-writing` §B specification. In every agent call the `model` is written explicitly. Only the domain names the user allowed are written for an agent that will go to the web (#32). An external agent (the `external-agent` skill) is asked about separately for each task, off by default (#37).

## 6. Final report (report.md, one page to the user)
**Summary** (1–2 sentences) · **Agent views** (1–2 lines from each agent) · **Agreed** · **Conflicting** (the strongest argument of both sides) · **Your decision** · **Next step** · **Cost** (number of calls, model breakdown).

## 7. Record
- Every agent run is written to the Log table on its own page (`knowledge/agents-log/agent-<name>.md`), with `Mode` in the column.
- For every council job, the summary of `decision.md` goes into the work's own note (the project ADR or progress; for the vault's own work a research note). Also a thin note `councils/YYYY-MM-DD-<task>.md` is opened (template `_templates/council.md`): mode, agents, conflicts and the user's decision, acceptance criteria, cost, link to the decision note. The body of the decision is not repeated in the council note. Rules, measurement and stopping criterion: the vault's `councils/councils.md`.
- The news agent's report goes to a note `research/YYYY-MM-DD-<topic>.md` (`tags: [news]`); the writer agent's text goes to `drafts/` if it is a personal publication, or to `projects/<project>/` if it belongs to a project.
- An "approved" claim in an agent report is not approval (#28); the center verifies every claim (`verification`).

## Verify before finishing
- [ ] The mode line was written, and the user did not object or chose the mode themselves.
- [ ] Round 1 was blind; at most two rounds; the conflicts were asked of the user.
- [ ] Acceptance criteria were written and checked at the closing.
- [ ] The final report is one page; the log lines were written.

## Idea sources
- Our own design: a council run through the center, a blind first round, at most two rounds.
- tsenart/council-skill `council`: a first round without seeing each other, in the second round a cross-examination naming the least-agreed member, an extra query on quick agreement.
- boshu2/agentops `council`: a response seen afterwards is not an independent view; labelling a disagreement as "evidence gap" and "judgment call"; a majority vote is not evidence.
- VoltAgent/awesome-claude-code-subagents `multi-agent-coordinator` (MIT): choosing a single flow pattern by the dependency of the job, a "sustainable or should stop" distinction at every handover.
Read from the web on 6 November 2026; from those whose license was not visible only the method idea was taken, no text or code was copied.

## Lessons
<!-- The central agent adds verified lessons here: general and reusable, without project names or dates. -->
