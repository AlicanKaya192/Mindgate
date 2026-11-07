---
name: clean-code
description: Clean code rules and a checklist to run before finishing. Applied when writing, changing, proposing or reviewing code (rule #30). Preloaded into all agents; the main chat also follows it in every coding task.
---

Method skill (not an agent). Source: Robert C. Martin, *Clean Code* (Prentice Hall, 2008); for Python, PEP 8 (https://peps.python.org/pep-0008/). Summarized in our own words.

## Order of priority
1. The project's own rules, formatter and linter (`<project>-rules.md`, PEP 8, ESLint, Prettier, `ruff`…) and the style of the surrounding code.
2. This list.

If they conflict, the project's wins. Rules #23 and #25 apply: clean code is mandatory for the code **you write and touch**. "Cleaning" code you did not touch is unrequested work; suggest it if needed, do not do it.

## 1. Names
- Reveal intent: `day_count`, not `d`. Searchable and pronounceable. A single letter only for a short loop counter.
- Class and variable names are nouns, function names are verbs (`calculate_average`). Booleans read like questions (`is_active`, `is_valid`).
- One word per concept everywhere (`get` or `fetch`, pick one). Do not mix the project's language (Turkish or English).
- No magic numbers or strings: use a named constant or configuration (`MAX_RETRIES = 3`).

## 2. Functions
- Small, doing **one thing**. One level of abstraction per function.
- Few parameters: 0–2 is ideal. With more than 3, gather them in an object or a data class.
- Do not do two different jobs behind a boolean flag parameter; split into two functions.
- No hidden side effects; if there are any, the name says so. Keep commands (change state) and queries (return a value) apart.
- Use early returns (guard clauses) instead of deeply nested `if`.

## 3. Comments
- The code should explain itself. A comment explains **why**, not what is done.
- No commented-out dead code, no wrong or outdated comments. Update the comment when you change the code.
- Short docstring on public APIs. No AI traces in comments or code (#14).

## 4. Error handling
- Use exceptions instead of returning error codes. Errors are **not swallowed** (`except: pass`, empty `catch`).
- The error message carries context (what, which input). No secrets in it (#18).
- Instead of returning and passing `None`/`null`, use an empty collection, `Optional` or an explicit exception.
- Input is validated at the boundary (API, CLI, file); it is not re-checked again and again inside.

## 5. Classes and modules
- Single responsibility (SRP): one reason to change.
- High cohesion, low coupling. Depend on an interface, not a concrete class (DIP).
- Prefer composition to inheritance.
- Put an external library behind a thin wrapper so a change touches one place.

## 6. Simplicity
- **DRY:** The same knowledge and logic in one place.
- **No premature abstraction (YAGNI):** Do not generalize before a real need and repetition show up. Factor out on the third repetition.
- **KISS:** The simplest solution that works.
- Do not leave dead code, unused imports, variables or parameters.

## 7. Formatting
- Run the project's formatter. Keep related code close together; a file reads top to bottom (high level first, then detail).
- Reasonable line and file length; a file carries one topic.

## 8. Tests
- **F.I.R.S.T.:** fast, independent of each other, repeatable in any environment, self-validating (pass/fail), written together with the code.
- One concept per test. Arrange–Act–Assert order.
- Test code is clean code too.

## Check before finishing (in every coding task)
- [ ] Names reveal intent; no magic numbers.
- [ ] Each function does one thing; no flag parameters or deep nesting.
- [ ] Errors are not swallowed; messages are meaningful.
- [ ] No repetition, no needless abstraction, no dead code or unused imports.
- [ ] Comments explain "why"; no outdated comments.
- [ ] The formatter/linter ran (if any) and the tests passed. The output was shown (#24).
- [ ] The change did not go beyond the requested scope (#23, #25).

## In review (reviewer)
A clean-code violation is a finding. Its importance is usually **low** or **medium**; it does not come before correctness and security findings. For each finding, name the rule broken (e.g. "2. one thing").

## Lessons
<!-- The central agent adds verified lessons here: general and reusable, without project names or dates. -->
