---
name: problem
description: Saves a bug/problem and its solution to the second brain's central problem library (problems); it first searches whether the same problem exists. Use it when a bug is solved or when the user says "write this to problems".
---

Vault: `{{VAULT}}`. Schema: vault `CLAUDE.md` §7.3, template `_templates/problem.md`. Write in the vault language; put the translation of English terms in parentheses next to them.

1. **Search first (rule #38):** In `problems/` search for the distinctive part of the error message and for keywords (`grep -ril`), then search by meaning (`{{PY}} -I _system/search.py "<symptom>"`); similar problems count too. Look at the "Problems" section of `index.md` as well.
2. **If it exists — try the old solution first.** Do not try again, in the same conditions, a solution marked ✗ (did not work) in the note's "Attempted solutions" table. Write the result as a new row in the table: `| date | [[project]] | what was tried | ✔ worked / ✗ did not work / ~ partly | why |`.
   - **If it worked:** the row is ✔; add the date + project to "Seen again in".
   - **If it did not work:** **do not overwrite or delete** the old solution; its row stays with ✗ and its reason. Find the new solution (`debugging`), add it as a new row too, and replace the "Solution" section with the new valid solution. If the root cause changed, add a dated note to "Root cause".
   - **If it could not be solved:** `status: open`, the attempts are in the table.
   - Set the `updated` field to today. If the problem is similar but different, open a new note and link to the old one.
3. **If it does not exist:** create `problems/<short-name>.md` (lowercase, ASCII, hyphens). Required sections: Symptom (the error message **verbatim**, in a code block), Environment, Root cause, Solution (the valid solution, step by step, with commands), Attempted solutions (including attempts that did not work), How to prevent it, Seen again in, Sources. Frontmatter: `type: problem`, `status: solved|open`, `project: "[[<project>]]"`, `tags`, `aliases` (the searchable form of the error message).
   - **Regression marker:** If the solution left a distinctive string in the code (a new parameter, a guard line, a constant), write it in the "Regression marker" section: ``- `<file path>` → `<string>` ``. The string must appear only in that solution (a single match with `grep`). `health.py` warns if the string disappears or the file moves; this way you notice if the solution is silently reverted. The path may start with `~`; a string that contains a secret, an IP or a computer name is not written (#18).
4. If the solution needs a concept and there is no page for it in `knowledge/`, open a short concept note and link it (just a note; no teaching, #15).
5. Add a link to the "Problems" line of the content map (MOC) on the project's main page. Add one line to the "Problems" section of `index.md`.
6. Log: `{{PY}} -I _system/records.py log --operation problem --title "<title>" --evidence "<commit/test>" --learned "…"`; in the body which solution was tried and the result.
7. Commit in the vault (push if a remote is set). Optional dashboard: not in v1.
8. In the `_system/skills/skills-registry.md` table, increase the usage count by 1.

Not to be written: passwords, keys, tokens, IP/MAC, computer name, personal data (#18). If the source of a command is unclear, do not write it (§9).
