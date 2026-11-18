# Save system, dialogue, input and game UI

Numbers are the declaration of the source pack's owner and were not independently verified. Every threshold is a starting point: measure, play, tune.

## Save system
**Scope:** Writing game state to disk, reading it back and carrying it across versions.

**Method**
- Save plain data: dictionary, list, number, string. An engine object or a scene node is not saved.
- Put an integer `version` field in from the first version.
- Atomic write: write to a temporary file first, make the existing save a `.bak`, then rename the temporary file to the real name. If the write is cut halfway, the old save stays intact.
- Defensive loading:
  - If the save is from a newer version than the game knows, reject it and do not write over it.
  - Migrate an old version step by step (1→2→3), do not skip.
  - If the file is corrupt, fall back to the `.bak`.
- Autosave at most every 60 s. Use a ring of 3 slots; the oldest is written over.
- Derived data (total stats, map cache) is not saved; it is recomputed on load.
- In a roguelike the run and the profile are separate files (`genres.md`).

**Pitfalls**
- Godot JSON loses an integer above 2^53; store large IDs as strings.
- Godot `str_to_var` can run scripts on an untrusted save; do not use it to read saves.
- A NaN or infinite value is not saved; check before writing.
- Roblox DataStore rules are separate: `engine-roblox.md`.

**Verification**
- Write, read, compare: the state should come back exactly the same.
- Migrate sample saves of old versions; see that a save of a newer version is rejected.
- Cut a write halfway (leave the temporary file) and see that loading falls back to the intact save.

## Dialogue
**Scope:** Dialogue graph, conditions and choice outcomes. For the text itself see `expert-writing`.

**Method**
- Choose the tool by the content: Ink for dense prose, Yarn if a tight tie to the engine is needed, a small JSON graph if neither is needed.
- Give every line a stable ID from the start; translation, voice-over and the read marker are tied to this ID.
- The cost of a choice (money, item, relationship points) is deducted at the choice transition, not when the line is shown.
- Do not run conditions with `eval()`. Write a small evaluator that knows only the allowed variables and operations.

**Verification**
- Walk every path automatically: is every node reachable, is there a dead end.
- Unreachable ending check in a visual novel: `genres.md`.

## Input
**Scope:** Key and gamepad mapping, buffer, dead zone, accessibility.

**Method**
- Give actions intent names (`jump`, `interact`), not key names.
- A radial dead zone of 0.2 on the analog stick.
- The input buffer is 0.15 s and counted in game time; it does not expire during a freeze or a pause.
- On remapping, save the physical key position; the keys do not shift when the keyboard layout changes.
- Accessibility: full remapping, a toggle option instead of hold, adjustable timing.

**Pitfalls**
- A misspelled action name fails silently (e.g. Unity `FindAction`).
- The Enhanced Input context in Unreal: `engine-unreal.md`.

**Verification**
- Check that every action name used in code is in the mapping file.
- The agent cannot press a button. The user tries gamepad, touch and vibration behavior; device behavior that was not seen is reported as "not verified".

## Game UI
**Scope:** HUD, menu, settings screen. For non-game interfaces see `expert-design` and `expert-frontend`.

**Method**
- Build the layout with anchors and containers, not fixed positions. Reference resolution 1920×1080.
- Keep screens in a stack; do not track open menus with separate bool flags.
- Every screen that opens should give focus to an element; without focus a gamepad player is stuck.
- Leave room for translation: German text comes out about 30% longer.

**Thresholds**
| Measure | Start |
|---|---|
| Text size (1080p) | PC 18 px, console 26 px |
| UI scale | up to 200% without breaking |
| Contrast | text 4.5:1; large text and UI elements 3:1 |
| Touch target | about 9 mm |

**Verification**
- Take screenshots at three different resolutions, open them and look: is there overflow, clipping, unreadable text.
- Write a test that walks the menu from start to finish with only a gamepad, or have the user check it.
- Visual states of a UI element: `feel-camera-level.md` → Game feel, "Visual asset set".
