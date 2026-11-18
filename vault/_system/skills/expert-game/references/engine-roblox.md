# Roblox

Behavior information is the declaration of the source pack's owner of 11 November 2026 and was not independently verified. For the economy and server validation, use `expert-security` alongside.

## Luau basics
- Get services with `game:GetService(...)`.
- Set the properties of a new object first and assign `Parent` last.
- Store an event connection (Connection) in a variable and disconnect it when done.

## DataStore
- If loading failed, refuse to save in that session; otherwise empty data is written over the player's save.
- Use `UpdateAsync` and a session lock instead of `SetAsync`; two servers should not overwrite the same record.
- Wrap every DataStore call in `pcall`.
- In `BindToClose` there are 30 s to save.
- Do not save a NaN or infinite value.

## Network
- The client sends only an identity and an intent ("I want to buy this item"), not the result.
- The server validates in layers: request rate, type, the number being finite, permission, distance, cooldown.
- Do not use `InvokeClient`.

## Character and physics
- When the character respawns, increase a generation counter. After every yield, check that the character in hand is still the current generation.
- For a collision query use a shapecast; network ownership of moving parts belongs to the server.

## Studio workflow
- Edit the source of truth: if the project is kept with files (Rojo), the files; otherwise the instance in Studio.
- The source uses a 6-step verification ladder (the steps were not read); the general ladder is SKILL.md §4.
- The report is written with the distinction "ran / checked statically / prepared but not run / not verified".
- Clean up the objects and experiments placed for testing when the work is done (ask the user before deleting, #22).

## Economy
- Cost growth multiplier (`costGrowth`) 1.07–1.15.
- Do not save or display a NaN or infinite value.
- In abbreviated number format, test the limit: 999950 should be shown as "1.0M".
- The source has balance and economy scripts written in pure Luau; they were not read.
