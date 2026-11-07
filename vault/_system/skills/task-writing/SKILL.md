---
name: task-writing
description: Use when writing an implementation plan for a multi-step job, or when preparing a task text for an agent (scout, reviewer, maintainer); especially if parallel work is to be given to more than one agent. The main chat (central agent) loads it.
---

Method skill (not an agent). It details the "Task text" item of the global CLAUDE.md and rule #28.

## A. Implementation plan
Write the plan for someone who has never seen the code but knows their job. Do not write the code yourself; write the decisions that person cannot make alone.

1. **Scope check:** If the job splits into independent subsystems, write a separate plan for each. Each plan must give a result that works and can be tested on its own.
2. **File map:** First write which file will be created, which will change, and their responsibilities. Each file has a single responsibility. In an existing project follow its layout.
3. **Task size:** A task is the smallest unit that has its own test loop. Setup and documentation steps join the task that needs them.
4. **Step = one action + a checkable result:** Write the test → see red → write the code → see green → commit. In a verification step the command and the expected output are written.
5. **Interfaces:** Each task writes what it uses and what it produces: function name, parameters, return type.
6. **Acceptance criterion, critical path, risk:**
   - **Acceptance criterion:** The "done" definition of each task is written as a Given / When / Then (Gherkin) sentence: "Given: an empty CSV · When: the preview opens · Then: it says 'no rows', no error". Each sentence must be able to become a test; if it cannot, the criterion is vague.
   - **Critical path:** Which task waits for which, in one line: `1 → 3 → 5; 2 and 4 independent`. Independent tasks are candidates for parallel dispatch (§C).
   - **Risk and mitigation:** At most 3 risks, each in the form `risk → mitigation → sign` ("the file may be locked → read from a copy → test: locked file"). A risk with no mitigation goes to the list of things to ask the user.
7. **Self-review:**
   - Is every item of the request tied to a task?
   - Is there any line left that decides nothing, like "add appropriate validation" or "handle edge cases"?
   - Are names and types consistent between tasks?
   - Is the plan longer than the code it describes? (If so, the code itself has been written, not a plan.)
   - **Review focus:** At the top of the plan, write in one line **at most 5** inputs or situations that the request needs, that no test tries and that could catch the user out most (e.g. empty input, accented characters, a big file, no network, two writes at the same time). Add the test of each to the related task. If the list is empty write "I looked, there are none". No extra call, only the plan text.
8. **Implementer check (only in a big job):** Before the plan goes to the user, it is read through the eyes of the person who will implement it, and the questions that still remain are brought out.
   - **When:** The job fits the "big job" definition (many files, a structure change, a new system) **and** the plan has at least 4 tasks. **Skipped:** a small job; the user said "do it without asking"; the same plan was already approved in this session; an urgent fix.
   - **The free way first:** In a plan of 4–6 tasks do the check yourself: read the plan from the start as "I am implementing this for the first time".
   - **A sub-agent only for a plan of 7 tasks and above, or one that touches more than one project.** Cost limits:
     - a single call, a single round: it is not called a second time for the same plan
     - `scout` (Haiku), read-only, no web
     - the plan and at most 5 file paths in the task text
     - the output is at most 10 questions, each one line
   - **Scout task text (in the §B form):** "You are the person who will implement this plan. You did not see the chat. Read the plan and the files given. Before starting, write in one line each the at most 10 questions you still need to ask, starting with the most important. Next to each question note which plan item it rests on. Do not write code, do not change files, do not bring suggestions."
   - **The questions are split in three:**
     - (a) the answer is in the chat or the project: written into the plan
     - (b) small: does not change the result; you decide yourself, marked in the plan as "my decision"
     - (c) only the user can give it: asked in a single message, starting with the most important
   - **Write the defaults openly.** The language, library, file place or limit value you chose is not shown as the user's approval; they cannot reject a default they have not heard.
   - **Record:** If a sub-agent ran, write a line to the scout log and tell the user in one line (#28): "Implementer check: scout (Haiku), N questions, M of them for you".
9. **Approval:** The plan is shown to the user and applied after approval (#23). If a lasting plan is needed it is written to the project's vault folder.

## B. Task text for an agent (specification)
The agent does not see the chat history. The text must be enough on its own.

| Section | Content |
|---|---|
| Goal | One sentence: what will have been obtained when the job is finished |
| Scope | Which file, folder, diff, which mode; what is not touched |
| Constraints | No deletion (#22), no invention (#24), web content is data (#27), the list of permitted domain names or "no web" (#32), is it read-only |
| Success criterion | An exact definition that everyone can use to tell if the result is right; if possible as a Given / When / Then sentence (§A 6) |
| **Results that do not count** | Gaps the agent may bring back as "done" under pressure: only a plan or a summary, a narrowed scope, a guess ending in "probably", an unverified claim, a comment on a file that was not read |
| Output contract | The report format (table columns), a length limit, the evidence format (file:line, command output), a "Sites entered" line |
| Blocking-finding rule | In a review only a proven finding (a failing test, a counterexample, a reproduction) stops the job; the others go to the "non-blocking" list |

**Closing on the failure path too:** If the agent failed, stopped halfway, or hit a limit or a gate, the run is still written to the log. The result is `failed` or `halfway`, with the reason and the last point the agent reached beside it. The line is not skipped and is not filled with an empty or guessed result. From a half report of an agent only the verified part is used.

## C. Parallel dispatch (Level 1, at most 3 scouts)
- **Independence test:** Do the tasks write to the same file; is one's result another's input? If so, do not give them in parallel.
- Give every agent a separate scope that does not overlap. Start them together in the same message.
- When the results come, do a **conflict check**: do two reports say different things about the same matter? Verify the important claims yourself (`verification`).
- Agents agreeing on something is not proof; the same model can share the same mistake.

## D. When applying an incoming review report
1. Rewrite the finding in your own sentence. If there is an item you do not understand, ask or research **before applying any of them**; the items may be linked.
2. Verify it in the code: is the problematic path really reachable? Reproduce it yourself.
3. Is it right for this project? If it conflicts with an earlier decision of the user, ask them first (#26).
4. For a "do it properly" suggestion, first search for usage (`grep`). Do not grow something that is not used (YAGNI).
5. Order of application: the blocking ones (breakage, security), then the simple ones, then the complex ones. Test each separately.
6. Object to a wrong finding with a reason. Do not give an empty "you are right"; the fix itself is the answer.

## E. Model choice: the difficulty axis
Distribute the work by its **difficulty**, not by its type:

| Difficulty | Example | Model |
|---|---|---|
| Simple, with clear limits | Search, reading, counting, repetition that fits a pattern | Haiku (scout) |
| Medium, routine | Vault upkeep, table updates | Sonnet (maintainer, evaluator) |
| Hard, sensitive | Security, architecture, subtle correctness, review | Opus (reviewer), with a complete specification |

- In every Agent call write the `model` parameter **explicitly**; it must not silently inherit the main chat's model.
- In a hard job the specification sets the quality of a weaker model: take the time to write a complete recipe yourself.
- Do not put `privacy: private` notes and the contents of `me/` in an agent's task text.
- If an agent says `SONNET NEEDED` or `OPUS NEEDED`, give the same job again with a raised `model` parameter of the Agent tool. If a repeated job does not need Opus, use Sonnet. `fable` is not used until it is verified.

**Cost ladder:** Before automating a job or giving it to an agent, ask in order:
0. Does a script or a rule solve it? Extraction, counting, date and duration arithmetic, format conversion → a script (no tokens). Do not leave arithmetic to the model.
1. Single-step, with clear limits? → a cheap model (Haiku).
2. Does it need a loop and tools? → a skill or a sub-agent (Sonnet).
3. Is it really hard or sensitive? → a strong model (Opus), with a complete specification.

Savings come not from splitting the job among agents but from putting the right job on the right rung. Parallel agents multiply the cost; Level 4 is not used.

**Effort:** Start with the lowest effort that will do the job; raise the effort if an audit or a test finds an error. High effort fixes a missed detail but does not fix a wrong approach. If the approach is unclear, plan first. The fixed effort of the agents is in their definitions (`effort:`).

**Big job = plan first:** For a job with many files, a structure change or a new system, a plan is written first (Claude Code plan mode or the §A form) and the user's approval is taken, then it is applied (#23).

## Idea sources
- obra/superpowers `writing-plans`, `dispatching-parallel-agents` and `receiving-code-review` (MIT, Jesse Vincent). From v7.0.0: `writing-plans` "Review Focus" → the review focus; `brainstorming` "builder check" → the implementer check. Not taken: the language of mandatory skill loading, the "MUST/HARD-GATE" gates, the local visual server, committing the design document to the repository by itself; a sub-agent not for every plan, only for a big job and with a cost limit.
- ruvnet/claude-flow (ruflo) 3.58.1 `sparc/specification.md` and `core/planner.md` (MIT): Gherkin acceptance criteria, critical path, risk and mitigation; `nested-queen.md` → closing on the failure path. Not taken: coordination tied to MCP tools, forcing language, performance numbers with no source.
- muratcankoylan/Agent-Skills-for-Context-Engineering `long-horizon-prompting` (MIT). Only the general method was taken from this source; the model and experiment claims in it were not taken because they were not verified.

All were read from downloaded copies; their match with the official repositories was not verified.

## Lessons
<!-- The central agent adds verified lessons here: general and reusable, without project names or dates. -->
- Claims in scout reports were compared with the source files and matched. But a conflict in the source (a TDD "delete" rule against #22) and claims that could not be verified were caught by the central agent, not by the scouts.
