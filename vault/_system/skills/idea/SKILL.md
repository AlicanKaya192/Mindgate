---
name: idea
description: Saves an idea the user states straight into the second brain's inbox (their own sentence verbatim + a short assessment + links). Use it at moments like "something came to mind" or "I have an idea like this"; write without asking questions.
---

Vault: `{{VAULT}}`. Schema: vault `CLAUDE.md` §7.1, template `_templates/idea.md`. Write in the vault language.

1. **Write at once, do not ask questions.** Create `inbox/YYYY-MM-DD-<short-name>.md` (lowercase, ASCII, hyphens). Frontmatter: `type: idea`, `status: draft`, `tags`, `created`/`updated` today.
2. In the "Raw idea" section put the user's **own sentence verbatim** (no correction, no shortening).
3. A short assessment: what it is for / for whom; what the first step is; which existing project, idea or concept it is related to (`[[...]]` links). List open questions if there are any. No more than 10 lines in total.
4. If the same or a very similar idea exists in `inbox/` or `ideas/`, do not open a new note; add a dated entry to the existing note and tell the user in one sentence.
5. One line in the "Ideas" section of `index.md`; at the end of `log.md` `## [YYYY-MM-DD] idea | <title>`.
6. Commit in the vault (push if a remote is set). Optional dashboard: not in v1.
7. In the `_system/skills/skills-registry.md` table, increase the usage count by 1.
8. One line to the user: "Saved → [[file-name]]". Do not start discussing or teaching the idea (#15); if the user wants, it is discussed.
