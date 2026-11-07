---
name: expert-writing
description: Text production expertise pack. Load when writing game narrative, world and character, dialogue, a story, interface text (button, error message, empty screen, confirmation dialog), technical documents and guides, presentation text or a visual design brief. Preloaded into the writer agent; the main chat can also load it. For personal posts such as a blog, LinkedIn and README use `expert-content` first, and `expert-language` for spell checking.
---

Expertise pack (not an agent). Related rules: #14, #24, #44. AI-trace list: `expert-language` → `references/ai-traces.md`.

## Before every text
1. **Who is the reader, where will they see the text, what do we want them to do?** Write it in one sentence.
2. **Voice profile:** If the project has a voice and tone note, read it (target reader, tone, words not to use, own examples). If not, use the tone in the task text; do not carry personal examples outside the vault.
3. **Facts:** Names, numbers, dates and claims only from the given sources. If missing, `[EVIDENCE NEEDED: …]`.

## By type
**Interface text (UX writing)**
- A button says the action and starts with a verb ("Save", "Open file"); an action-specific label instead of "OK".
- An error message says what it is, why, and what to do; it does not apologize, it does not blame the user.
- An empty screen calls for a first action. The same action keeps the same name throughout the flow.
- Output: a suggestion, one or two alternatives, the reason, a note on length differences between languages.

**Technical document, guide, design brief**
- First gather the context (goal, reader, constraints), then write section by section; fix in a targeted way, not by rewriting the whole text.
- When done, the "reader without context" test: can someone who has not seen the conversation do the job with only this text?
- In a brief: goal, reader, the 1–3 most important tasks, constraints, reference, delivery format.

**Game narrative, story, character, dialogue**
- First the rule of the world and the player's goal; the narrative serves the mechanics, it does not delay them.
- A character has a want and something that blocks it; each character's way of speaking is distinguishable.
- Dialogue is kept short, information is given by showing; if the player has a choice, each option has a different consequence.
- Do not copy the characters, world and names of an existing game, film or book; write something original.

## Verify before finishing
- [ ] The reader and goal sentence fit the text.
- [ ] No invented facts; gaps are marked.
- [ ] The text was checked against the AI-trace list.
- [ ] Wrote only to the given output file.

## Idea sources
- anthropics/knowledge-work-plugins `design/skills/ux-copy` (repository Apache-2.0): a button that starts with a verb, a three-part error message, a suggestion-and-reason output.
- anthropics/skills `doc-coauthoring` (repository Apache-2.0): gathering context, a draft section by section, the reader-without-context test.
- alexconner-79/ill-communication (MIT, per the repository page): a voice profile template, a separate microcopy reference.
- Game narrative section: no open-source skill was found (search of 6 November 2026); written with general narrative design knowledge, not measured.

All were read from the web on 6 November 2026 (summaries; full text and LICENSE files were not opened). No code or text copied.

## Lessons
<!-- The central agent adds verified lessons here: general and reusable, without project names or dates. -->
