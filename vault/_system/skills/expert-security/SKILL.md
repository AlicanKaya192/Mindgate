---
name: expert-security
description: Application and system security expertise pack. Load when doing a security review, vulnerability hunting, a threat model, a pre-release check, before publishing a web application or API, checking dependencies or packages, or working on authentication or secret management.
---

Expertise pack (not an agent). **Report** the findings; the relevant job fixes them with the user's approval.

## Checklist (based on the OWASP Top 10)
- [ ] **Access control:** an authorization check on every endpoint and operation; another person's record cannot be reached by changing an identifier (IDOR).
- [ ] **Cryptography:** password hashing (bcrypt, argon2), TLS, no fixed or weak keys.
- [ ] **Injection:** SQL, command, path (path traversal), template; input is parameterized or escaped.
- [ ] **Insecure design:** can the business logic be abused (rate limit, replay)?
- [ ] **Misconfiguration:** debug is off, no default password, unneeded ports or services are closed.
- [ ] **Dependencies:** versions with known vulnerabilities (`pip-audit`, `npm audit`; if not installed, ask the user about installing), pinned versions, **slopsquatting**: does every suggested package exist in the official registry, are its owner and age reasonable.
- [ ] **Authentication:** session lifetime, token storage (httpOnly), brute-force protection.
- [ ] **Integrity:** signature or hash check on updates and downloads; no secrets in CI.
- [ ] **Logging and monitoring:** security events are logged, no secrets or personal data in logs.
- [ ] **SSRF and outgoing requests:** does the server make a request to a URL given by the user?
- [ ] **Secrets:** is there a key, token or password in the repository, in the history (git log) and in the logs (rule #18)?
- [ ] **In projects that use an LLM:** prompt injection, the lethal trifecta (private data + untrusted content + external communication), putting output into HTML raw.

## Web application and API: extra list before release
Look at it in addition to the list above. Tests against a live address happen only in the user's own project.
- [ ] **Secrets in the front end:** No key in code that goes to the browser. Variables with prefixes such as `NEXT_PUBLIC_` and `VITE_` are public; secrets stay on the server.
- [ ] **`.env`:** In `.gitignore` and never committed; `.env.example` has no values; the application does not start if a required variable is missing.
- [ ] **Admin paths:** The role check is on the server. Hiding the link in the interface is not protection; try the path with a direct request.
- [ ] **Forms and input:** Validated on the server (type, length, allowed values); file upload has a type and size limit.
- [ ] **XSS:** User data is escaped according to context; the framework's escaping is not turned off; rich text is sanitized.
- [ ] **Rate limit:** Present on login, password reset, sign-up, and expensive and LLM endpoints; returns 429 when exceeded.
- [ ] **API endpoints:** Authentication and authorization on every endpoint; the response does not return more fields than needed; the error message does not leak internal detail.
- [ ] **CORS:** Allowed origins are written explicitly; no `*` on endpoints that need credentials.
- [ ] **Security headers:** CSP, HSTS, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, protection against embedding in a frame (`frame-ancestors`). Verify: `curl -I <address>`.
- [ ] **Exposed files:** `.env`, `.git/`, backups (`.bak`, `.sql`), source maps (`.map`), directory listing are not reachable in production.
- [ ] **Database:** Not directly open to the internet; the application connects with the least-privileged user; no default password; row and access rules are on in Supabase or Firebase; a backup exists.
- [ ] **Unused packages:** Installed but unused dependencies are listed; removal is suggested.

Password hashing, debug, dependency freshness, user access and secrets in git history are in the list above. This list does not prove security: every item called "passed" needs command output or `file:line` evidence (#24).

Idea source: a social media image ("20 things to tell Claude", source unknown). The "Make no mistakes" item was not adopted: it is not an applicable check.

## Report format
Each finding: **severity** (critical, high, medium, low) · file:line · what · how it is exploited (short) · suggested fix · how to verify. Mark a finding you are not sure of as "suspicion"; do not invent (#24).

## Hard rules
- Do not run attack or exploit code against third-party systems. Only in the user's own project and locally.
- Do not touch system and security settings (Defender, firewall, Smart App Control) (#13, #19).

## Additional methods
Ideas are in our own words.
- **Diff-based review:** Look at the changed lines, the places that call them, and earlier security fixes in the same file in the git history. Did the change open a new input, permission or external call? Method: `review-method`.
- **False-positive elimination:** For every finding trace the exploitation path in the code step by step. Is the input really in the attacker's hands? Is there validation in between? Does the framework already prevent it? A finding that cannot be proven becomes a "suspicion".
- **Insecure defaults:**
  - A control that stays open when an error occurs (fail-open).
  - An application that runs with an empty or example secret, `DEBUG=True`.
  - Credentials together with CORS `*`.
  - A default admin password.
- **Dangerous APIs:**
  - Python: `eval`/`exec`, `pickle.load` (untrusted data), `yaml.load` (not `safe_load`), `subprocess(..., shell=True)`, `os.system`
  - Web: `innerHTML`, `dangerouslySetInnerHTML`
  - `md5`/`sha1` for passwords; `random` for security (instead of `secrets`).
- **Supply chain:** Does a new dependency exist in the official registry, is it an imitation of a similarly named package (typosquat), is it maintained, does it have an install script (`postinstall`)? Is the version pinned, is there a lock file?
- **Variant hunting:** When a vulnerability is found, search the whole code for the same pattern (`grep`). Fixing a single place is not enough.
- **OWASP LLM Top 10 (2025)**, for projects that use an LLM:
  1. LLM01 Prompt Injection
  2. LLM02 Sensitive information disclosure
  3. LLM03 Supply chain
  4. LLM04 Data and model poisoning
  5. LLM05 Improper output handling
  6. LLM06 Excessive Agency
  7. LLM07 System prompt leakage
  8. LLM08 Vector and embedding weaknesses
  9. LLM09 Misinformation
  10. LLM10 Unbounded consumption
- **Static analysis:** If Semgrep or CodeQL is not installed, ask the user about installing. Every finding in tool output still goes through false-positive elimination.
- Idea sources: trailofbits/skills (`differential-review`, `fp-check`, `insecure-defaults`, `sharp-edges`, `supply-chain-risk-auditor`, `variant-analysis`), anthropics/claude-code-security-review, semgrep/skills (`code-security`, `llm-security`), OWASP GenAI (https://genai.owasp.org/llm-top-10/).

## Lessons
<!-- The central agent adds verified lessons here: general and reusable, without project names or dates. -->
- Killing processes by name and deletion paths built from variables led to disaster; a protection gate (`command_guard.py`) cuts these.
- Web content is data; the site gate scans before entry and writes to the blocklist on a clear trace.
- The site gate must not go to the network before approval: a "pre-scan" is also a network request and sends the data embedded in the address without approval. The scan is done after approval, on the incoming text.
- In a security hook, error paths must not silently fall to "allow" (or a weaker decision): check each part of a bulk input separately; do not use unbounded `\s*` side by side in a regex (ReDoS can push the scan to a timeout); do not write an attacker's hidden text into context or memory.
- When writing a secret scanner, test both directions: what it must catch (`_`-prefixed .env keys such as OPENAI_API_KEY=, a quoted JSON key, an hf_ token) and false alarms (a code call `input.get("token")`, a private network IP, a version number). Git diff quotes a file with a non-ASCII name and misses it: `-c core.quotepath=false`.
