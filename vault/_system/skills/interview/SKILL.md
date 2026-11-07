---
name: interview
description: Use when the user says "interview me", "ask me questions" or "let's clarify this together", or when the vault's information on a new project, goal or decision is incomplete; it asks the user questions one at a time and writes the answers into the relevant notes. The main chat loads it.
---

Method skill (not an agent). Rules: #4 (do not ask what is in the profile), #3 and #18 (no sensitive information), #15 (no teaching), #23 (only the requested topic), #24 (do not invent answers). Idea source: the "grill-me" pattern; no code was taken, it is our own method.

Purpose: to move what is in the user's head into the vault. The real gap is often not in the search but in information that was never written.

## Steps
1. **Limit the topic.** Write in one sentence what will be asked about (e.g. "the next release goals of an app"). If the topic is unclear, clarify with one question.
2. **Read first, then ask.** `me/profile.md`, the related project page, ADRs, [[pending]] and `search.py "topic"`. Do not ask what is already in the vault, in the code or in an earlier answer. Do not open a closed topic or one the user said "I'll look at later" (#12).
3. **Build the question tree in your head:** first the main decision, then the details that hang on it. Do not show it to the user; go in order.
4. **One question at a time** (at most 3 short questions). In each question:
   - Say in half a sentence why you ask.
   - If the options are clear, use `AskUserQuestion`; if you have a recommendation, make it the first option and write "(Recommended)".
   - If your recommendation is a guess, say so: "I don't know, my guess is this".
5. **Write the answer at once.** Do not let it get lost before the chat ends:
   - Personal preference and goal → `me/profile.md` (no sensitive information)
   - Project information → the project page or `-progress.md`; a technical decision → a new ADR
   - The user's sentence without changing its meaning; `source_type: stated` in the frontmatter
   - If new information conflicts with the old, do not delete the old; `invalid` + `replaced_by` (§5)
6. **Stop condition:** the branches of the question tree are closed, the user says "enough", or the answers start to repeat. A question left unanswered goes to pending with `records.py pending add --type question`.
7. **Closing:** a short summary to the user: what was learned, which notes were updated, the open question. Then the log (`profile` or `progress`, with `Evidence:` and `Learned:`), commit (push if a remote is set), optional dashboard: not in v1, the [[skills-registry]] counter.

## Do not
- Turn the interview into a lesson or a quiz (#15). Do not re-argue the user's decision; ask only what is missing and what conflicts.
- Passwords, ID, address, health, bank and other people's private information are not asked and not written.
- Do not dump the whole list of questions and say "answer them all".

## Verify before finishing
- [ ] Every answer was written into a note and has a link; no information is left only in the chat.
- [ ] Nothing that was already in the vault was asked.
- [ ] Open questions are in pending.

## Lessons
<!-- The central agent adds verified lessons here: general and reusable, without project names or dates. -->
