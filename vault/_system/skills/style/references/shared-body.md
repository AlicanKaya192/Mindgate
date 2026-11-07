# Shared body (copied verbatim into every style prompt)

In step 3 of the `style` skill, the block inside the fence below is copied without changes into `style-prompt.md`, right after the "Task" paragraph. The placeholders (`{{…}}`) are filled in only in section 1.

```
# 1. PROJECT SETTINGS: SETTINGS CHANGE ONLY HERE

**Topic:** {{TOPIC}}

- Storyboard: {{STORYBOARD}}            (On | Off)
- Voiceover: {{VOICEOVER}}              (Off | the name of the recording file in the folder)
- Subtitles: Off
- Duration if there is no voiceover: {{DURATION}} seconds (default 30)
- Format: {{FORMAT}}                    (1080×1920 vertical | 1920×1080 horizontal | 1080×1080 square)
- Frame rate: 30 fps
- Sound effects: {{EFFECTS}}            (Off | the effect files in the folder | Openverse with permission)
- Background music: {{MUSIC}}           (Off | the name of the music file in the folder)
- Output: MP4 (out/final.mp4)

This is the only section that is edited and the only source of truth. The topic is free text: a sentence or a paragraph. Every object, piece of information, label, number and scene comes from the topic or the voiceover; never from the examples elsewhere in this prompt. The same prompt must work on unrelated topics. All text on screen is in the language of the topic. If the topic involves a real product or company, do not invent the logo and colors: use the files in the `brand/` folder; if there are none, write the brand by name without a logo and say so in the report.

# 2. HOW TO WORK: CLAUDE CODE

You are in a project folder inside Claude Code.

- **Limits:** Work only in this folder. Do not delete or move any file other than the ones you produced yourself. Do not install packages or programs and do not go to the web: if a missing tool or permission is needed, stop, write what is needed and why, and ask the user. Do not kill processes; if a port is needed, pick a free one. There is no AI signature in the video, the credits or the code.
- **Build:** Write the animation in this folder as `index.html` (separate JS and CSS files if needed). Expose the function `window.seek(t)` (t in seconds): it draws the frame at time t deterministically. It does not depend on requestAnimationFrame timing, on `Date.now()` or on an unseeded `Math.random()`; randomness comes from a seeded generator. Timing is written as a proportion of the resolved total duration, not as fixed seconds. Fonts are loaded locally from the `fonts/` folder; if they are not in the folder, use a close match from system fonts and say so in the report.
- **Render:** Drive the installed headless browser (Edge or Chrome) with `puppeteer-core`. Open the page with `file://`, call `seek(i / fps)` for every frame, capture at the configured native resolution and encode with ffmpeg as `out/final.mp4` (H.264, yuv420p). Keep the frames under `out/frames/`.
- **If voiceover is on:** the recording is in this folder and its duration is the master clock. Get the word timestamps with an installed Whisper (if it is not installed, stop and ask). Align every visual idea to the moment it is spoken. Add the recording to the final MP4. Voiceover text or timestamps are never invented.
- **If voiceover is off:** use the fixed duration; the visuals carry the narration, with short on-screen text and moving diagrams.
- **If sound effects are on:** use the effect files in the folder. If the setting is "Openverse with permission", take CC0-licensed sound only from `api.openverse.org`, only if the user allowed that address (`/v1/audio/?q=<query>&license=cc0`). Effects are tied to sparse, meaningful moments; they are placed at exact timestamps with ffmpeg; the sources are written to `CREDITS.md`.
- **If background music is on:** only the music file the user put in this folder is used; it is mixed far below the voiceover, with ducking (lowering during the voiceover). Music is not synthesized.
- **If the storyboard is on:** first write a scene table (time, idea, composition, motion, on-screen text) and draw PNG preview frames of the important scenes; then stop and ask for approval. If it is off, make the plan yourself and deliver the finished video.

# 3. QUALITY CRITERION

- **Narration, not display.** First decide what the viewer must understand; then let the graphics themselves do the narrating: objects that transform, diagrams that build up, numbers that move. Decoration that teaches nothing is removed.
- **A connected story.** Scenes grow out of one another; an element in one idea becomes the start of the next. The video never looks like a slideshow of separate cards.
- **Clear hierarchy.** At every moment one main idea, one focal point, wide margins; text is readable on a phone and stays still long enough to be read.
- **Fluidity.** Easing in every motion; no jitter, no sudden appearing, no frame where nothing has been decided.

# 4. VERIFICATION

Render many frames from all over the timeline as PNG and look at them. Fix overflowing, overlapping, unreadable, empty or broken frames and anything that looks ordinary instead of in this style; keep going until you are proud of the result. Then render the final MP4 and report briefly what it shows: duration, resolution, scene list, and anything that is missing or filled in by assumption (font, logo, effect).
```
