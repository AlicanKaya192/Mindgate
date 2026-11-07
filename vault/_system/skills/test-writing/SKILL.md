---
name: test-writing
description: Use before writing code for a new feature, a bug fix or a behaviour change, and when testing a web interface. The main chat loads it; the reviewer may load it in the test coverage pass.
---

Method skill (not an agent). It works together with `clean-code` §8 (F.I.R.S.T.). The project's own test framework and rules come first.

## Red → green → refactor
1. **Red:** Write a test with a clear name that describes a single behaviour.
2. **See the red (not skipped):** Run the test.
   - The test must **fail** without raising an error.
   - The failure message must be the expected message.
   - The reason must be the right one too: the feature is missing, not a typo.
   - If the test passes at once, you are testing existing behaviour; fix the test.
3. **Green:** Write the least code that will make the test pass. Do not add unrequested features (#25).
4. **See the green:** Run this test and all the tests.
5. **Refactor:** Clean the code while the tests stay green (`clean-code`).

If you wrote the code before the test: **do not delete** that code (#22). Set it aside and write the test without looking at it. After the test shows red, use the code as the criterion. (The "delete and start over" rule in the source does not apply to us.)

## A good test
- One behaviour; the name describes the behaviour (`test_returns_zero_for_empty_list`).
- Real code instead of a mock. A mock is used only in unavoidable places such as an outside service, the clock or the network. Do not test the mock and think you tested the code.
- Arrange → act → assert. One concept per test.
- Boundary cases in separate tests: empty, a single element, very large, invalid input, the error path.
- **A test must not pass by accident:** For an important test, break the code on purpose and see the test fail. A test that always passes is worse than no test.

## A regression test in a bug fix
First comes the test that reproduces the bug (red), then the fix (green). The order of verification: undo the fix, the test must fail; put the fix back, the test must pass (`verification`).

## Web interface testing (explore first, act after)
1. If it is static HTML, first read the file and find the selectors there.
2. In a dynamic application let the page load and the network settle. In Playwright the equivalent is `wait_for_load_state("networkidle")`.
3. Then take a screenshot or inspect the DOM (in an in-app browser: `read_page`).
4. Choose the selectors by the **seen** state: role, text, id. Then do the action.

Additional rules:
- Do not look at the DOM before the page has loaded.
- A local server is also a page: the user's permission is needed before opening it (#32). If the port is taken, do not kill the process, pick a free port (#20).
- If Playwright is not installed on this computer, ask before installing it (#23).

## When a test is not written
Throwaway trial code, generated code and configuration files. If you are not sure, ask the user.

## Idea sources
- obra/superpowers `test-driven-development` (MIT, Jesse Vincent).
- anthropics/skills `webapp-testing` (Apache-2.0).

Both were read from downloaded copies; their match with the official repositories was not verified.

## Lessons
<!-- The central agent adds verified lessons here: general and reusable, without project names or dates. -->
- When a new file path constant (for example an archive directory) is added to the code, redirect it to a temporary directory in every test class that uses it, and put the new test in the class that redirects the paths. After the tests check with `git status` that no file was written to the real data folder (fake lines were written twice to the real archive).
- Tests of a gate that must not touch the network run without a network by forbidding socket creation; this way the claim "no network before approval" is tested too.
