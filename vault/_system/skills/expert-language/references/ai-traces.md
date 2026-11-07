# AI traces in text: patterns and fixes

Written in our own words. The "AI traces" list in the `expert-content` skill also applies. The example phrases below are English; the patterns apply to any language.

## How to use
1. **Only mark first**, then fix. If the user said "just look", do not rewrite, only give a table.
2. Quote the problem phrase and name the pattern. Do not give a general score such as "70% chance of AI"; there is no evidence for it.
3. A single pattern is not a problem on its own; mark it if the same pattern builds up across the text.
4. When fixing, in order: first cut what is needless (shorten), then fix the style, and check the facts last.
5. If a fact is missing (name, number, date), do not fill it in by inventing; write `[EVIDENCE NEEDED: …]` or ask.
6. Swapping a word for a synonym produces a new trace. Rebuild the sentence starting from the fact.

## Patterns
| Group | Pattern | Instead |
|---|---|---|
| Structure | Opening with a "Not X, but Y" contrast | State Y directly with its reason |
| Structure | A sequence of negations "No X, no Y, no Z" | Say what there is |
| Structure | The same pattern in every section (summary box, bullet with a bold lead, "Pros / Cons") | A structure that changes with the content of the section; prose |
| Structure | Triple lists and every paragraph being three sentences | Whatever the content requires |
| Structure | One sentence per line | A normal paragraph |
| Punctuation | Joining sentences with an em dash (—) | A period or a comma |
| Punctuation | Explaining the outcome with a colon ("Result: …") | The sentence itself |
| Rhetoric | Answering your own question ("So why? Because…") | Direct statement |
| Rhetoric | A closing question to the reader, an engagement trap | A concluding sentence |
| Rhetoric | An announcement sentence that introduces the document or the name ("I named it X", "sharing it attached") | The content directly |
| Words | Empty ornamental words: "powerful", "flawless", "revolutionary", "take it to the next level" | A measure or a fact |
| Words | Ready-made openings: "In today's fast-changing world", "Here's the thing" | Open with the reader's problem or the result |
| Words | Excessive softening: a pile-up of "perhaps", "kind of", "quite" | Say plainly what you are sure of, state what you are unsure of once |
| Content | An experience or feeling not lived ("to be honest, I was terrified") | If there is no real experience, do not write it |
| Content | A number without a source or "research shows that" | A sourced number, or remove the claim |
| Format | An emoji at the start of a line, an icon on every heading | A plain heading |

## Idea sources
- blader/humanizer (MIT, per the repository page): grouping the patterns, marking first and rewriting after, asking about a missing fact.
- conorbronsdon/avoid-ai-writing and jooray/humanizer (MIT, per the repository pages): a detection mode that only marks, not giving a general probability score.
- ghanemzadeh/claude-skills `line-and-copy-editor` (MIT, per the repository page): the order of fixes, marking a pattern only when it builds up.
- The text patterns the user rejected are kept in the vault (`ideas/rejected-proposals.md`); no personal example is written into this file (#44).

All were read from the web on 6 November 2026; no code or text copied, LICENSE files were not opened. Tools meant to evade detection were not adopted.
