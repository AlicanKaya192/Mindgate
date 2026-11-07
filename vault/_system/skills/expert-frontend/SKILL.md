---
name: expert-frontend
description: Interface (UI) and user experience (UX) expertise pack. Load when working on a web or desktop interface, a component, a page, a form, a theme, accessibility or a visual layout, or when reviewing an interface change.
---

Expertise pack (not an agent). Read the project's rules and earlier design decisions first (#26). Put **readability** first in the interface: do not lose existing information, and compare with the old version after a change.

## Checklist
- [ ] Is the existing design language kept (color, type, spacing, component patterns)? Do not invent a new style; use what exists.
- [ ] Accessibility (a11y): meaningful HTML, labeled form fields, keyboard navigation, visible focus, enough contrast, alt text on images.
- [ ] Responsive design: no horizontal scroll on a narrow screen (≈375px), touch targets big enough.
- [ ] Are light and dark themes (if present) both readable?
- [ ] States: are loading, empty, error and success states all designed?
- [ ] Is the text consistent with the user's language (a local-language interface in that language; consistent terms)?
- [ ] Performance: no needless re-render, large image or blocking script.
- [ ] Security: user input is not put into HTML raw (XSS); external image and link sources are trusted.

## Verification (do not say "it works" by guessing, #24)
- Actually run the change and **see** it: a screenshot in the browser pane or `read_page`, narrow and wide screen.
- Check for console errors. Compare before and after.

## Common mistakes
- Losing information while "simplifying" existing content.
- Trying only one screen size.
- Writing color and spacing values as fixed numbers one by one (instead of tokens or variables).

## Additional methods
Ideas are in our own words.
- If a **design decision** (color, typography, layout, design system) is needed, load `expert-design` too; this pack is the coding side.
- **Interface audit:**
  - [ ] The focus ring is visible; `prefers-reduced-motion` is respected.
  - [ ] Form: every field has a label and a suitable `autocomplete`/`type` attribute; the error is next to the field.
  - [ ] Buttons have loading and disabled states; double submission is prevented.
  - [ ] Long text, a list with many items and empty data do not break the layout.
  - [ ] Date and number format suits the locale (`Intl`). `color-scheme` is set in the dark theme.
- **React/Next.js performance:**
  - [ ] Independent data requests run in parallel, not in sequence (no request waterfall).
  - [ ] A large library or a rarely used component is loaded dynamically.
  - [ ] `memo`/`useMemo` is not added without measuring. Lists have a stable `key`.
- **Component design:** Instead of many boolean props (`isPrimary`, `isLarge`, …), variants or composition (child components).
- **Verification:** A screenshot with Playwright or the browser pane (375px and wide), console log. Core Web Vitals (LCP, INP, CLS) if measurable; do not write numbers without measuring.
- **Package commands:** Before running a command whose version is not pinned, such as `npx <package>@latest`, ask the user and pin the version (e.g. shadcn CLI; supply chain).
- Idea sources: vercel-labs/agent-skills (`web-design-guidelines`, `react-best-practices`, `composition-patterns`), anthropics/skills (`webapp-testing`).

## Further methods
- **Interface testing** follows the "Web interface testing" section of the `test-writing` skill: first the page loads and the network settles, then the DOM or a screenshot is inspected, the selector is chosen from the state seen, and the action comes last.
- Use `debugging` for debugging, and `verification` before saying "it works".

## Lessons
<!-- The central agent adds verified lessons here: general and reusable, without project names or dates. -->
- When a redesign is asked to be "more functional", that means presenting more information readably, not removing existing content; do not deliver without comparing with the old version.
- If two elements have the same `id`, `querySelector` returns the first; a second renderer silently wipes the content of the first. On every page change, check with a script that no `id` is repeated and that every `$('#…')` in the code exists on the page; if there is no browser permission, run the script in Node with a fake DOM and real data (smoke test).
- Do not put non-clickable items (a group label, a separator) in a navigation bar: they look broken, take space and push the tabs to a second row. If grouping is needed, do it by ordering.
- In a grid card, if the column is not `minmax(0, 1fr)`, the content widens the card and a right-aligned link overflows the card. On a card and a list item use `minmax(0, 1fr)` + `min-width: 0` + `overflow-wrap: anywhere` on long text. Do not give `white-space: nowrap` to a badge/label that carries data.
