# Game feel, camera and level design

Numbers are the declaration of the source pack's owner and were not independently verified. Every threshold is a starting point: measure, play, tune.

## Game feel
**Scope:** Making a hit, a collision and a pickup feel like a reaction to the player.

The numbers come from the declaration of the owner of a game development skill pack and were not independently verified; they are starting points, tune them by measuring. The maximum offset (12×8 px) can stay large for pixel art; choose the offset by the game's pixel scale. The Unity-specific `Lerp` note is in `engine-unity.md`.

**Tiers.** An event only names its tier; the values live in one table.

| Tier | Trauma | Freeze | Particles |
|---|---|---|---|
| Small | 0.10–0.20 | none | 0–4 |
| Medium | 0.30–0.50 | 0.04–0.06 s | 6–12 |
| Large | 0.70–1.00 | 0.10–0.15 s | 20–40 |

**Trauma model**
- Trauma accumulates between 0 and 1. The shake strength is the square of the trauma: a small event gets smaller, a large event stands out.
- Trauma decays in real time, 1.2 per second. A freeze does not stop the decay.
- Maximum offset 12×8 px, maximum roll 0.1 rad. Our own example:
  `shake = trauma * trauma`
  `offset = max_offset * shake * noise(t)`
- Apply the shake to the camera's offset; do not move the character's body or the camera's real position. It is added last in the camera chain.
- The noise should be smooth (noise that flows with time). A new random offset every frame looks like jitter.

**Freeze and time**
- Keep the freeze under ~0.15 s.
- With stacked freezes only the last call turns time back on. Each call pushes the end time forward; the end of the first freeze does not cut the second short.
- UI transitions and shake decay run in real time and are not affected by a freeze.
- The time scale does not slow down sound. Decide separately what the sound does during a freeze and slow motion.
- A key pressed during a freeze is buffered and handled when the freeze ends.

**Easing and squash-stretch**
- Pop in and grow with overshoot easing; settle with ease-out. Use ease-in only for anticipation.
- Squash: 1.3 horizontal, 0.7 vertical; back to normal within 0.18 s.

**Visual asset set**
- If several visuals (sprite, tileset, UI element) will be produced, first write an asset manifest; each row has name, size, state, source, license, approval.
- Before producing the whole set, have the user approve a single target image at game scale (at the game's real resolution, on the game screen).
- A UI element is not a single image: the source pack asks for 6 states per element (the list was not read); write each state as a separate row in the manifest.
- Checks for cropping, alpha and size are done with a tool, not by the model's eye (a small script that uses an image library).

**Verification**
- Trigger two freezes 30 ms apart: at the end the time scale returns to 1.0.
- Raise the trauma to 1: it becomes 0 after 1/decay seconds, and it also decreases during a freeze.
- These tests are written headless. The user confirms the feel itself by playing.

## Camera
**Scope:** Following, dead zone, look-ahead and bounds of the camera that follows the player.

**Method**
- For following, use smoothing with a coefficient of `1 - exp(-speed * dt)` or a critically damped spring.
- Inside the dead zone the camera does not move; when the target leaves the zone it starts following.
- Look-ahead: the camera shifts toward the direction of movement, and the shift builds up over a short time.
- Clamp the view to the level bounds; the player should not see outside the map.
- Shake is added last, after everything else.

**Thresholds**
| Setting | Start |
|---|---|
| Smoothing speed | 5–12 |
| Dead zone | 32–64 px |
| Look-ahead distance | 40–120 px |
| Look-ahead build-up time | 0.2–0.4 s |

**Pitfalls**
- A lerp with a fixed per-frame coefficient: at high FPS the camera follows tighter, at low FPS it lags.
- On teleport (room change, respawn, scene load), if the smoothing state is not reset the camera sweeps across the map to get there.

**Verification**
- Play the same movement at two different FPS values and compare the camera's lag behind the target. The lag should stay the same.

## Level design
**Scope:** Level geometry, teaching order, pacing and a lock-out check.

**Method**
- Measure reach first: record the highest and farthest jump with the character's real controller. The level is built with the measured value, not an estimated one.
- If the jump tuning changes, redo the measurement and recheck the levels.
- Teach a new mechanic in four steps: introduce (in a safe place), develop, twist (an unexpected use), test under pressure.
- Pacing: mark intensity from 0 to 1. Put at most 2 intense sections (0.7 and above) in a row, then let the player breathe.
- The key must not stay behind its own door. The key to each lock must be in a place reachable before that lock is opened.

**Thresholds**
| Measure | Start |
|---|---|
| Mandatory gap | 0.7 of the measured reach |
| Optional hard crossing | 0.95 of the measured reach |
| Consecutive intense sections (≥0.7) | at most 2 |

In a platformer the rule "the gap is at least 1 tile shorter than the computed reach" in the genre file also applies; take whichever of the two limits gives the shorter gap.

**Pitfalls**
- Assuming reach by guess or by looking at the grid in the editor.
- If the key and door order is checked only by playing by hand, a lock-out is missed.

**Verification**
- Write a goal reachability check (`goal_reachable` in the source): is there a path from the start to the goal that follows the key order. If not, the level is locked out.
- The pacing check (`pacing_problems` in the source) should return empty: the consecutive intense section limit is not exceeded.
- Whether the flow is good is decided by the user by playing.
