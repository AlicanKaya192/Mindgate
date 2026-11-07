# Style sections: what is written, what the criterion is

Step 3 of the `style` skill. Every section is drawn from the reference image, but no section describes the layout, the text or the logo of the reference. 2,000–4,000 words in total. In every section both "how it looks" and "how it is made" are written; a sentence that gives no concrete number (hex, px, ms, ratio) is a weak sentence.

## 1. Visual language and palette
- Hex values sampled with a script; the approximate area proportion of each color (e.g. background 70%, main ink 20%, accent 5%).
- **Which color may be used where:** background, text, accent, warning. What is the accent color reserved for (only the key number? only the moving element?)?
- Forbidden pairings and the contrast limit (text on the background at least 4.5:1).

## 2. Material and surface
- What the image is physically made of: paper, ink, screen print, glass, light, pixels, fabric…
- The behaviour of the material: edge (sharp, torn, ink spread), grain, shadow (cast, inner, none), overprint, wear, misregistration.
- Every texture is produced **deterministically**: seeded noise (value/Perlin/simplex), a fixed seed, layers produced in advance and cached. No ready-made texture picture placed over the screen.

## 3. Typography
- The typefaces and the free web fonts that fit them (by name); separately for title, body, label and number.
- Sizes (px by format), capitalization, letter spacing, line spacing.
- How the text sits on the page: printed into the background, stuck on top, cut out?
- Entrance and exit: letter by letter, line by line, like a stamp; which easing and duration.

## 4. Composition habits
- Grid rhythm, margins, scale contrast (the ratio of the biggest to the smallest element), use of empty space, cropping habit.
- Write the **habits**, not the reference's own layout: "one giant number with a small label beside it" is a habit; "a red circle at the top left" is a layout.

## 5. Signature elements
- 3–5 things that make this look recognizable. For each: how it looks, why it belongs to this style, how many times and where it is used in the video (overuse turns a signature into decoration).

## 6. Technical implementation (the most important section)
- The choice of renderer and the reason: Canvas 2D, SVG or WebGL. If texture and light are heavy, WebGL; if vector and text are heavy, SVG or Canvas.
- The layer structure (bottom to top): background, texture, shapes, text, overprint, post-processing (vignette, grain).
- Offscreen buffers (offscreen canvas), masks, blend modes (`multiply`, `screen`), shaders or noise functions, step by step.
- How the textures are produced and cached; that they are not regenerated on a `seek(t)` call.
- The performance limit: the draw time per frame is measured; if it is too slow, first a cache, then an intermediate buffer at reduced resolution.

## 7. Signature motion
- How this material would move if it were real: an ink stamp (sudden landing, slight spread), a paper slide (with friction, slightly delayed), a light sweep.
- Timing (ms) and easing curves (e.g. `cubic-bezier` values); the motion hierarchy: first the main element, then the supporting ones, last the detail.
- The stillness margin: for how long at least the text to be read stays still.

## 8. Transitions
- Most scene changes are a plain cut or a camera move, like an edited film.
- For big moments, 1–2 signature transitions from the style's own material (e.g. the paper tearing to show what is underneath, ink spreading to fill the screen); when they are used.

## 9. Information design
- The kinds of diagram that suit this style (flow, comparison, timeline, proportion).
- How numbers, labels, arrows and charts look in this style; the counting-up (count-up) motion.
- Readability on a phone: the smallest text size, the most words on the screen.

## 10. Sound
- Effect types that suit the material, as search terms (e.g. "paper slide", "rubber stamp", "pen scratch"). The sparse-use rule.

## 11. Cheap shortcuts to avoid
4–6 ways in which the model usually imitates this look and what to do in place of each. Format: **shortcut → why it looks fake → instead**. Example types: a flat color instead of a real overprint, a blur instead of refraction, a ready-made gradient, a fixed texture picture, everything sliding at the same time, the same easing on every element.
