# Game AI, behavior tree and utility, procedural generation

Numbers are the declaration of the source pack's owner and were not independently verified. Every threshold is a starting point: measure, play, tune.

## Game AI
**Scope:** The perception, decision, pathfinding and movement of an enemy or NPC.

**Method**
- Keep five layers apart: perceive, decide, find a path, steer, animate. Animation does not decide; the decision layer does not draw.
- Pick the decision structure from simple to complex:
  - Finite state machine (FSM): if 2–6 states are enough, this.
  - Behavior tree (BT): when states multiply and transitions get tangled.
  - Utility: when you need to choose among a few options by scoring.
  - GOAP (goal-oriented action planning): last resort.
- Run perception at 5–10 Hz, not every frame. Offset the agents' ticks; they should not all think in the same frame.
- Hysteresis: start chasing at a distance of 10 units, give up at 14. Stay in a state for at least 0.3–0.5 s. Let the reaction delay be 0.2–0.5 s; an instant reaction looks inhuman.
- If there is no approach to the target for 2 s, ask for the path again.
- On an eight-direction grid use the octile heuristic.
- Visible intent: give a warning (telegraph) before an attack so the player can react.

**Pitfalls**
- Without hysteresis the enemy goes in and out at the boundary and flickers.
- A misspelled state or key name gives no error in most engines; it silently does not work.

**Verification**
- With the heuristic at 0, A* should give the same path cost as Dijkstra. Compare on 50 different grids.
- Count state transitions: more than 2 transitions per second shows missing hysteresis.

## Behavior tree and utility
**Scope:** Building a decision structure with BT and utility.

**Method**
- On the outside the BT builds the structure (patrol, combat, flee); on the inside utility makes the choice (which attack, which target).
- Define the Blackboard first: key names and types. Nodes write to and read from the Blackboard, not from each other.
- Use a reactive Sequence: the condition is rechecked on every tick.
- Utility:
  - Each criterion is turned into a 0 to 1 range by a curve.
  - Criteria are multiplied; if one is 0 the action is eliminated (veto).
  - Add an inertia margin of 0.05 to the selected action; when scores are close, the choice should not change on every tick.
- A decision tick of 5–15 Hz is enough.

**Pitfalls**
- A Sequence with memory continues from the middle node even if the condition breaks: an enemy chases a player who left its sight forever.
- If a timed node (wait, cooldown) is not reset when interrupted, it continues with the old counter on the next entry.
- Allocating memory inside a tick (a new list, a new object) drops the frame rate with many agents.

**Verification**
- For each branch, change the condition on purpose and see with a test that the tree moves to the right branch.
- Engine-specific: the `Observer Aborts` setting in Unreal (`engine-unreal.md`).

## Procedural generation
**Scope:** Generating a map, rooms, loot and enemy placement from a seed.

**Method**
- One main seed; a sub-seed derived from it for each purpose (map, enemy, loot separately).
- Carry your own pseudo-random generator (PRNG) (e.g. SplitMix64); the same seed should give the same result in every environment.
- Generate plain data first (grid, room list), and build the scene from this data afterwards.
- Validate every result and reject what fails:
  - Is every room connected, by flood fill.
  - Is the spawn point safe.
  - Is the key reachable before its door.

**Thresholds**
- 0 failures on at least 200 seeds. For a roguelike 500+ seeds (`genres.md`).

**Pitfalls**
- Perlin noise gives 0 at integer coordinates; scale or shift the input.
- Wave function collapse (WFC) gives contradictions if the rules are not symmetric (A can go next to B but B cannot go next to A).
- If generation and combat share the same random stream, the player's move changes the next map.
- In Python `hash()` is randomized per process; do not use it to derive seeds.

**Verification**
- Generate the same seed twice; the hash of the output should be the same.
- Generate 200+ seeds headless, each passes the validators; even a single failure is a failure.
