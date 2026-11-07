---
name: expert-backend
description: Backend and database expertise pack. Load when working on or reviewing an API, server-side business logic, a database schema, a query, a migration, authentication, a queue or an external service integration.
---

Expertise pack (not an agent). First look for the project's rules, ADRs and related errors in `problems/` (#26).

## Checklist
- [ ] Is input validation done at the boundary (type, length, range, format)? Do not trust the client.
- [ ] Is SQL parameterized (no string concatenation)? If an ORM is used, were raw queries checked separately?
- [ ] Are transaction boundaries right? Is no partial write left behind? Is there a race condition under concurrency?
- [ ] Is the migration reversible? Is there a risk of data loss? Would it lock a large table? Back up or use a test environment first.
- [ ] Query efficiency: N+1, missing index, unbounded `SELECT *`, pagination.
- [ ] Error handling: meaningful error codes; internal detail (stack trace, query) does not leak to the client; no secrets in logs.
- [ ] Authentication and authorization: authorization check on every endpoint, least privilege.
- [ ] Secrets are in `.env` or a secret store; they are not written into code or the vault (#18).
- [ ] External service calls: timeout, retry limit, idempotency.
- [ ] Tests: happy path + edge cases + error path.

## Verification
- Really run the change (test, sample request). Show the output. Do not invent numbers (#24).
- Database operations are **never** tried on real data; deletion or bulk update only with the user's approval (#22).

## Common mistakes
- Writing a migration that cannot be rolled back.
- Time zone and date confusion (store UTC, convert when displaying).
- Swallowing an error silently (`except: pass`).

## Additional methods
Ideas are in our own words.
- **API design:**
  - [ ] Resource names and URL structure are consistent; HTTP status codes are right (400 validation, 401/403 authorization, 404, 409 conflict).
  - [ ] The error body has the same format on every endpoint.
  - [ ] List endpoints have pagination and an upper limit.
  - [ ] Write requests that may be retried carry an idempotency key.
  - [ ] Breaking changes are versioned.
- **Migration:**
  - Follow the expand → migrate → contract order: add the new column first, move the data, remove the old one last.
  - On a large table, do the operation in batches.
  - Every migration has a written rollback step.
- **TDD cycle:** red (failing test) → green (smallest code) → refactor. One vertical slice at a time. When fixing a bug, first write the test that catches it.
- **Systematic debugging:**
  1. Reproduce the error.
  2. Collect evidence (log, input).
  3. Form a single hypothesis, change one variable to test it.
  4. Find the root cause. Fix the cause, not the symptom.
  5. After the fix, verify with the same steps.

  Search `problems/` first.
- **Silent-failure hunt:** swallowed exceptions, empty `catch`, hiding an error behind a default value, unchecked return values.
- **Circuit breaker:** Stops sending requests to an external service that keeps failing.
  - It has three states. **Closed:** requests pass, consecutive errors are counted. **Open:** once the threshold is exceeded no request is sent; an error or a fallback answer returns immediately. **Half-open:** when the wait time ends, a single trial request passes; if it succeeds the breaker closes, otherwise it opens again.
  - Used together with retry: first a limited retry with growing waits (exponential backoff + jitter), and outside it the circuit breaker. Only transient errors (timeout, 503) count; client errors such as 400 do not.
  - Check: are the threshold, the wait time and the fallback behavior written down? Is it logged when the circuit opens? Is the closed → open → half-open → closed transition tried in a test with a fake service?
  - When it is not needed: a single-user local tool, no external service. No needless layer is added (#25).
  - Idea source: ruvnet/claude-flow (ruflo) 3.58.1 `sparc/refinement.md` (MIT). No code example was taken.
- Idea sources: obra/superpowers (`systematic-debugging`, `test-driven-development`), mattpocock/skills (`tdd`, `diagnosing-bugs`), everything-claude-code (`api-design`, `database-migrations`), anthropics `pr-review-toolkit` (silent-failure-hunter).

## Lessons
<!-- The central agent adds verified lessons here: general and reusable, without project names or dates. -->
