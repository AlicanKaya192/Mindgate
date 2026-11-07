---
name: expert-language
description: Expertise pack for Turkish and English spelling, punctuation and context checking, and for removing AI traces from a text. Load when writing or reviewing interface text, an error message, a README, a document, a report, a story, a post or an e-mail draft; and when the user says "spelling", "grammar", "TDK", "proofread" or "sounds like AI". Preloaded into the language-editor agent; the main chat and the writer can also load it.
---

Expertise pack (not an agent). Related rules: #1, #8, #24. Detailed rule lists: `references/tdk.md` (Turkish spelling reference, used when the vault language is Turkish), `references/ai-traces.md` (trace patterns).

## Order
1. **Spelling and punctuation** (firm rules). For Turkish `references/tdk.md`, for English general grammar.
2. **Context:** Is the sentence built the way a person would build it? Subject-predicate agreement, needless repetition, missing connective, wrong term.
3. **AI trace:** Check against the `references/ai-traces.md` list one by one.
4. **Voice:** If the text is in a person's voice, keep their voice; do not suggest a "prettier" sentence that belongs to someone else.

## Most common Turkish mistakes (detail in `references/tdk.md`)
- The conjunction "de/da" and "ki" are written separately, the suffix "-de/-da" is written attached; the question particle "mi" is written separately and later suffixes attach to it.
- A suffix on a proper noun is separated by an apostrophe; the conjunction "de" is not attached with an apostrophe.
- A period as the thousands separator, a comma as the decimal; no space after the percent sign ("%25").
- Compound words: attached if there is a shift in meaning or a dropped sound, separate if not.

## English
- Subject-verb agreement, tense consistency, articles (a/an/the), the comma splice.
- In a Turkish text, an English term gets its Turkish in parentheses at first use (#1, #8); code, commands and error messages are not translated.

## Output
A correction table: place, wrong, right, rule, firm or suggestion. A correction you are not sure of is a "suggestion". Do not change the meaning.

## Verify before finishing
- [ ] The rule behind every firm correction is written.
- [ ] The person's voice was kept; the meaning did not change.
- [ ] Code, commands and file names were not touched.

## Idea sources
- Turkish Language Association (TDK) spelling rule pages (tdk.gov.tr, read on 6 November 2026; the addresses are in `references/tdk.md`).
- In the vault: the AI-trace list of the `expert-content` skill.

## Lessons
<!-- The central agent adds verified lessons here: general and reusable, without project names or dates. -->
