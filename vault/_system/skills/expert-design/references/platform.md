# Platform guides and licenses

## Apple HIG
- Because the pages are drawn with JavaScript, the HTML comes back empty. Read from the JSON (with web permission, #32):
  - Table of contents: `https://developer.apple.com/tutorials/data/design/human-interface-guidelines.json`
  - Page: `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/<page>.json` (layout, typography, color, materials, accessibility…)
- The HIG's platform-independent principles apply in every project: hierarchy, grouping, color roles named by purpose, minimum type size, contrast, target size and spacing, reduced motion; tabs are for navigation and actions go in the toolbar. Apple-specific looks such as Liquid Glass and system APIs are not copied to Windows.
- **License:** SF fonts may be used only to make mockups for Apple platforms. Embedding them in an app and using them on a website is forbidden (Apple font license). The SF Symbols license was not verified; do not use it in a non-Apple project. Never used in an app icon or logo.

## Microsoft Fluent
- `fluent2.microsoft.design/typography` and `/motion` open. Scout report (30 October 2026, not compared with the raw text): Body 1 14/20 px, Caption 1 12/16 px, Title 1 32/40 px; no linear curve except for continuous rotation; a reduce-motion setting is offered.
- In a themed app take Fluent for structure and accessibility; the project provides the visual identity.

## Material 3
The `m3.material.io` pages are drawn with JavaScript; the scout could read nothing beyond the headings. If a number is needed another route is sought; it is not written from memory.

## Figma
For Figma to code there is an official Figma MCP. It needs an account and design data goes to an external service. Ask the user before installing (#23, #27).

## CSS trap
Make sure the section class and the element class do not override each other. This happens most with spacing between sections (padding, margin).
