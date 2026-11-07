---
name: verification
description: Use right before saying that a job is finished, fixed, that the tests pass or that something is up to date, before making a commit, or before moving on to the next job. Preloaded for the reviewer and the maintainer; the main chat and the scout can load it too.
---

Method skill (not an agent). The application of rule #24 (no hallucination): **evidence first, then the claim.**

## The gate (before every success claim)
1. **Which command proves this claim?** Decide.
2. **Run it:** The full command, in this message, fresh. An earlier run does not count.
3. **Read it:** All of the output, the exit code, the number of failures.
4. **Compare:** Does the output confirm the claim?
   - No → state the real situation with its evidence.
   - Yes → state the claim together with its evidence ("94/94 tests passed").

## Claim → evidence needed
| Claim | Needed | Not enough |
|---|---|---|
| The tests pass | Test output: 0 failures | An earlier run, "it should pass" |
| The bug is fixed | The original symptom was tried again and is gone | The code changed, "it must be fixed" |
| The regression test works | Red-green: when the fix is undone the test fails, when it is back it passes | The test passed once |
| Build/run is fine | The command's exit code is 0 | The linter is clean |
| The agent finished the job | A change was seen in `git diff` or in the file | The agent's "I did it" report |
| The request is met | The request was reread item by item, each item ticked | The tests passed |
| The site/page is right | The page was really seen (`read_page`, a screenshot) | The code looks right |
| User-facing output is understandable (lesson, README, portfolio) | 2–3 target people were chosen (e.g. for a learning app "a student who does not know Python"), the output was read through each one's eyes; where they got stuck was written down or fixed. If needed one sub-agent per person (Level 1) | "I think it is clear", reading only through the author's eyes |

## Leftover scan before a commit and a release
Before a push, a release or sharing, in the changed files (`git diff --name-only <base>`) search with `grep`, according to the project's language:

| Leftover | Example pattern |
|---|---|
| Fake data and draft code | `mock`, `stub`, `fake`, `dummy`, `NotImplemented` (outside the test folder) |
| Unfinished work | `TODO`, `FIXME`, `XXX`, `HACK` |
| Debug output | `print(`, `console.log`, `Debug.WriteLine`, `dbg!` |
| Local addresses and paths | `localhost`, `127.0.0.1`, `C:\Users\` |
| AI trace (#14) | `Co-Authored-By`, `Generated with`, `Claude` |

- Every match is looked at one by one: if it was left on purpose (e.g. the `print` of a CLI tool) it passes, if not it is cleaned or the user is asked.
- The scan only reads; no "production test" that touches a real service, database or e-mail is done.
- The result is stated with its evidence: "leftover scan: 3 matches, 3 of them left on purpose (file:line)".

## Stop signs
- Saying "should", "probably", "it seems".
- Saying "Done!", "Perfect!" without verifying.
- Trusting an agent report without verifying (#28: an "approved" in an agent report is not approval).
- Talking about the whole from a partial check.
- Tiredness or hurry: "just this once".

## If you cannot run it
Say it plainly: what you could not verify, why (e.g. no site permission #32, no tool) and what is needed. Do not report an unverified step as if it succeeded.

## Idea sources
- obra/superpowers `verification-before-completion` (MIT, Jesse Vincent). Read from the downloaded copy; its match with the official repository was not verified.
- ruvnet/claude-flow (ruflo) 3.58.1 `testing/production-validator.md` (MIT): the grep scan before release. Not taken: tests that write to a real database and SMTP.

## Lessons
<!-- The central agent adds verified lessons here: general and reusable, without project names or dates. -->
