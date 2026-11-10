---
name: new-project
description: Opens a new project folder in the second brain (main page, progress, rules, decisions/, experiments/) and updates the index and the log. Use it when the user starts a new project or adds an existing project to the vault.
---

Vault: `{{VAULT}}`. Schema: vault `CLAUDE.md` §2 (project folder layout), §3 (naming), §5 (frontmatter). Write in the vault language.

1. Decide the project name: lowercase, ASCII, hyphens (`rag-chatbot`). If the user did not say it, make a short suggestion, do not ask.
2. If the project is on the computer, **read** it first: README, plan/status files if any, `git log --oneline | head -30`, dependency files. Do not change the code.
3. Under `projects/<project>/` create from the templates (`_templates/`): `<project>.md` (`project`), `<project>-progress.md` (`project-progress`), `<project>-rules.md` (`project-rules`), an empty `decisions/` and, for an ML project, `experiments/`. Fill in the `{{title}}`/`{{project}}`/`{{date}}` placeholders; write the goal, the status, the tech stack and the "Content map (MOC)" with real information.
4. If an important technical decision already taken in the project is known, write a retroactive ADR (`decision-adr` template; if the options are inferred, mark them "retroactive").
5. If the project has known problems/solutions that will also help other projects, write them to `problems/` and link them from the project main page.
6. Add it to the "Projects" section of `index.md`; the Bases table in `projects/projects.md` shows it automatically. Add it to the "Projects" list in `me/profile.md`.
7. At the end of `log.md` add the entry `## [YYYY-MM-DD] project | <Project> added`.
8. If the project folder has a `CLAUDE.md`, add a short "Second brain" section at its end (the vault path, this project's vault pages, that progress/problems/decisions are also recorded in the vault). **Do not put an AI signature** in commits (#14); commit to the project repository only if the user asks.
9. Commit in the vault (push if a remote is set), then update the dashboard (`/dashboard`).
10. In the `_system/skills/skills-registry.md` table, increase the usage count by 1.

Strict rules: sensitive information and computer codes are not written (#3, #18); no AI trace is left in the project (#14).
