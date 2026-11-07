# Motion, interaction and UX measures

**(S)** is from the scout's report, not compared with the raw text; the others were read from the page on 30 October 2026.

## Motion: is it needed first?
- Ask the purpose: does it explain a cause or a result, give spatial continuity, or is it a rare delight? If there is no answer, do not add it. (Kowalski, Vercel)
- Look at frequency: no motion on something seen dozens to hundreds of times a day. The Raycast launch has no animation at all. (Kowalski)
- **An action triggered by keyboard is never animated.** (Kowalski)
- No needless motion on frequent, unremarkable actions: right-click menu, adding and removing in a list, hover on a minor button. (Freiberg)
- On a functional data screen, no motion at all is often best. (S, Kowalski)
- A marketing page is separate: there motion can tell a story and be longer. (Kowalski)
- In a themed scene motion can be part of the identity. These rules are for frequent actions, not for a scene.

## Motion: how
- Duration: ≤200 ms for interaction (Freiberg), <300 ms for general UI; a 180 ms selection feels more responsive than 400 ms. (Kowalski)
- Ease-out on enter and exit. Ease-in does not suit UI: it speeds up at the end, and the same 300 ms dropdown feels slow. (Kowalski)
- Built-in CSS curves are often weak; use a custom curve. Linear for continuous rotation. (Kowalski; S, Fluent)
- Do not start from `scale(0)`: start from ~0.9+ with opacity (Kowalski's example 0.93); a dialog from ~0.8 (Freiberg).
- On press, `scale(0.97)` with `:active` (Kowalski), ~0.96 or ~0.9 (Freiberg); 0.8 is too much.
- A popover opens from its trigger; `transform-origin: center` is often wrong. (Kowalski, Vercel)
- Tooltip: a delay on the first, no delay and no animation on the following ones in a group. Do not put interactive content in it. (Kowalski, Vercel, Freiberg)
- Only `transform` and `opacity`; avoid `width`, `height`, `top`, `left`. `transition: all` is forbidden; write properties one by one. (Vercel)
- Motion should be interruptible. CSS first, then the Web Animations API, then a JS library. (Vercel)
- For motion that autoplays and lasts >5 s, a pause or hide button. Pause a loop that is not visible. (Vercel, Freiberg)
- A `prefers-reduced-motion` counterpart is mandatory. (Vercel)
- If a transition is still bad, ~2 px of `blur` between two states can be tried; large blur is slow. (Kowalski, Freiberg)
- A blurred or scaled solid rectangle shows banding; use a radial gradient. (Freiberg)

## Waiting and feedback
- <0.1 s feels instant; 1 s keeps the flow of thought; >10 s needs a percentage, remaining time and cancel. (S, NN/g) Doherty: <400 ms is productive. (S, Laws of UX)
- On a task >10 s, say the remaining time. (NN/g) Over 1 s an indicator, 2–10 s circular, over 10 s a percentage. (S, NN/g)
- The indicator starts with a ~150–300 ms delay, stays visible ~300–500 ms; no flicker. (Vercel)
- The skeleton has exactly the same dimensions as the final content, the layout does not shift. (Vercel) For loads under 10 s. (S, NN/g)
- A loading button shows the indicator and keeps its label. (Vercel)
- Optimistic update: if success is likely, change at once; on error revert or offer Undo. (Vercel, Freiberg; S, Wroblewski)
- Feedback next to the trigger: on copy, an in-place checkmark, not a notification. (Freiberg)
- A destructive action gets confirmation or a timed Undo. (Vercel) A toggle takes effect at once and asks no confirmation. (Freiberg)
- Write operation <500 ms budget. (Vercel)

## States
- Empty, sparse, dense and error are designed separately. Short, average and very long content do not break the layout. (Vercel)
- An empty screen says what it is and how it will fill, and leads to a new item or a template. (Freiberg; S, NN/g)
- No dead ends: every screen has a next step or a way out. (Vercel)
- An error says what happened and how to fix it in plain language. (Vercel; S, NN/g)

## Forms
- A label on every field, clicking it focuses the field; a placeholder is not a label, it shows an example. (Vercel, Freiberg; S, Smashing)
- Do not disable the submit button in advance; lock it once submission starts and show an indicator. (Vercel)
- The error is next to the field; on submit focus the first error. (Vercel) Show validation after typing stops. (S, Smashing)
- Do not block keystrokes or pasting; show a warning. Warn on leaving with unsaved changes. (Vercel)
- Right `type`, `inputmode`, `autocomplete`. Enter submits. On mobile, input ≥16 px prevents iOS zoom. (Vercel, Freiberg)
- Reduce the number of fields; single column; group when there are more than six questions. (S, Smashing)
- A dropdown is the last resort: a stepper or radio for few options, one date picker instead of six menus. (S, Wroblewski)

## Data-dense screens and tables
- Numbers use `tabular-nums`; decimals as needed, the exact value on the server is kept. (Vercel; S, Smashing)
- Key columns (name, status) do not scroll. A small table turns into a stack of cards on mobile. (S, Smashing)
- Clickable element ≥40×40 px, the layout does not break at 200% zoom. (S, Smashing)
- Virtualize a large list. (Vercel)
- Keep sidebars and headings dense, make room for content. (Linear)

## Interaction details
- Keyboard everywhere; `:focus-visible`; the focus ring does not stay under a sticky header. (Vercel) `box-shadow` for a ring that follows the radius. (Freiberg)
- If the visual target is <24 px, enlarge the target to 24 px; ≥44 px on mobile. Do not disable zoom. (Vercel)
- A link is an `<a>`, not a `<button>` or a `<div>`. (Vercel)
- In an ordered list, navigate with ↑ ↓; a dropdown opens instantly on `mousedown`. (Freiberg)
- Hover state inside `@media (hover: hover)`; no flicker on touch. (Freiberg)
- Filters, tabs and pagination live in the URL; the Back button keeps the scroll position. (Vercel)
- `aria-label` only on an icon-only button; no tooltip on a disabled button. (Freiberg)
- Decorative elements (glow, gradient) get `pointer-events: none`. (Freiberg)

## Laws (S, Laws of UX)
- Jakob: users expect what they learned elsewhere. Hick: decisions take longer as options grow. Fitts: a small, distant target takes longer to reach. Miller: 7 ± 2 items. Peak-end: an experience is remembered by its most intense moment and its end. Aesthetic-usability: what is beautiful is thought more usable, which can hide problems.

## Conflicts
- **Touch target:** Vercel 44 px, Smashing 48 dp and 40 px (2018, 2019). Use ≥44 px on mobile.
- **Contrast:** Vercel prefers APCA; this skill keeps WCAG 2.2 AA as the minimum.
- **First focus:** Vercel says autofocus on a single main input on desktop, rarely on mobile; Freiberg says none on touch. Compatible.
- **Writing marks:** Vercel's Title Case and `&` preferences belong to its own brand, not universal.
