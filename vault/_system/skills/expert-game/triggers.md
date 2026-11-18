# Trigger measurement: expert-game

Method: each request is read against the `description` text of the skills (`skill-writing` § Test, step 4). This measurement serves to correct the description; it does not prove loading in a real session.

| # | Request | Should trigger | Reason |
|---|---|---|---|
| 1 | In Godot my character sticks to the wall and `is_on_floor` always returns false | yes | Engine name and debugging in an engine |
| 2 | I am making a platformer with Phaser; can you suggest jump and gravity values | yes | Engine name and platformer genre |
| 3 | Should I use a behavior tree or a state machine for my enemy in Unity | yes | Enemy AI |
| 4 | My roguelike map comes out different every time with the same seed | yes | Genre and procedural generation |
| 5 | Add a save system to my pygame game, and the game must not crash when the save is corrupt | yes | Engine name and save system |
| 6 | I am joining a 48-hour game jam this weekend, how should I plan | yes | Game jam workflow |
| 7 | What should I check before uploading my game to itch.io | yes | itch.io release |
| 8 | Players are cheating to increase their money in my Roblox game, how do I prevent it | yes | Roblox; with expert-security alongside (in-game economy) |
| 9 | Draw an 8-frame sprite sheet for this fireball | no | Only a sprite request; not game development |
| 10 | Recolor the explosion effect with a blue palette | no | Recoloring an existing effect; not game development |
| 11 | Design a landing page for my game's promo site | no | expert-design: non-game page design |
| 12 | Write the contact form on my promo site in React, make it accessible | no | expert-frontend: non-game web interface |
| 13 | Set up the color and type system for a web dashboard that shows tournament results | no | expert-design: design system, not a game |
| 14 | I want to train an agent that plays Atari games with reinforcement learning | no | expert-ml: model training; no game is being made |
| 15 | Build a model that predicts the winner from chess match data, watch for leakage | no | expert-ml: data and model evaluation |
| 16 | Cluster player behavior data and extract player types | no | expert-ml: data science analysis |

Date: 2026-11-18

Result (central agent, reading against the description): 15/16 correct. 1–8 match the situations in the description; 9–10 are only effect and sprite requests and do not count as game development; 11–13, 15 and 16 do not involve game development. 14 is unclear: the word "game" is there, but the request is to train a model, not to make a game; the description does not exclude it explicitly. Loading in a real session was not measured. On the same day "For training an agent that plays games or analyzing game data use expert-ml" was added to the description; 14 is excluded by it (re-read: 16/16).
