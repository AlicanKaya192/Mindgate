---
name: obsidian-writing
description: Obsidian syntax and vault rules for writing to the second brain vault; a checklist to verify before finishing. Preloaded for the maintainer agent; the main chat can use it too when writing a note to the vault.
---

Method skill (not an agent). The real source of rules is the vault `CLAUDE.md` (§3 naming, §5 frontmatter, §6 links, §10 index/log/git). This skill is its short practical summary; if they conflict, `CLAUDE.md` wins.

## Syntax
- **Link:**
  - `[[file-name]]`, with a display name `[[file-name|Display Name]]`
  - to a heading `[[file-name#Heading]]`
  - The extension is not written. The file name is unique across the vault.
- **Embed:** `![[file-name]]`, for an image `![[image.png]]`.
- **Callout:**
  - `> [!note]`, `> [!warning] Title`, `> [!tip]`
  - the foldable form `> [!info]-`
  - Used in the vault: `[!warning] Conflict`, `[!warning] Superseded`.
- **Properties (frontmatter):**
  - Flat YAML; no nested fields. The same field has the same type in every note.
  - Date `YYYY-MM-DD`. List `[a, b]`.
  - A link inside a property is written **in quotes**: `project: "[[project-name]]"`.
  - No `#` and no spaces in `tags`.
  - Optional fields:
    - `source_type: stated|inferred|verified`
    - `privacy: private`: stays out of automatic context and agent tasks
    - for a rejected inference `invalid` + `invalid_reason` (not deleted)
  - Write to shared files (pending, log, handoff) with `_system/records.py` (locked, #36).
- **Other Obsidian syntax:**
  - Link to a block: write `^block-id` at the end of the paragraph and link with `[[file#^block-id]]`. In a list or a quote, `^block-id` goes on a separate line.
  - Width in an embed `![[image.png|300]]`, a PDF page `![[document.pdf#page=3]]`.
  - Hidden comment `%%…%%`, highlight `==…==`, footnote `[^1]`.
  - Callout types: `note`, `tip`, `info`, `warning`, `danger`, `bug`, `example`, `question`, `success`, `failure`, `todo`. `-` is folded, `+` is open foldable.
  - In an inline tag the first character is not a digit; a nested tag is `#parent/child`.
- **Bases (`.base`)** files produce the tables of the entry pages. Do not touch them unless the work needs it. If you do:
  - The difference of two dates is not a number but a duration (Duration). For days take `.days`, then round: `(now() - file.ctime).days`. Calling `.round()` directly gives an error.
  - Protect a field that may be empty with `if(field, …, "")`.
  - Quote a YAML value that contains special characters. Put the formula in single quotes and the text inside it in double quotes.
  - If you use `formula.X`, `X` must be defined under `formulas:`.
- **Canvas (`.canvas`, JSON Canvas 1.0):** Node ids must be unique (16 hexadecimal digits). The `fromNode` and `toNode` of every edge must point to an existing node. Check that the JSON is valid before saving.
- **Invisible characters and external images** (`![](https://…)`) do not enter the vault (#27).

## Vault rules (summary)
- File names are lowercase, ASCII, hyphens (for Turkish: ç→c, ğ→g, ı→i, ö→o, ş→s, ü→u). Dated notes have a `YYYY-MM-DD-` prefix.
- Every note starts from a template (`_templates/`) and links to at least one place; there are no orphan notes.
- In a changed note the `updated` field is updated.
- `log.md` is append-only: `## [YYYY-MM-DD] <operation> | <title>`.
- An `index.md` line: `- [[file]] — one-line summary`.
- Sensitive information, secrets and computer codes are not written (#17, #18). No deletion, move to the archive (#22).

## Verify before finishing (#24)
- [ ] The target file of every `[[link]]` you wrote exists (look with Glob). If not, use plain text or code format.
- [ ] The frontmatter is valid YAML; `type`, `status`, `updated` are correct.
- [ ] `index.md` and `log.md` are updated.
- [ ] Content from an outside source was scanned with `{{PY}} -I _system/security_scan.py <file>`.
- [ ] Secrets were checked with `git diff --cached`, the commit was made (and pushed if a remote is set).
- [ ] The report has evidence: the commit id. Saying "I did it" is not enough.

## Idea sources
- kepano/obsidian-skills (`obsidian-markdown`, `obsidian-bases`, `json-canvas`; MIT, Steph Ango): https://github.com/kepano/obsidian-skills. The missing parts were added from the copy downloaded on 13 October 2026.
- obra/superpowers `verification-before-completion`: https://github.com/obra/superpowers

## Lessons
<!-- The central agent adds verified lessons here: general and reusable, without project names or dates. -->
- Add a new `index.md` line with **`records.py index --section … --line …`**; adding by hand once lost a line (a #36 violation). For a project sub-note (ADR, progress) put two spaces at the start of the line: `--line "  - [[project-name-adr-009-…]] — …"` (an indented line is supported).
- Parallel chats can write to `pending.md` at the same time (the same number was taken twice). Reread the file right before writing a P-NNN number, and after writing check that the number is unique.
