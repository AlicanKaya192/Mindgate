# AI-trace audit

Go through it against the screen, item by item. None of them is a crime on its own: if the brief requires it, use it and write the reason. The problem is spending empty choices on these. Do not escape one default only to land on another.

**Evidence level:** **A** primary source, read on the page. **B** Anthropic's `frontend-design` skill (13 October 2026, downloaded copy). **C** search-result summary; mostly blogs selling tools, the pages were not visited: a candidate, not certain. The user's own rejections are not in this list; they are read from `me/profile.md` and [[rejected-proposals]] and override this list.

## General look
- [ ] **A** A neutral, plain background and a single bright accent, no other identity. (NN/g)
- [ ] **A** If the screen were swapped with another product, no one would notice. (NN/g)
- [ ] **A** Visual choices come from a library default, not from an idea (Tailwind, Shadcn). (NN/g)

## Hierarchy and layout
- [ ] **A** Every element has equal weight; the main task is below and secondary information is on top. (NN/g)
- [ ] **A** A large gap between two related things; no grouping. (NN/g)
- [ ] **A** Margins are inconsistent across screens. (NN/g)
- [ ] **B** Everything is split into the same rounded cards with the same shadow. Cards are not forbidden; use them for real grouping.
- [ ] **C** A grid of equally spaced, equal-height cards; sections repeat the same pattern.
- [ ] **C** Sections look as if they were produced separately, as if from different sites.

## Color
- [ ] **A** Too much color, creating visual tension. (NN/g)
- [ ] **A** Weak contrast. (NN/g)
- [ ] **B** Gradients as decoration.
- [ ] **B** Cream background, serif heading and terracotta accent; or a single bright green or red accent on a dark background.
- [ ] **C** Purple, indigo or blue-purple gradient; a gradient hero.
- [ ] **C** A thick colored stripe on one edge of a rounded card.

## Typography
- [ ] **B** A small uppercase label above every heading.
- [ ] **B** Monospace in small data labels.
- [ ] **B** Coloring a single word in a heading.
- [ ] **C** No typeface was chosen, the default stayed (Inter etc.). **Inter is not forbidden**, the sources argue about it; the question is "why did I choose this typeface".

## Pattern repetitions
- [ ] **B** A meta line shaped like `A · B · C`.
- [ ] **B** `→` at the end of button text.
- [ ] **B** 01/02/03 numbering when it is not a sequence.
- [ ] **B** Newspaper layout: thin lines, boxes without corners.
- [ ] **B** A slide-in entrance animation on every section.

## Content
- [ ] **C** Placeholder names such as John Doe, Sarah Johnson; fake data with round numbers.

## Process
- [ ] **A** Wrong pattern: chosen from a word, not from the context. (NN/g)
- [ ] **A** The swap test was not done, no reason given.
- [ ] Finished without taking any screenshot.

## Details that raise quality
These are the invisible part of the craft. Kowalski: they add up even if unnoticed.
- Shadows from a single light source; numbers in table layout (`tabular-nums`); nested corners that match.
- Small feedback on press; the popover opens from its trigger; the second tooltip has no delay.
- On copy, an in-place checkmark instead of a notification; an error highlights the related field.
- Hover and focus have higher contrast than the resting state.
