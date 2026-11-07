---
name: expert-server
description: Server, deployment and network expertise pack. Load when working on publishing an application (deploy), a reverse proxy, a port, a domain name and TLS, CI/CD, server configuration, logging and monitoring, or a local development server.
---

Expertise pack (not an agent). On this computer rules #19 and #20 are absolute.

## Hard rules (this computer)
- If a port is taken, **do not kill** the process; pick a free port (`netstat -ano | findstr :<port>` or `Get-NetTCPConnection`) and set the project to that port. Using port 0 in code lets the operating system pick a free port.
- Never kill a process by name. By PID only after verifying its owner and asking the user.
- No changes to the firewall, services, scheduled tasks or the registry (HKLM). No shutdown or restart.
- Outward-facing actions such as connecting to a remote server, publishing or changing DNS only with the user's approval (#23).

## Checklist
- [ ] Configuration via environment variables or a file; secrets in `.env` and outside git.
- [ ] TLS on, HTTP → HTTPS redirect; security headers (HSTS, CSP, X-Content-Type-Options).
- [ ] Reverse proxy timeout, body size limit, rate limit.
- [ ] A health check endpoint; graceful shutdown.
- [ ] Logging: structured (JSON), rotating, no secrets in it.
- [ ] Rollback plan: how to return to the previous version?
- [ ] CI: tests, dependency scan, secret scan; secrets in CI secret variables.
- [ ] Least privilege: the service user is not root or administrator.

## Verification
- Run the change locally or in a test environment and show the result (#24). Before saying "I deployed it", really call the health check.

## Additional methods
Ideas are in our own words.
- **GitHub Actions security:**
  - [ ] Third-party actions are pinned by commit SHA (not by tag).
  - [ ] `permissions:` is defined with least privilege.
  - [ ] Code from a fork is not run with `pull_request_target`.
  - [ ] Untrusted input (such as `${{ github.event.issue.title }}`) is not put directly into `run:`; it is passed through an environment variable (command injection).
  - [ ] Untrusted content (issue, PR text) is not given to workflows that run an AI agent.
- **Observability:** three signals (log, metric, trace); meaningful alarm thresholds; a short runbook for every alarm (what to do).
- **After an incident:** a blameless postmortem. Timeline, impact, root cause, fix and a step to prevent recurrence. Written to `problems/`.
- **Terraform/IaC:**
  - The `plan` output is shown; `apply` and `destroy` with the user's approval.
  - A state file may contain secrets; it does not enter git.
  - Provider and module versions are pinned.
- Idea sources: trailofbits/skills (`agentic-actions-auditor`), semgrep/skills (`code-security`: GitHub Actions checks), hashicorp/agent-skills (Terraform), wshobson/agents (`observability-monitoring`, `incident-response`).

## Lessons
<!-- The central agent adds verified lessons here: general and reusable, without project names or dates. -->
