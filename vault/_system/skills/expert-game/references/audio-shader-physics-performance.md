# Audio, shaders, physics tuning and performance

Numbers are the declaration of the source pack's owner and were not independently verified. Every threshold is a starting point: measure, play, tune.

## Audio
**Scope:** Audio buses, loudness, ducking, variation, music transitions.

**Method**
- Buses: under Master, Music, MusicDuck, SFX, Ambience, UI, Voice. Every sound source is assigned to a bus.
- The settings slider goes from 0 to 1. Take the square of the value and convert it to dB; at 0 mute the bus.
- Ducking: when speech or an important sound arrives, the music is lowered (the MusicDuck bus).
- On every SFX play, randomize the pitch by ±1 semitone and the level by ±2 dB; the same sound should not sound like a machine in a row.
- Music layers change with intensity using hysteresis: switch to the intense layer at 0.6, go back at 0.4.
- Music timing is tied to the audio clock, not the game clock.
- What sound does during a freeze and slow motion: `feel-camera-level.md` → Game feel, "Freeze and time".

**Thresholds**
| Measure | Start |
|---|---|
| True peak | ≤ -1 dBTP |
| Average loudness | PC and console about -24 LUFS, mobile about -18 LUFS |
| Ducking ratio | 4:1–8:1 |
| Ducking attack | ≤10 ms |
| Ducking release | 300–500 ms |

**Pitfalls**
- Engine-specific (Godot bus, `volume_db`, `max_polyphony`; Ebitengine audio context): the relevant engine file.

**Verification**
- Record 2–5 minutes of the game's audio output and measure it with `ebur128` (an ffmpeg filter). If the tool is missing, say what is needed and why, and ask permission.
- The agent cannot listen. The user decides on the audio balance by listening.

## Shader
**Scope:** Writing shaders, checking compilation and porting across engines.

**Method**
- Do all of the math in a single space (world or view); do not mix two spaces.
- Renormalize the normal in the fragment stage; interpolation breaks the length.
- Also check compilation outside the engine: `glslangValidator` for GLSL, `naga` for WGSL. Ask if the tool is missing.
- Edge value test: draw the inputs with 0, 1, negative and very large values.

**Pitfalls**
- If the edges of `smoothstep` are reversed (the first edge larger than the second) the result is undefined.
- The texture V axis can be flipped between engines; check when porting.
- On mobile `mediump` precision causes flicker with large values.
- Shader compilation on first use causes a hitch (see the performance section).
- Engine-specific (Godot `TIME`, `ALPHA`): `engine-godot.md`.

**Verification**
- The validator passes clean; the edge value images are opened and looked at.

## Physics tuning
**Scope:** Physics step, tunneling, mass ratio, stability.

**Method**
- Physics runs in a fixed step; drawing interpolates between two steps.
- Prevent tunneling: the distance per tick should be shorter than the thinnest wall (`speed / tick < thinnest wall`). If not, use continuous collision or a shapecast.
- Keep the mass ratio of colliding bodies within about 1:10.
- Death spiral: a long frame asks for many physics steps, and the steps make the frame even longer. Put an upper limit on the number of steps per frame.

**Pitfalls**
- On teleport (respawn, door), if the interpolation history is not reset the body is drawn sliding between two positions.
- Moving a body by changing its position directly skips collision (Godot `position +=`, Phaser Arcade `x/y`).

**Verification**
- Tunnel test: throw the fastest body at the thinnest wall; it should not pass.
- Measure the speed of the same movement at 30 and 144 FPS (a speed probe); the result should be the same.

## Performance
**Scope:** Measuring a frame rate problem and finding the largest cost.

**Method**
- Turn the "it stutters" complaint into a ms budget: how many ms fall to one frame at the target frame rate.
- Measurement conditions: VSync off, a release build, the target hardware. A number measured in the editor does not decide.
- First separate whether it is CPU or GPU bound. Then find the single largest cost and fix it first.
- Measurement: 3 runs on the same machine; 60 frames of warm-up, then 600 samples; look at p95, not the average.
- On mobile leave a 20–30% margin in the budget.
- First-use shader hitch: warm the shaders up in advance on the loading screen.

**Pitfalls**
- Measuring in a debug build or with VSync on.
- Engine-specific memory and pixel ratio problems (PixiJS `removeChild`, three.js pixel ratio): `engine-web.md`.

**Verification**
- Take 3 measurements under the same conditions before and after the change, compare the p95 values.
- On the target device the user decides on smoothness.
