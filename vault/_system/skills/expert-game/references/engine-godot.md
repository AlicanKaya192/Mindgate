# Godot

The source pack targets Godot 4.7.2; version and behavior information is the owner's declaration of 11 November 2026 and was not independently verified. Read the project's version from `project.godot`; if it differs, do not apply the API in this file blindly.

## Verification chain
**Scope:** The counterpart of the general ladder (SKILL.md §4) in a Godot project.

1. **Import:** In a fresh clone `godot --headless --path . --import`.
2. **Static check:** Broken `res://` paths, uid consistency, orphan `.import` and `.uid` files, ExtResource and `[connection]` lines in scenes, the autoload list. In the source `check_godot_project.py` does this; if you do not have it, do the same check with your own small script.
3. **Headless test:** A test runner with `--script`. If a test fails the runner exits with 1, otherwise 0.
4. **Smoke run:** Run the game briefly with `--quit-after 300`; search the log for `SCRIPT ERROR|^ERROR:`.
5. **Human playtest.**

**Pitfalls**
- Godot also exits with 0 on a script error. The real signal is the log.
- A bare `assert()` does not count the test as failed; write the failure to the runner's counter.
- Before trusting green, break a test on purpose and see that the exit code is 1.
- In CI put a timeout on the job (`timeout-minutes: 5` in the source).
- In PowerShell redirect stdout and stderr to a file, then read the file.
- Test scripts load the target scene and `_ready` runs: a test runs the project's code.

## GDScript
- `:=` type inference gives an error in functions that return Variant (`max`, `min`, `clamp`). Use the typed versions (such as `maxi`, `clampf`).
- `--check-only` does not recognize autoload names; in a script that uses autoloads it can show a false error.

## Physics and collision
- Do not multiply `velocity` by `delta`; `move_and_slide` does it itself.
- `is_on_floor` is correct only after the `move_and_slide` call.
- `position +=` skips collision; move the body with physics methods.
- The layer is "what I am", the mask is "what I scan". The bit of layer n is `1 << (n - 1)`.
- Do not change the scene tree inside a physics callback (adding, deleting, moving nodes); use `call_deferred`.

## Signals and groups
- The same lambda produces a new Callable at every connect; to disconnect, store the Callable in a variable.
- `call_group` silently skips a node that does not have the method; if the name is misspelled nothing happens.

## Animation and tween
- A looping clip does not emit the `animation_finished` signal.
- In an opacity tween use `modulate:a` instead of `modulate`; the color is not disturbed.

## Resource and file
- A Resource is shared between instances. Before changing an instance, copy it with `duplicate_deep`.
- `res://` is read-only in an exported game; save and settings are written to `user://`.
- JSON loses an integer above 2^53. `str_to_var` can run scripts on untrusted data (`save-dialogue-input-ui.md`).

## Shader
- `TIME` wraps around at 3600 s; there is a jump in a long session.
- Writing to `ALPHA` in a spatial shader puts the object into the transparent pipeline.

## Audio
- A sound assigned to a bus that does not exist plays on Master, no error.
- `volume_db` is not linear; convert the slider value to dB.
- `max_polyphony` is 1: in a frequently played sound a new play cuts the previous one.

## Network
- `@rpc` by default allows only the authority to call.
- The RPC definition must be the same in the server and client builds.

## Export
- The export template must match the engine version exactly.
- The output folder must exist before the export.
- If the web build uses threads, the server must send the COOP/COEP headers.
- A project that uses C# cannot be exported to the web.
- `export_credentials.cfg` does not go into git; check that it is in `.gitignore`.

## From Godot 3 to 4
| Godot 3 | Godot 4 |
|---|---|
| `export`, `onready`, `tool` | `@export`, `@onready`, `@tool` |
| `yield` | `await` |
| `setget` | `set` / `get` inside the property |
| `connect("x", self, "m")` | `x.connect(m)` |
| `instance()` | `instantiate()` |
| `move_and_slide(v, up)` | `velocity` and `up_direction` properties, a call with no arguments |
| `rect_*` | `size`, `position` |
| Tween node | `create_tween()` |
| `SCREEN_TEXTURE` | a sampler declared with `hint_screen_texture` |
| `hint_color` | `source_color` |
| TileMap | TileMapLayer (4.3) |
