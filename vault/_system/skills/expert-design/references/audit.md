# Measuring audit

Renders and measures the running page in a real browser. The standard library and an installed Edge or Chrome are enough; no package is installed. For web interfaces only. For desktop interfaces (WinUI, Slint, Qt) use a manual list and screenshots.

## Usage
A local page or server is also a page: permission under #32 is obtained before opening it.

```bash
{{PY}} -I scripts/page_audit.py http://localhost:3000/ http://localhost:3000/settings --output audit --record design-record.json --baseline
```

| Option | What it does |
|---|---|
| `--output` | Full-page images and `summary.json` |
| `--record` | The project's design record; kept in the project |
| `--baseline` | Writes this measurement as the inventory before the redesign. Run once **before** the change |
| `--note "..."` | Writes the user's comment of this round to the round |
| `--widths` | Default 320, 375, 768, 1280, 1440, 1920; the dark theme is also measured at 375 and 1440 |
| `--external-url` | Opens a non-local address and the external network. Only with site permission |

Exit code: 0 passed, 1 failed, 2 usage error. **Passed does not mean beautiful:** the measurement catches only what is measurable; the images are still looked at by eye.

**Safe default:** A non-local address is refused and the page is blocked from reaching the external network. A page that uses an external font or a CDN may therefore appear with a fallback font; look at `external_resources` in `summary.json` and at the image.

## Design record (`design-record.json`)
```json
{
  "keep": ["search", "bookmarks"],
  "add": ["dense table"],
  "exemptions": [{"rule": "T04", "scope": ".chip", "reason": "dense filter, desktop", "date": "YYYY-MM-DD"}],
  "removed": [{"type": "buttons", "name": "Submit", "reason": "reduced to a single button in the top menu"}],
  "baseline_inventory": {},
  "rounds": []
}
```
- **Keep and add:** Written in step 1; the change is made according to them.
- **Exemption:** `reason` is mandatory; an exemption without a reason is invalid and fails the check. `scope` is searched in the selector; if empty, the rule is exempt on the whole page. An exemption that is no longer used is reported and removed.
- **House style:** If the same rule is exempt on 3 pages, it is not an exception but a rule; it is written to the project's design decisions.
- **Preservation counter:** Links, buttons, fields, headings, images and tables are compared by name. Every lost element is written by name as `LOST` and fails the check; if it was removed deliberately, it is written to `removed` with its reason. Event listeners are not counted; the list of buttons and links is an approximation of them.
- **Rounds:** Every run is written as a round. If a new error or warning appears it is called `REGRESSED`: while fixing one place, another was broken.

## Rules
An **error** fails the check, a **warning** is fixed or justified, a **note** is looked at and a decision is made. Notes are not accusations; they ask whether the choice is deliberate.

| Rule | Severity | Measured | Basis |
|---|---|---|---|
| T01 | error | Horizontal scroll | Responsive layout |
| T02 | error | Element overflowing the screen | Responsive layout |
| T03 | error | Text contrast: <4.5:1, <3:1 for large | WCAG 1.4.3 |
| T04 | error, warning | Target <24 px; <44 px on mobile | WCAG 2.5.8, Vercel |
| T05 | warning | Input text <16 px on mobile | Vercel, Freiberg |
| T06 | warning | Dominant text <16 on mobile, <14 px on desktop | Hobday, Fluent |
| T07 | warning | Average >90 characters per line | Butterick |
| T08 | warning | Line height <120% | Butterick |
| T09 | warning | More than 2 font families | Hobday |
| T10 | note | More than 25% of spacings outside the 4-step scale | Hobday |
| T11 | note | More than 4 color families | NN/g: too much color |
| T12 | note | Pure black or white | Hobday, Refactoring UI |
| T13 | note | More than 3 shadows; shadow in a dark interface | Hobday |
| T14 | warning | Inner corner radius mismatch | Hobday |
| T15 | warning | `transition: all` | Vercel |
| T16 | warning | Transition >300 ms on a control | Kowalski |
| T17 | error | Element with no alt text, label or name | WCAG 1.1.1, 4.1.2 |
| T18 | warning | Lorem ipsum, John Doe | AI trace |
| T19–T24 | note | Gradient text, card with a side stripe, small uppercase label, small mono label, emoji icon, arrow at the end of text | `ai-traces.md` |
| T25 | warning | Button or menu label breaks across lines | Generated-interface audit |
| T26 | note | No `tabular-nums` on table numbers | Freiberg, Vercel |
| T27 | warning | Motion without `prefers-reduced-motion` | WCAG 2.3.3, Vercel |
| T28 | warning | No visible change on focus | WCAG 2.4.7 |
| T29 | note | Content is short, the bottom of the screen is empty | Generated-interface audit |
| T30 | warning | Number of h1 is not 1 | Vercel |

**Measurements** (`summary.json`, not rules, interpreted by eye): control heights, section spacings, words on the first screen, whether h1 is on the first screen, dominant text, font families, color family, shadow and corner variety, unmeasurable contrast, external resources. A very different value in control heights or irregular section spacing is a sign of inconsistency. No numeric threshold was set because no sourced threshold was found.

## Limits
- The contrast of text on an image or gradient background is not measured (`unmeasurable_contrast`); overlapping elements are not taken into account.
- It cannot read code; it sees only the first rendered state. For a dropdown, dialog and error state, the address that leads to that state must be measured.
- The theme changes only through `prefers-color-scheme`; the dark form of a page that switches theme by class is not measured.
- Taste, originality and choosing the right pattern are not measured: steps 4 and 8 of the flow are for that.
