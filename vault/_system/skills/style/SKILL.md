---
name: style
description: Use when the user gives one or more reference images (a poster, an ad, a screenshot, any design) and wants a reusable animated explainer video style extracted from it, a video made in that style, or the image turned into a template. Load it for requests such as "extract a style from this image", "make a video in this style", "turn it into a template", "turn this into motion graphics", "turn this poster into a video style", and when an image is given with a request for motion graphics. The main chat loads it.
---

Workflow skill (not an agent). Linked rules: #14, #22, #24, #32, #35, #39, #44, #45. For design critique `expert-design` alongside, for code `clean-code`.

Purpose: to extract a **living video style** from a still image. The result should look as if it came from an explainer sequence made by the same designer; not like "objects sliding over a poster".

The real output is a **style prompt**: a long, self-contained prompt that, run in a fresh Claude Code session with no other context, produces this look on any subject. Detail is the work itself: a short description like "cream paper, bold type" gives an average video. A prompt that explains how the look is built, how it moves and how it is usually imitated gives a good video.

## 1. Context and environment
- The reference image(s) and the subject: if the subject was not given, ask only for that.
- Read the user's design taste and rejections (`me/profile.md`, the lines tagged `design` in `ideas/rejected-proposals.md`; #39). This information is not written into the skill or the style prompt as personal information (#44).
- **The project folder is outside the vault** (html, js and video do not go into the vault). If no folder was given, ask.
- Tool check: `ffmpeg -version`, `node --version`, an installed headless browser (the Edge or Chrome path), `puppeteer-core` (or Playwright) in the project folder. **Do not install** what is missing yourself. Write what is missing, why it is needed and its source, and ask for permission (#35, #19). An npm install is done with `--ignore-scripts`; a browser is not downloaded, the installed one is used.
- Docker: because the browser draws with the GPU, the job depends on local hardware and under #45 is not suitable for Docker; say this in one line.

## 2. Read the images
- Look at each image at full size and in cropped parts (corners, text, texture, edges). Do the cropping with a script (ffmpeg `crop` or Pillow).
- **Do not guess colors by eye:** sample the dominant colors with a script (e.g. k-means or a histogram on a shrunk image). Take the hex values and the approximate proportions from the output (#24).
- Separate what is material (paper, ink, glass, light, pixels), what is composition and what is text. What is taken is the material and the habits; the layout, the text and the logo are not taken.

## 3. Write the style prompt
`<project>/style-prompt.md` is written in this order:
1. **Task:** the name of the style and the goal in a single paragraph: a first-class animated explainer video in this visual language, not a slideshow.
2. **Shared body:** the block in `references/shared-body.md` **verbatim**, with its `{{…}}` placeholders.
3. **Style sections:** 2,000–4,000 words written by you. The content and the criterion of each section are in `references/style-sections.md`; read it before writing. The sections: visual language and palette, material and surface, typography, composition habits, signature elements, technical implementation, signature motion, transitions, information design, sound, cheap shortcuts to avoid.

The style prompt is written like craft knowledge that an expert designer hands to an apprentice: concrete enough to be built. Most of the effort goes into the **technical implementation** section; it is what separates average output from good output.

## 4. Test the prompt, not only the video
1. Fill in the config with the user's subject: duration 8 s, storyboard off, sound and effects off.
2. Run the prompt **as written** in a fresh context: a sub-agent (`general-purpose`, with `model` written explicitly). Give the task text only the prompt, the project folder and the rules: no deletion (it overwrites only its own output files), no going to the web, no installing packages, no killing processes. If a sub-agent cannot be used, apply it yourself looking only at the prompt.
3. Extract frames from the video (`ffmpeg -vf fps=2`) and make a montage side by side with the reference. Judge honestly: would someone believe the two were made by the same designer? In the judgment use the critique steps of `expert-design`.
4. If they would not, fix the **prompt line** that creates the biggest difference (do not fix the video by hand) and run again. In every round keep a "difference → the line changed in the prompt" record.
5. The first draft is not a finished prompt: expect 2–3 rounds. The style is ready when a fresh, unaided run comes out as good as the reference.

## 5. Delivery and learning
- Show the test video and `style-prompt.md`; summarize the round records briefly.
- When the user gives feedback, fix the video and add the lesson, in the user's own words, to the **"Notes"** section at the end of the prompt, so that the next video does not need the same fix. A rejected proposal is also written to `rejected-proposals` (#39).
- There is no AI signature in the video or the credits (#14).

## Copyright and brand
- **Take the style, not the picture:** the visual language is used; original drawing, composition, text and logos never. Every frame is a new layout built for the subject.
- If the subject mentions a real product or company name, the logo and colors are **not invented**: the file the user put in the project folder is used; if there is none, the brand is written by name without a logo and the user is told. A logo is not downloaded from the web without permission (#32).

## Verify before finishing
- [ ] The hex values come from the script output; the style sections are 2,000–4,000 words and all 11 sections are present.
- [ ] The shared body was copied without changes; the placeholders are in place.
- [ ] At least one fresh run was done; the side-by-side montage with the reference was seen; the round records exist.
- [ ] No text, logo or layout was copied from the reference.
- [ ] Installs, downloads and web access were done only with the permission received; no files were deleted outside the project.

## Idea sources
- The `/stil` skill: adapted from a public /stil skill text (the source address given with the text: `smokich.gosem.dev/stil`). The site was not opened; its owner and license were not verified. The idea was taken and the text was rewritten in our own sentences and according to our rules (#35). What changed: permission instead of installing a missing tool by itself, sound and font downloads with permission, a logo only from the user's file, output outside the vault.

## Lessons
<!-- The central agent adds verified lessons here: general and reusable, without project names or dates. -->
