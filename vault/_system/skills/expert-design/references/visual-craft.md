# Visual craft measures

A safe starting point, not a rule: break it if you have a reason (Hobday). **(S)** is from the scout's report, not compared with the raw text; the others were read from the page on 30 October 2026.

## Color
- Near-black and near-white instead of pure black and white. (Hobday, Refactoring UI)
- Slightly saturate the greys toward the main color: <5% in HSB. Do not mix warm and cool. (Hobday)
- Most of an interface is grey. 8–10 shades of grey, 1–2 main colors with 5–10 shades, accents sparse; a complex interface can go up to 10 colors. (Refactoring UI)
- Define shades in advance; do not generate them on the fly with `lighten`/`darken`. 9 steps: first 500 (the shade that will be the button background), then 900 and 100, then 700 and 300, then the ones in between. The math is a starting point; fix by eye. (Refactoring UI)
- The 5 colors from a palette generator are not enough; a real interface cannot be built with them. (Refactoring UI)
- The colors in a palette should differ from each other in lightness. (Hobday)
- In HSL the same lightness looks different across hues. Use a perceptual space: OKLCH (S, Evil Martians), LCH (Linear), CIELAB (Stripe).
- Few inputs for a theme: Linear cut 98 variables to 3 (base, accent, contrast). The contrast variable also gives the high-contrast theme.
- If shade steps are built by contrast: a difference of ≥5 steps is enough for small text, ≥4 steps for icons and large text. (Stripe)
- Accessible does not mean vivid; WCAG looks only at contrast. (Stripe)
- When darkening, a black overlay washes the color out; keep the hue, lower the lightness. (Comeau)

## Dark theme
- Closer elements are lighter; the same in light and dark themes. (Hobday)
- The lightness gap between a container and the background in HSB is ≤12% in a dark theme and ≤7% in a light theme. (Hobday, review of about 100 sites)
- Shadows do not work in a dark interface; give depth with surface lightness. (Hobday)
- A theme switch should not trigger transition animations on elements. (Freiberg)
- Set `color-scheme: dark` and `theme-color`. (Vercel)

## Typography
- At most 2 typefaces; the second to strengthen the idea. (Hobday)
- The typeface is chosen deliberately: Butterick suggests avoiding monospace, most free typefaces and system fonts. In a Windows app the platform font can be reasonable; write the reason.
- Body ≥16 px on the web (Hobday); Butterick 15–25 px. Dense desktop: Fluent Body 14/20, Caption 12/16, Title 32/40 (S).
- Line 60–80 characters (Hobday), 45–90 (Butterick). Line height 120–145% (Butterick).
- Reduce letter and line spacing in large type, increase in small. (Hobday) About 1.5 in narrow content, about 2 in wide content, close to 1 in large headings. (S, Refactoring UI)
- 5–12% letter spacing for uppercase text; no longer than a single line. (Butterick) All caps hurts reading. (S, Fluent)
- Do not use weights below 400; 500–600 for medium headings. (Freiberg)
- Weight should not change on hover or selection; the layout shifts. (Freiberg)
- `font-variant-numeric: tabular-nums` in tables and counters. (Freiberg, Vercel)
- Curly quotes and the ellipsis character (…). No bold and italic together. Underline only on links. Centered text sparingly. (Butterick, Vercel)
- Fluid headings: such as `clamp(48px, 5vw, 72px)`. (Freiberg)
- Font subsetting and preloading. (Freiberg, Vercel)

## Spacing and alignment
- Measures should be mathematically related; multiples of 8 are a good start. (Hobday)
- Everything aligned to something. Optical alignment is often better than math; shift ±1 px. (Hobday, Vercel)
- Outer spacing ≥ inner spacing: content close together, far from the edge. (Hobday)
- Spacing is measured between contrast points. (Hobday)
- On a button, horizontal padding is 2× the vertical. (Hobday)
- A 12-column horizontal grid. (Hobday)
- Do not put two hard separations side by side (background change + border + line). (Hobday)
- In a list, do not leave dead space between clickable items; increase the padding. (Freiberg)
- Visual weight order: from heaviest to lightest, the heaviest on the outer edge. (Hobday)
- Alignment tied to line height: `calc((1lh - var(--size)) / 2)`; paragraph spacing `1lh`. (S, Shadeed)
- Center an icon on the cap height. (S, Prokopov)

## Corner, border, depth
- Inner corner = outer corner − the gap between (30 − 20 = 10). (Hobday) Child corner ≤ parent. (Vercel)
- A border should contrast with both the container and the background, not be a color between the two. (Hobday)
- Instead of a border, try separating with spacing, a contrasting background or a shadow. (S, Refactoring UI)
- Use a single depth technique; do not mix. (Hobday)
- All shadows come from one light with the same horizontal-to-vertical ratio. As elevation grows, offset and blur increase and opacity drops. (Comeau)
- Layered shadow instead of a single one: `0 1px 1px`, `0 2px 2px`, `0 4px 4px`, `0 8px 8px`, `0 16px 16px`, alpha 0.075. Vercel says at least two layers. Watch performance with many elements and in animation. (Comeau)
- Shadow color takes the hue of the background, not grey. (Comeau, Vercel)
- Simple on complex or complex on simple; no complex on complex. (Hobday)

**Conflict:** Hobday says blur = 2 × distance (`0 4px 8px`). In Comeau's layered example blur = distance; his ratio is vertical = 2 × horizontal. Use Hobday for a single shadow and Comeau for layered; pick one in the project.

## Hierarchy
- High contrast for the important element; structural elements with contrast as low as possible. (Hobday)
- The `label: value` pattern gives everything equal weight. If it is clear from the format, remove the label and merge it with the value ("3 bedrooms"); if needed, shrink and fade it. (Refactoring UI)
- If the user looks for the label (a technical spec page), emphasize the label and soften the value a little. (Refactoring UI)
- Lower the contrast of an icon next to text, because the icon looks heavy. A thin icon can be thickened next to medium-weight text. (Hobday, Vercel)
- Hover, press and focus have higher contrast than the resting state. (Vercel)

## Process (Linear)
- Saarinen designed full-screen sets and flows every day for a few weeks, produced hundreds of screens, then narrowed to a few directions. (Linear) Do not settle for a single sketch.
- Test by view types: list, board, timeline, split, full screen. The direction goes through a stress test on every main screen.
- On sidebars and tabs, label, icon and button alignment: "you don't see it at once, you feel it after a few minutes".
- A refresh does not break the product apart; it feels like evolution.
