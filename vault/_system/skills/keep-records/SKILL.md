---
name: keep-records
description: Second brain: scan the session logs, review this conversation, write what is missing into the vault, log, commit. Use it when the user says "keep the records" or when a big piece of work is finished.
---

Vault: `{{VAULT}}`. Schema: vault `CLAUDE.md` (§7.8 session logs, §10 git). Write in the vault language; put the translation of English terms in parentheses next to them.

1. From the vault root run `{{PY}} -I _system/session_log.py scan`.
2. Read every record under `inbox/sessions/`. Review **this conversation itself too**. Write what has no counterpart in the vault into the relevant notes:
   - idea → `inbox/` (template `idea`)
   - problem/solution → `problems/` (first search whether the same problem exists; if it does, add to "Seen again in")
   - technical decision → the ADR in the project's `decisions/`
   - progress → a dated entry in `<project>-progress.md`
   - new rule → `rules/general-rules.md` or `<project>-rules.md`
   - non-sensitive profile information → `me/`
   Do not rewrite what is already in the vault. Do not invent what you are not sure of; if needed, read the relevant part from the transcript path in the record.
   - A question that was asked to the user but not answered, an approval/decision that was requested, a job left to them, or a notice they should see → a `P-NNN` item in `inbox/pending.md` (ending with `| chat: <chat title> | project: [[<project>]]`) + a `pending` entry in the log (§7.10). Close the answered/finished ones (`[x]`, `✔ date`, a `done` entry in the log).
3. Set the `updated` field of the notes you touched to today; add new pages to `index.md`; leave no orphan note.
4. **Do not delete** the processed records, move them to the archive: `{{PY}} -I _system/session_log.py process <record.md> ...` (rule #22: no deletion without permission). Add a `## [YYYY-MM-DD] progress | Records kept` entry at the end of `log.md` (short: how many records, which notes).
5. `git add -A`; check with `git diff --cached` that no secret leaked; commit (message in the vault language); push if a remote is set. If another session is writing to the vault at the same time, do not break its half-written files.
6. Update the dashboard (`/dashboard`).
7. In the `_system/skills/skills-registry.md` table, increase this skill's "usage" count by 1 and write the "last used" date; if there was an error, write one line to the "last error" column.
8. A 2–4 line summary to the user.

Strict rules: this computer only (#17, if enabled); computer codes, passwords, keys, IP/MAC and computer name are written nowhere (#18); no teaching (#15).
