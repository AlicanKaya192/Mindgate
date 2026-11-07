<div align="right">
  <a href="./CONTRIBUTING.tr.md">Türkçe</a> · <b>English</b>
</div>

# Contributing Guide

Issues and pull requests are open to anyone. Please read the
[Code of Conduct](./CODE_OF_CONDUCT.md) first. Security problems do not go in
issues: see [SECURITY.md](./SECURITY.md).

## How can I help?

- **Bug reports:** a guard that stops something harmless or lets something
  harmful through, an installer step that fails, a wrong translation.
- **New skills, agents or rules:** open an issue first and describe the
  problem they solve, so we can agree on the shape before you write it.
- **Translations:** Mindgate ships in English and Turkish. A new language
  needs a `locales/<code>/` folder that follows
  [TRANSLATION-GUIDE.md](./TRANSLATION-GUIDE.md).
- **Testing on macOS and Linux:** both are untested; reports from either are
  very welcome.

## Running the tests

You need Python 3.10 or newer. No packages are installed.

```bash
# installer and uninstaller (always uses a throwaway home under .yerel/)
cd setup
py -3 -I -B installer_test.py -v

# the vault scripts (from the vault/ folder)
cd vault
py -3 -I -B _system/run_tests.py
```

On macOS and Linux use `python3` instead of `py -3`. The tests make no network
calls and never touch your real `~/.claude` or your own vault.

## Rules for changes

1. **Both languages, together.** Text a user sees changes in English
   (`vault/`, `setup/`) and in Turkish (`locales/tr/`) in the same pull
   request. Code, frontmatter fields and script messages stay English in both.
   Names follow `locales/tr/names.json`.
2. **No personal data.** No real names, paths, e-mail addresses, machine
   names, project names or secrets in code, notes, tests or screenshots. Use
   `{{VAULT}}`, `{{HOME}}`, `{{PY}}` and neutral examples.
3. **Nothing is deleted.** The installer and uninstaller back up and move;
   a test fails if a deleting call appears in their code. Keep it that way.
4. **Guards change with tests.** A change to a guard (`command_guard.py`,
   `write_guard.py`, `site_guard.py`, `agent_gate.py`) comes with a test for
   the case it adds or fixes, including the harmful case it must still stop.
5. **Safe defaults.** A new security setting is on by default; a setting that
   sends data out or reaches the web is off by default and asked at install.

## Pull requests

- Keep one change per pull request and explain why it is needed.
- Run both test suites and say in the description that they pass.
- If the change affects what the installer writes, run it once with
  `--dry-run` and paste the relevant part of the summary.
