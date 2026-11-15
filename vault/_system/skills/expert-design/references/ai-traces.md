# AI-trace audit

Go through it against the screen, item by item. None of them is a crime on its own: if the brief requires it, use it and write the reason. The problem is spending empty choices on these. Do not escape one default only to land on another.

Each line has the form **trace → what to do instead**. The fix is a starting point; the project's design decision and the user's taste come first.

**Evidence level:** **A** primary source, read on the page. **B** Anthropic's `frontend-design` skill (13 October 2026, downloaded copy). **C** search-result summary; mostly blogs selling tools, the pages were not visited: a candidate, not certain. **D** a designer's list of traces (unslop, 15 November 2026, downloaded copy); it rests on craft judgment, not on measurement. The user's own rejections are not in this list; they are read from `me/profile.md` and [[rejected-proposals]] and override this list.

## General look
- [ ] **A** A neutral, plain background and a single bright accent, no other identity. (NN/g) → Go back to the direction step: choose a material from the product's world and a single memorable element.
- [ ] **A** If the screen were swapped with another product, no one would notice. (NN/g) → Rewrite the heading, the imagery and the signature detail with this product's own names and content.
- [ ] **A** Visual choices come from a library default, not from an idea (Tailwind, Shadcn). (NN/g) → Derive the tokens from the direction; for every value that stays at its default, answer "why this one".
- [ ] **D** Richness spread over the frame: background, buttons, borders and labels are all colored or carry effects. → Calm the frame; gather color and detail into one or two moments of the content.

## Hierarchy and layout
- [ ] **A** Every element has equal weight; the main task is below and secondary information is on top. (NN/g) → Move the main task up and make it the largest element; shrink secondary information or move it further down.
- [ ] **A** A large gap between two related things; no grouping. (NN/g) → Spacing inside a group is smaller than spacing between groups.
- [ ] **A** Margins are inconsistent across screens. (NN/g) → One value for the page edge; bring one-off values that are off the scale back onto it.
- [ ] **B** Everything is split into the same rounded cards with the same shadow. Cards are not forbidden; use them for real grouping. → Remove the cards that carry no grouping; separate with spacing and thin lines.
- [ ] **C** A grid of equally spaced, equal-height cards; sections repeat the same pattern. → Give the grid a rhythm: a few small elements and one wide one; if the content type differs, so does the size.
- [ ] **C** Sections look as if they were produced separately, as if from different sites. → Tie every section to the same tokens; fix layer by layer, not section by section (spacing first, then color).
- [ ] **D** Rows in the same list have different heights; sibling cards have different padding. → The same thing has the same size: one row height, one padding.
- [ ] **D** Icons, labels and numbers do not line up in the same column. → The icon box has the same width on every row; numbers are right-aligned.

## Color and surface
- [ ] **A** Too much color, creating visual tension. (NN/g) → Take background, surface, border and text from one neutral ramp; bring the accent down to one or two places per screen.
- [ ] **A** Weak contrast. (NN/g) → Measure it; 4.5:1 for normal text, 3:1 for large text and interface elements.
- [ ] **B** Gradients as decoration. → A flat surface. If a gradient stays, it carries a meaning or is a small shift within the same hue.
- [ ] **B** Cream background, serif heading and terracotta accent; or a single bright green or red accent on a dark background. → Derive the palette from the product's world; do not move from one default to another.
- [ ] **C** Purple, indigo or blue-purple gradient; a gradient hero. → One neutral surface; a brand color, if there is one, becomes the accent and leaves the surface.
- [ ] **C** A thick colored stripe on one edge of a rounded card. → Show the status with a small dot or with text.
- [ ] **D** Gradient text in a heading, a number or a logo. → Flat, in the primary text color.
- [ ] **D** Colored glow, colored shadow, neon border; a blurred blob of color behind the content. → Remove it. Depth comes from surface steps and a thin, low-opacity border.
- [ ] **D** Many very close shades of the same color in the text. → Three text roles: primary, secondary, muted.
- [ ] **D** Every element is accented and none stands out. → The accent marks only the main action, the selection or the one important number.
- [ ] **D** Glass-look card: white inner glow and colored shadow. → A flat raised surface and a thin border.

## Typography
- [ ] **B** A small uppercase label above every heading. → Remove the label or write it in sentence case. A short, one-line uppercase label can stay with a reason (letter spacing: `visual-craft.md`); the trace is repeating it on every section.
- [ ] **B** Monospace in small data labels. → Use the interface family; keep monospace for code and for numbers that must line up.
- [ ] **B** Coloring a single word in a heading. → Give emphasis through word choice; the heading is one color.
- [ ] **C** No typeface was chosen, the default stayed (Inter etc.). **Inter is not forbidden**, the sources argue about it; the question is "why did I choose this typeface". → Choose by the character in the direction, or write why it stayed.
- [ ] **D** Headings at weight 800–900. → Build hierarchy with size and color; keep weight to a few steps.
- [ ] **D** Many sizes and weights on the same screen. → A few sizes from the scale, two weights.
- [ ] **D** Numbers in mixed formats (one with cents, one without). → One format across the screen, `tabular-nums`.
- [ ] **D** Negative letter spacing in small text; italics for emphasis. → Zero or slightly open letter spacing in small text; emphasis with color or weight.

## Icons
- [ ] **D** Emoji in navigation, labels or status; emoji inside a counter. → Line icons from one set, or none; a counter is a plain number.
- [ ] **D** Icons in different sizes and colors. → One size, one stroke width; the color comes from the role of the text the icon belongs to.
- [ ] **D** A sparkle icon on everything AI-related. → Remove it; an icon stays only if it explains something.

## Pattern repetitions
- [ ] **B** A meta line shaped like `A · B · C`. → Keep the most important item and move the others to the details.
- [ ] **B** `→` at the end of button text. → The button says the action; an arrow only if it leads to another page.
- [ ] **B** 01/02/03 numbering when it is not a sequence. → Remove the numbers; keep them if the sequence is real.
- [ ] **B** Newspaper layout: thin lines, boxes without corners. → Go back to the project's corner and line tokens.
- [ ] **B** A slide-in entrance animation on every section. → At most one entrance on load; the rest stay still (`motion-interaction.md`).
- [ ] **D** Glowing pills for counters, plans and shortcuts; "PRO", "New", "Beta" badges everywhere. → Calm text or key caps; a badge only if it is really needed, and then one calm badge.
- [ ] **D** Everything fully rounded, from the search field to buttons and cards. → Corners follow size; work out nested corners.

## Text
Rules: "Interface text" in the skill file.
- [ ] **C** Placeholder names such as John Doe, Sarah Johnson; fake data with round numbers. → Names and numbers that resemble the project's real data.
- [ ] **D** A greeting heading ("Welcome back!"). → The heading states the context: the page's name or the period.
- [ ] **D** Exclamation marks in interface text. → A plain sentence.
- [ ] **D** A change that does not say what it is compared with ("+12%"). → Write the comparison: "+12% vs last month".
- [ ] **D** Hype words and a heading that fits any product ("Supercharge your workflow"). → Say what the product does for whom, in its own names.
- [ ] **D** Social proof without a source ("Trusted by 10,000+ teams", stars, a row of avatars). → Ask the user; if it is true, write it calmly and concretely; if not, remove it. List it in the report.
- [ ] **D** A long placeholder ("Search for anything..."); a period at the end of labels and buttons. → "Search"; short text ends without a period.

## Chart and stat card
Rules: "Chart and stat card" in `visual-craft.md`.
- [ ] **D** Rainbow bars in a single series; glowing bars. → The one thing that matters takes the accent; the rest stays in neutral steps.
- [ ] **D** A mini chart or decorative line added to every stat card. → A label, a large number and what it changed against.
- [ ] **D** Charts side by side at the same size and in the same layout. → One main chart; the other data smaller and of a different kind.

## Opening section (hero)
- [ ] **D** A pill-shaped announcement badge above the heading. → Remove it; if it is real news, a calm text link.
- [ ] **D** Floating blobs, spheres, grids or glowing lines in the background; robot and brain images on every AI product. → A plain background or the product itself: a preview built in code with realistic data.
- [ ] **D** Three or more buttons; badges and avatars lined up under the buttons. → One primary action and at most one secondary.
- [ ] **D** Text baked into an image, a fake button or a fake logo. → Text is real text on the page; the image carries no text.
- [ ] **D** An image in every section. → Images where they help, often only in the opening.

## Motion
Measured rules: `audit.md` T15, T16, T27, T38, T39.
- [ ] **D** A pulse or a breathing glow on an element that is not live; elements that float in on scroll. → Still.
- [ ] **D** Cards that grow on hover; bouncy, overshooting springs. → On hover, a color or surface step; a small shrink on press; one ease-out curve.

## Process
- [ ] **A** Wrong pattern: chosen from a word, not from the context. (NN/g) → Reread the task in the brief; choose the pattern from the task.
- [ ] **A** The swap test was not done, no reason given. → Do it and write it down.
- [ ] Finished without taking any screenshot. → Draw, measure, look (step 8 of the flow).

## The template you land on after cleanup
Not a trace: it is where a cleaned-up screen ends up when nobody makes a decision. Look for it after the fixes.
- [ ] **D** A flat grey background, the default typeface and the old brand color on a single button. → Tint the neutrals slightly toward the product's world and take the accent from there.
- [ ] **D** An opening image left as an empty box or a generic picture. → A product preview.
- [ ] **D** The same layout, type and palette for every product. → Let the direction decide, not habit.

## Details that raise quality
These are the invisible part of the craft. Kowalski: they add up even if unnoticed.
- Shadows from a single light source; numbers in table layout (`tabular-nums`); nested corners that match.
- Small feedback on press; the popover opens from its trigger; the second tooltip has no delay.
- On copy, an in-place checkmark instead of a notification; an error highlights the related field.
- Hover and focus have higher contrast than the resting state.

---
The **D** traces and the fix ideas are adapted from Damir Sokolovsky's unslop skill (CC BY 4.0, https://github.com/heydamir/unslop). The text was rewritten; its numeric values and absolute bans were not taken. The fixes on the A, B and C lines are our own.
