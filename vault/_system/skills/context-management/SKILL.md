---
name: context-management
description: Use when the context is nearly full in a long session, when a large read or tool output arrives, when writing a session summary or handoff note, or when the model starts mixing up earlier information. The main chat loads it; the maintainer may load it when processing session records.
---

Method skill (not an agent). It details rule #16 (record before the context resets) and §7.8 of the vault `CLAUDE.md`.

## Measure: spending per task
Look at the total spending of a task from start to finish, not at spending per message. If a summary drops a file path, an error message or the reason for a decision, the same files are read again and more is lost than gained. Reading the same file again and again is a sign that the summary is bad.

## Thresholds and automatic routine
- **40% (end of a task):** The hook says once "continue if a task is running". If a task has just finished and a new topic is coming: write the handoff card, process the unprocessed items into the vault, and suggest a new chat or `/clear` to the user. `/clear` is free; `/compact` reads the whole conversation, so it is a large request, and it brings back the skills already used. **Early compaction is not recommended in a running task:** in a half-finished task the summary drops file paths and error details, the same files are read again, and more is lost than gained.
- **60% (warning):** The Stop hook (`context_check.py stop`) says once "write the handoff card, process the unprocessed items into the vault". In order:
  1. Handoff card: the half-finished task and the exact step you stopped at, the next steps, open questions.
  2. Ideas, decisions, problems/solutions, progress and rules that were discussed but not yet written to the vault.
  3. Log, commit. Then continue the task.
- **70% (compaction):** Claude Code compacts on its own (`CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`, value in `config.json` → `context`). The PreCompact hook adds a "what to keep" instruction to the summary; the PostCompact hook saves the summary under `inbox/sessions/`. After compaction, the SessionStart reminder makes you read the record and process what is missing.
- **One chat, one task:** When a task (chapter, release, feature) is finished, write the handoff card and suggest a new chat to the user. A chat that runs for weeks rereads hundreds of thousands of tokens at every message (measure with `cost.py`).

## Mandatory sectioned summary
When writing the session state (to the vault, a progress file or a handoff note), these sections are **never left empty**:
- **Goal:** what the user wants (in their own words).
- **Files:**
  - created (full path)
  - changed (what changed, by function name)
  - read but unchanged
- **Decisions and their reasons.**
- **Current state:**
  - with evidence, e.g. "94/94 tests passed"
  - open errors, error message verbatim
- **Pending:** approvals and questions expected from the user. Use the same numbers as `inbox/pending.md`.
- **Next steps.**

The sections work like a checklist: an empty section shows what was forgotten. The summary is not regenerated from scratch each time. Only the new part is summarized and added to the existing sections; regenerating from scratch loses detail every round.

## Test the summary (probe questions)
After the summary, ask yourself; if the summary cannot answer them, it is incomplete:
- Recall: "What was the original error message?"
- File trail: "Which files did we change?"
- Continuation: "What is the next step?"
- Decision: "What did we decide about X, and why?"

## Put large output in a file
- Write large tool output (test lists, scan results, long logs) to the scratchpad. Only a short summary and the file path enter the context; read it with `grep` or a line range when needed.
- Give multi-file reading to the `scout` agent. Tell it you want a short, sourced report.

## Signs of context degradation
| Sign | What to do |
|---|---|
| Lost in the middle: information in the middle of a long context is forgotten | Move critical information (rules, goal) to the start or the end; reread it from the vault |
| Poisoning: a wrong piece of information is used again and again | Do not add a correction on top of the error. Declare the wrong part invalid explicitly and reread the right one from the source |
| Distraction: unrelated content splits attention | Do not load what is not needed; fetch it with a tool when required |
| Conflict: two sources say different things | Source priority: the user's last word > vault rule and ADR > older note > memory. Write the conflict down (`> [!warning] Conflict`) |

## Idea sources
- muratcankoylan/Agent-Skills-for-Context-Engineering (MIT): `context-compression`, `context-degradation`, `filesystem-context`. Read from a downloaded copy; its match with the official repository was not verified.

## Lessons
<!-- The central agent adds verified lessons here: general and reusable, without project names or dates. -->
