<div align="right">
  <a href="./SECURITY.tr.md">Türkçe</a> · <b>English</b>
</div>

# Security Policy

## Supported versions

Mindgate is in early development. Reports are checked against the current
`main` branch.

| Version | Supported |
|---|:-:|
| `main` | ✅ |
| Older commits | ❌ |

## What Mindgate does on your computer

Mindgate is not a service. It has no server, no account and no telemetry.

- **The installer** writes only the places listed in the README's Security
  notes: the vault folder you choose, `~/.claude/CLAUDE.md` (or an import line
  in it), hooks in `~/.claude/settings.json`, skills, agents, scheduled task
  files and `~/.claude/mindgate/`. A file it changes is backed up first. It
  downloads nothing and installs no packages. `--dry-run` shows the full list.
- **The uninstaller** never deletes. It restores backups and moves installed
  files into `~/.claude/mindgate-removed-<time>/`.
- **The scripts make no network calls.** Web access only happens through
  Claude Code's own tools, when Claude decides to use them; the weekly task's
  web step is off unless you turn it on at install time.
- **Hooks run Python scripts with your user's rights** each time Claude Code
  reaches an event (before a tool call, at session start and so on).

> **The guards are not a sandbox.** The command, write and site guards and the
> agent gate catch known risky patterns and ask or refuse. They lower the risk
> of a model acting on bad instructions; they cannot stop every harmful
> command, and they do not make a model safe on their own.

## Reporting a vulnerability

These count as vulnerabilities, and reports are welcome:

- A way to get a command, file write or site visit past a guard that is meant
  to stop it (for example, a deletion outside the project that the command
  guard lets through)
- The installer or uninstaller writing, overwriting or deleting outside the
  places it lists, or losing a user file it should have backed up
- A script sending data off the computer, or opening a network connection
- A secret, personal path or personal data left in the repository or written
  into a vault by a script
- `secret_scan.py` or `security_scan.py` missing a pattern they claim to catch
- Text from a web page, file or tool output that makes a script, not just the
  model, act on it

These are not vulnerabilities in Mindgate: Claude choosing to ignore an
instruction when no guard is involved (that is model behaviour), and hooks
being able to run code (that is how hooks work; review them before you
install).

### How to report

**Do not post a vulnerability in a public issue.** Instead:

1. Open a private report through GitHub's
   [Security Advisories](https://github.com/AlicanKaya192/Mindgate/security/advisories/new),
   or
2. Write to a contact address on
   [the maintainer's GitHub profile](https://github.com/AlicanKaya192).

Please include the commit you tested, step-by-step reproduction, the likely
impact and, if you have one, an idea for a fix. Leave your own personal data
and secrets out of the report.

### What happens next

- Receipt is confirmed **within 48 hours**.
- **Within 7 days** you hear whether the issue is valid and how serious it is.
- If it is valid, you are kept informed until a fix is released.
- If you want, you are credited when the fix is published.

The project is run by one person in their free time; these timelines are
good-faith targets, not promises.
