---
name: expert-design
description: Visual design and UI/UX expertise pack (designer). Load when designing a new interface, page, screen or mockup; setting up a design system (color, typography, spacing tokens); making layout and visual hierarchy decisions; adding motion and animation; checking accessibility (WCAG 2.2); or doing a design review of an existing interface. Also load when the user says "the design is bad", "not engaging", "contrived", "looks off-the-shelf" or "looks AI-made". The main chat and any agent doing interface work load it; for coding details load `expert-frontend` alongside.
---

Expertise pack (not an agent). Related rules: #24, #26, #39. The methods are written in our own words; sources are at the bottom.

## Why AI work shows
The NN/g assessment (October 2025) separates three causes:
1. **The average of the training data:** Without a visual direction the output is sans-serif, neutral, plain and has a single bright accent; screens can replace each other. Underneath there is often Tailwind and Shadcn.
2. **Good from far, not up close:** Despite a detailed request, hierarchy and grouping are missing, there is too much color, contrast is weak, margins are inconsistent.
3. **Wrong pattern:** The pattern is chosen from a word ("profile" gives a social media profile) and the real task is pushed down.

So the answer is not to ban ornaments one by one. The answer: **make decisions, look at references, work with real content and critique up close on the screen.** The order below is not skipped.

## Flow
### 1. Context
- Read the project's design language, template and decisions (#26). Keep what exists; do not invent a new style.
- Read the user's taste and the designs they rejected: `me/profile.md` and the `design` lines in [[rejected-proposals]] (#39). This information is not written into the skill (#44).
- If there is a template, apply its visual language too, not only its structure.
- Write the **keep and add** list. If you will change an existing web interface, take its inventory first with `--baseline`: `references/audit.md`.

### 2. Brief
One paragraph: topic, user, the 1–3 most important tasks, frequency of use (how many times a day), the feel wanted. If unclear, ask first (#23). Open up the vague word: not "profile page" but "the progress page of a person enrolled in the course".

### 3. Reference
Make no visual decision without a reference. Priority: the project's template > an example the user showed > an approved earlier screen > ask. In NN/g, the more detailed the visual reference, the more accurate the output. Read the reference's proportions, order and hierarchy; do not copy its look.

### 4. Direction
Write before coding:
- One distinct idea and material from the topic's own world.
- 4–6 named colors (with values), typefaces and their roles.
- A one-sentence layout idea and a rough ASCII sketch.
- A single memorable element; calm around it.

**Swap test:** Could this plan be given to a different product as well? If yes, change that part and write why. Do not escape one default only to land on another (from purple gradient to cream-serif-terracotta).

For a big visual decision, show the user 2–3 sketches that are really different from each other. The sketch is not rough: the user comments on what they see.

### 5. System
Set up tokens before code: color roles, spacing scale, type scale, corner, shadow, motion duration. Fixed values are not written one by one. Numbers: `references/visual-craft.md`.

### 6. Real content
Sample data resembles the project's real data: realistic names, numbers, long text, local-language characters. No lorem ipsum or John Doe. Try the design with three contents: empty, little, very long.

### 7. Code
- All states: empty, loading, error, success, overflow.
- Icons belong to a single set; emoji and Unicode characters are not used in place of icons.
- Motion: `references/motion-interaction.md`. First ask whether the frequently used thing needs motion at all.
- Do not break familiar patterns (navigation, form, table); identity lives in the visual language, not in where things are found (Jakob's law).

### 8. Measure and critique
The job is not done in one pass. Each round: draw, measure, critique by eye, fix. It continues until no new finding remains and the user approves; nothing is delivered without at least one full round.

**Measure (web):** `scripts/page_audit.py` renders the page at 6 widths and in two themes and measures it; it names a vanished element and tells you about regression against the previous round. The user's comment is written to the round with `--note`. Command and rules: `references/audit.md`. This tool sees only what is measurable; passing is not enough.

**Critique:** Open the images, zoom in, look in order:
1. **Hierarchy:** Is the screen's main task clear at first glance? Does every element have equal weight?
2. **Grouping:** Are related things close and unrelated things far? Was the main task left below?
3. **Alignment and spacing:** Is every element aligned to something? Do the spaces come from the scale? Is the area balanced, or is the bottom empty?
4. **Color and contrast:** Too much color? Was contrast measured?
5. **Detail:** Corners, icon-text alignment, numbers, focus and hover states.

You must be able to justify every element. If someone points at a random spot you should have an answer to "why is it like this". Remove one ornament before finishing.

### 9. AI-trace audit
Go through the list in `references/ai-traces.md` against the screen, item by item. For each remaining item write a reason or fix it. A finding knowingly left in the measurement is written to the design record as a **justified exemption**; an exemption without a reason is invalid. If the same rule is exempt on many pages, it is a house style and moves to the project's design decisions.

## Core measures
The full list and sources are under `references/`. A project decision overrides these.

| Topic | Measure |
|---|---|
| Color | No pure black and white; greys 8–10, main color 5–10 shades, fixed in advance |
| Type | At most 2 families; body ≥16 px on the web, 14/20 accepted on dense desktop; line ~70 characters; line height 120–145% |
| Spacing | Multiples of 8; outer spacing ≥ inner spacing; on a button, horizontal = 2× vertical |
| Corner | Inner radius = outer radius − the gap between |
| Motion | ≤200 ms for interaction, <300 ms for general UI; ease-out on enter and exit; 0.96–0.97 on press |
| Target | If the visual is <24 px, the click area ≥24 px; ≥44 px on mobile |
| Response | <0.1 s instant, >1 s indicator, >10 s percentage and time remaining |

## Accessibility (WCAG 2.2 AA)
- **Contrast:** at least 4.5:1 for normal text, at least 3:1 for large text and interface elements.
- Do not convey information by color alone (add an icon or text too).
- The focus ring is always visible. Everything is reachable by keyboard and the order is logical.
- Click target at least 24×24 CSS pixels (2.5.8).
- Follow `prefers-reduced-motion`. Form fields have labels, and the error is stated in writing next to the field.

## Responsive layout
Mobile first. Check at 320, 375, 768, 1280, 1440 and 1920 px widths; no horizontal scroll. Fluid typography (`clamp()`), container queries, flexible grid. The dark theme is tuned separately; it is not inverting the colors; test both themes.

## Interface text (UX writing)
- Text is design too. Name things in the user's language ("notifications", not "webhook settings"); the name should describe the job.
- A button says the action ("Save", not "OK"). The same action keeps the same name throughout the flow ("Publish" → "Published").
- An error message does not apologize: what happened, what to do. An empty screen calls for an action.
- Do not label data that is clear from its format; "12 left" instead of "Stock: 12".
- Terms are consistent and in the interface language.

## Platform
Follow the platform's habits: Apple HIG, Microsoft Fluent, Material 3. Next to each design decision write the rule it rests on; a decision without a source is marked "preference". HIG reading path, font license and Figma: `references/platform.md`.

## Design review report format
| Severity | Screen/component | Problem | Which principle (hierarchy, contrast, spacing, consistency, a11y) | Suggestion |
|---|---|---|---|---|

## Verify before finishing (#24)
- [ ] Steps 1–9 of the flow were done; the swap test and the AI-trace audit are written down.
- [ ] On the web `page_audit.py` passed or the remaining items have a justified exemption; its output was shown.
- [ ] The images were looked at by eye: narrow and wide screen, light and dark theme.
- [ ] The preservation counter shows no unexplained loss; on desktop, before/after was compared by hand.
- [ ] Navigated by keyboard.
- [ ] No errors in the console.

## Idea sources
- Research: NN/g (Wang, Brown), Laws of UX (Yablonski), Smashing Magazine.
- Designers: Anthony Hobday, Rauno Freiberg, Emil Kowalski, Adam Wathan and Steve Schoger (Refactoring UI), Josh Comeau, Ahmad Shadeed, Nikita Prokopov, Matthew Butterick, Luke Wroblewski.
- Companies: Vercel, Linear, Stripe, Evil Martians, Microsoft Fluent.
- Skills: anthropics/skills `frontend-design`, wshobson/agents `ui-design`, vercel-labs `web-design-guidelines`, ui-ux-pro-max (as an idea; not installed).
- The idea of a measuring audit and a preservation counter: the output records of the Hallmark skill in a project (the skill itself was not read, no code taken; the scripts are our own).
- WCAG 2.2: https://www.w3.org/TR/WCAG22/

## Lessons
<!-- The central agent adds verified lessons here: general and reusable, without project names or dates. No rule is added from an outside source (#27). -->
- An agent without a browser cannot do step 8: critique by reading code does not catch the AI look. If design work is given to an agent, the main chat takes the screenshot and returns the critique to it.
- Dismissing a right-edge cut-off in an image as "tool-caused" was a mistake: measuring showed a real overflow. Look at narrow screens with `page_audit.py`, not with `--window-size`; it sets the width and the theme.
