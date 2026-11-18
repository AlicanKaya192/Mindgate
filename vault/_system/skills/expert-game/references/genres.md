# Genres

Numbers are the declaration of the source pack's owner and were not independently verified. Every threshold is a starting point: measure, play, tune. A request usually maps to one genre; in a hybrid game only the relevant part of the second genre is read. The roguelike section is for the classic, turn-based grid roguelike; for a real-time roguelite only the seed, run/profile and acceptance check rules apply; the discipline rules (camera, save, AI) are in their own files.

## Platformer
**Scope:** Jumping, gravity, air control and forgiving timings.

**Thresholds** (tile = one grid square)
| Setting | Start | Range |
|---|---|---|
| Full jump height | 3.5 tiles | 2–5 |
| Time to apex | 0.35 s | 0.25–0.45 |
| Short jump | 30% | what it applies to (speed or height) was not read in the source; choose by measuring |
| Gravity on the way down | 1.8x | 1.3–2.5 |
| Hang time at the apex | 0.5x gravity | |
| Coyote time | 0.1 s | 0.06–0.15 |
| Jump buffer | 0.1–0.15 s | |
| Air control | 0.65x of the ground | |
| Corner correction | up to half a tile | |
| Terminal speed | under half a tile per tick | |

**Method**
- Compute gravity and the initial velocity from the height (h) and the apex time (t), do not pick them by trial and error: `g = 2 * h / t^2`, `v0 = 2 * h / t` (our own derivation; in the source only the name of the calculator script appears).
- In the level the gap should be at least 1 tile shorter than the computed reach (`feel-camera-level.md` → Level design).

**Pitfalls**
- A variable `dt` shortens the apex height by about 5%; use a fixed tick.
- A floating-point (float) timer loses ticks; keep coyote and the buffer with a tick counter.
- If the coyote time is not reset on jumping, a second jump opens in the air.

**Verification**
- Write the position per tick to a CSV and compare with the computed curve; a row that deviates more than 5% fails.
- Write 4 edge case tests (the source's list was not read; e.g. the coyote limit, the buffer limit, hitting the ceiling, corner correction).

## Roguelike
**Scope:** Run structure, seed, turn system, field of view.

**Method**
- The run and the profile (permanent progress) are saved in separate files.
- A sub-seed per purpose from a single seed (`ai-generation.md` → Procedural generation).
- Energy scheduler: each actor gains energy equal to its speed per tick, an action costs 100 energy. Speed 50 is slow, 100 normal, 200 fast.
- Field of view (FOV) radius 6–9 and symmetric: if A sees B, B also sees A.
- Safe start: no enemy within 6–8 tiles of the start point.

**Pitfalls**
- If generation and combat use the same random stream, the same seed gives a different map. Python `hash()` is random per process.

**Verification**
- The same seed gives the same map hash.
- Acceptance check on 500+ seeds (connectivity, safe start, key order).

## RPG
**Scope:** Stats, modifiers, damage formula and balance.

**Method**
- Stat = base value + a stack of modifiers. Each modifier carries the identity of its source (item, spell); on removal the right one is deleted.
- Rounding is done only at the very end.
- Defense formula `damage * K / (K + defense)`: its effect diminishes as defense grows, and damage does not fall to zero.
- Resistance is at most 75%.

**Thresholds**
| Who dies | Number of hits |
|---|---|
| An ordinary enemy | 2–4 |
| The player | 5–8 |
| A boss | 25–60 |

**Verification**
- Produce a balance table per level; if the hit counts are outside the band, the row fails.
- Equip and unequip identity: equip the item, remove it; the stats should return exactly to the start.

## FPS
**Scope:** Weapon timing, time to kill (TTK), aim sensitivity.

**Method**
- TTK table: shots `ceil(health / damage)`, time `(shots - 1) / shots per second`.
- The fire timer is tied to the clock and independent of the frame rate. Mouse movement (delta) is not multiplied by `dt`; it is already the distance accumulated per frame.
- While aiming (ADS) the sensitivity ratio is `tan(ads_fov / 2) / tan(hip_fov / 2)`.

**Verification**
- Fire for 10 s at 30, 60 and 144 FPS: the number of shots should be `shots per second * 10` ±1.

## Tower defense
**Scope:** Wave growth, targeting, path.

**Method**
- Enemy health grows 1.12–1.18x per wave.
- Pressure is kept in the 0.6–0.95 range (the source's definition of pressure was not read; the definition should be written in the project).
- The default targeting is "first": the enemy furthest ahead on the path.
- If the player can build a maze, placement cannot cut the path completely; before placing, check that the path still exists.
- The wave timer runs on the game clock.

**Verification**
- Produce a table that computes the pressure of each wave; a wave that exceeds the band fails.

## Card
**Scope:** Zones, shuffling, trigger chain.

**Method**
- Every card is in exactly one zone at any time (deck, hand, graveyard, play area).
- A card being played waits in a separate holding zone (limbo) until it resolves.
- Shuffling uses Fisher-Yates and is seeded. A trigger chain is cut at 100 steps; an infinite loop does not lock the game.

**Verification**
- Play 10,000 bot rounds, check the invariants at every step (the card count is preserved, no card is in two zones).
- Shuffle 4 cards 24,000 times, apply a chi-square test to the distribution of orders.

## Visual novel
**Scope:** Branching, reading time, read text.

**Method**
- Draw the route map before the text: branches, merges, endings.
- For the time estimate, a reading speed of 200–250 words per minute.
- Line IDs should be stable; when the text is corrected, the read marker should not be lost. The read-text record is persistent data separate from the game save.

**Verification**
- Unreachable ending check: a breadth-first walk in Ink, lint in Ren'Py.

## Survival
**Scope:** Crafting, needs, decay.

**Method**
- Crafting first checks that the product fits in the inventory, then deducts the materials and adds the product in a single step.
- Needs such as hunger and thirst decrease on the game clock. In a merged stack, decay (spoilage, wear) is computed with a weighted average.
- Every item must be reachable from the start through a chain of recipes.

**Verification**
- Reachability check on the recipe graph: is there a path from the starting items to every item.

## Puzzle
**Scope:** State, move, solver, undo.

**Method**
- The rule is a pure function: `apply(state, move)` returns the new state and does not change the old one.
- Write the solver early; measure level difficulty with the solver.
- Undo stores a full snapshot, including the state of the random generator.

**Verification**
- The solver solves every level. After 1,000 undos the hash of the state is the same as at the start.
- In a matching puzzle, on 10,000 random boards there is no ready-made match at the start.
