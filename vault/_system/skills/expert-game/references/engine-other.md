# Ebitengine, Bevy, pygame-ce, LÖVE, Defold

Version and behavior information is the declaration of the source pack's owner of 11 November 2026 and was not independently verified. Read the version from the project's own file.

## Ebitengine
- 60 ticks per second. `Update` reads input and changes state; `Draw` only draws and does not change state.
- The audio context (`audio.NewContext`) is created once in the program.
- A screenshot in a headless environment: run the game under xvfb and take the image (the source uses a `-shot` flag for this; if the project has no such flag, ask before adding one). Ask also if xvfb is missing.
- In the delivery report, what was observed (screenshot, log) and what was not observed (feel, sound) are written separately.
- The macOS packaging script in the source forcibly deletes an existing folder. This skill does not do that; if the output folder exists, pick a new name or ask (#22).

## Bevy
- The source targets 0.20. Read the version from `Cargo.lock`; the API changes a lot between versions.
- Commands are deferred: a component added in the same system is not visible immediately.
- On the first update the delta is 0; guard code that divides by speed.
- Headless test: build the app with `MinimalPlugins` and advance time by hand.

## pygame-ce
- For a headless test `SDL_VIDEODRIVER=dummy`.
- Clamp `dt` at 0.05 s.
- `Rect` truncates to integers; use `FRect` for fractional positions.
- pygame and pygame-ce are not installed in the same environment; use whichever the project has.

## LÖVE
- The source targets 11.5.
- Fixed step `1/60`; clamp `dt` at 0.25.
- For pixel art call `love.graphics.setDefaultFilter("nearest")` before the images are loaded.
- `t.identity` (the name of the save folder) is decided before the first release.
- A headless run: `--frames 120` and a timeout. If the timeout exit code is 124, the game is stuck.

## Defold
- The source targets 1.14.
- Static check (`check_defold_project.py` in the source).
- Build with Bob (the source says it needs JDK 25). Ask if there is no JDK.
- Run it headless, search the log for `ERROR:SCRIPT:`.
- The test must print its own end line; if there is no line, the run did not finish.
