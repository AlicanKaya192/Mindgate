# Web: Phaser, PixiJS, three.js

The source pack targets Phaser 4.2, PixiJS 8.22 and three.js r187; version and behavior information is the owner's declaration of 11 November 2026 and was not independently verified. Read the version from `package.json` and the lock file.

## Shared
**Method**
- Keep the game rules in plain modules that do not import the engine, and test them with `node --test`.
- Smoke test in the browser (Playwright in the source): was the renderer created, is the scene or draw count greater than 0, is the console error list empty. Then open the screenshot and look at it.
- If Playwright or another test tool is not installed, say what is needed and why, and ask permission. Before opening a local server, say the address and the reason, and wait for permission (#32).

**Pitfalls**
- A test that checks only the DOM misses a canvas that draws nothing.
- If `window.game`, `window.app` or `window.renderer` was exposed for testing, remove it before release.

## Phaser
- Scene instances are reused. Reset the scene state in `init`; state set up in the constructor stays old on the second entry.
- Run the HUD as a separate scene on top of the game scene with `launch`.
- For pixel art in v4, `pixelArt: true`.
- From 3 to 4: effects moved to the filter system; `setTintFill` was removed; `Math.TAU` is 2π, check angle code carried over from 3.
- Arcade physics:
  - Do not move a dynamic body by assigning `x`/`y`; collision is skipped. Use velocity or body methods.
  - Set up the collider once in `create`, not in `update`.
  - A fast bullet passes through a thin wall (`audio-shader-physics-performance.md` → Physics tuning).

## PixiJS
- Start the application with `await app.init()`.
- The argument of the Ticker callback is not a number but a Ticker object; read the time from the object.
- `removeChild` does not free the GPU resource; destroy the finished object separately.

## three.js
- Limit the pixel ratio with `Math.min(devicePixelRatio, 1.5)`.
- `Timer` instead of `Clock` (since r183).
- Load dependencies with an import map.
- Keep the game state in a plain object, not in the scene graph; the scene is drawn from this state.
- Shadows are turned on in three places: the renderer, the light and the object (casting and receiving).
- A color texture is sRGB; data maps (normal, roughness) are linear.
- Put `OutputPass` at the end of the post-processing chain.
- If glTF comes in centimeters the model looks 100 times bigger; fix the scale.
- When duplicating a skinned model use `SkeletonUtils.clone`.
