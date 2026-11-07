---
name: debugging
description: Use when you meet an error, a failing test, unexpected behavior, slowness or a build error, BEFORE proposing a fix. No fix is made before the root cause is found. The main chat and every agent that writes code load it; the reviewer may load it when a root-cause analysis is needed.
---

Method skill (not an agent). Works together with rule #24 (verify first) and §7.3 (problem and solution) of the vault `CLAUDE.md`.

## Basic rule
**No fix without a root cause.** Suppressing the symptom (e.g. swallowing the error with `try/except`, adding a magic wait) is not a fix; the problem comes back somewhere else.

## 0. Vault first
Search `problems/` for the error message and for similar meaning (`grep`, `search.py`; §7.3, rule #38). If a recorded solution exists, try it first; do not retry in the same conditions one marked ✗ in the "Tried solutions" table. Write the result (✔/✗/~ and why) into the table; if it did not work, look for a new one without deleting the old one.

## 1. Root-cause investigation (before fixing)
- **Read the error message to the end:** stack trace, file:line, error code. The answer is often there.
- **Reproduce:** Are the steps exact, does it happen every time? If it cannot be reproduced, do not guess; collect data.
- **Look at recent changes:** `git diff`, recent commits, new dependency, setting, environment difference.
- **In a multi-layer system, measure the boundaries:** At each component boundary (e.g. script → subprocess → file) print the data going in and coming out once. Prove at which layer it breaks, then go down into that layer.
- **Trace the data backwards:** Where did the wrong value come from, who called with this value? Go up to the source; fix at the source.

## 2. Pattern comparison
- Find similar working code in the same project. List **every** difference between the working one and the broken one (do not say "this can't matter").
- If you are applying a pattern or an example, read the reference from start to end; do not skim.

## 3. Hypothesis and test
- Write a single hypothesis: "X is the root cause, because Y."
- Test with the **smallest** change; one variable at a time. If it did not hold, do not add a new fix on top; revert the change and form a new hypothesis.
- If you do not understand, say "I don't understand X" (#24). Do not pretend.

## 4. The fix
- First write a **failing test** that catches the error, or a small reproduction script (`test-writing`). See the test fail.
- **One** fix for the root cause. No "while I'm here" improvement or bulk refactor (#23, #25).
- Verify (`verification`): the test is green, other tests are not broken, the original symptom is really gone.

## The 3-attempt rule
Once three fix attempts have been made, **stop**. If every fix opens a new problem somewhere else, the problem is most likely in the design, not in a single line. Before a fourth attempt, write to the user the situation, what was tried and the architectural question.

## Stop signs
If any of these crosses your mind, go back to step 1:
- "Let me patch it quickly for now, I'll look later."
- "Let me change this and see."
- "Let me change a few things at once and run the tests."
- "It's probably X."
- Writing a list of solutions without tracing the data flow.
- Warnings from the user such as "don't guess" or "isn't this working?".

## When there really is no root cause
If the problem comes from the environment, timing or an external service, write what was investigated, put in a suitable mitigation (timeout, retry, meaningful error message) and add a record. This is rare; most of the time the investigation was incomplete.

## When done
Write the solved problem to `problems/` or update the existing note (`/problem`): symptom (error message verbatim), root cause, valid solution, **all attempted solutions with their results** (including the ones that did not work, rule #38), how to prevent it.

## Idea sources
- obra/superpowers `systematic-debugging` (MIT, Jesse Vincent). Read from a downloaded copy; its match with the official repository was not verified.

## Lessons
<!-- The central agent adds verified lessons here: general and reusable, without project names or dates. -->
