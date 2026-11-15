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
| `v1.2.2` (security update, latest) | ✅ |
| `v1.2.1` (security update) | ✅ (a `hooks:` field in a skill or agent definition is not asked: update to v1.2.2) |
| `v1.2.0` (security update) | ✅ (on Python 3.10 the command guard does not load: update to v1.2.1) |
| `v1.1.0` and older | ❌ (please update, see [CHANGELOG.md](CHANGELOG.md)) |

## What Mindgate does on your computer

Mindgate is not a service. It has no server, no account and no telemetry. The update check in `health.py` is off
by default; when you turn it on, it asks one fixed GitHub address for the latest release number and sends nothing
from the vault.

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

### What the guards check (since v1.2.0)

- **Defense files.** Changing the guards' own ground is asked: the hook and
  permission settings of every supported assistant, the vault scripts in
  `_system/`, `config.json`, agent definitions, scheduled tasks, git hooks, the
  blocklist, the rules, the instructions and the vault schema. One list
  (`common.DEFENSE_SET`) serves the write guard and the command guard.
- **Network calls from the shell** are asked, with the address in the reason:
  download tools, raw sockets and remote shells, remote paths, .NET network
  classes, network code given to node/deno/bun or Python, opening an address in
  the browser, `git clone`/`git remote`, `gh api`. Piping a download into an
  interpreter is refused. A web search (`WebSearch`) is asked like a page.
- **Hidden command names** (quotes or backslashes inside the name, prefixes
  such as `command` or `env`, a name computed with `$(…)`) are checked as the
  real command or asked.
- **Long commands.** A command over 20,000 characters is asked (refused in an
  unrecorded chat) before any pattern runs, so no input can run out the hook's
  time limit.
- **Broken helpers.** If a guard cannot load its helper modules it asks (other
  assistants: refuses) instead of crashing, and a file named after a standard
  library module in `_system/` cannot take its place.
- **Hooks in skill and agent definitions** (since v1.2.2). A `hooks:` field in
  the frontmatter of a `SKILL.md` or an agent definition runs a command on
  every tool call without passing `settings.json`. Writing one is asked, and
  `health.py` names the definitions that already have one.
- `health.py` reports missing or narrowed security hooks, broad permission
  patterns, a bypassed commit hook and uncommitted changes in the guard scripts.

### Known limits

- **A script that writes indirectly is not seen.** `py tool.py` that edits a
  guard file passes the command guard when the path is not on its command line;
  `health.py` shows the uncommitted change afterwards.
- **Values built at run time are not resolved:** a path or command name kept in
  a variable (`$p`, `%P%`) or joined from strings is not seen by the guard.
- The read tools pass no guard; `.env` files are protected only in the shell.

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
