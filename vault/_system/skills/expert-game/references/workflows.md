# Workflows: game jam, quick prototype, Steam, itch.io, game document

Numbers and store conditions are the declaration of the source pack's owner and were not independently verified. Store conditions may have changed; the user verifies details such as fees and durations on the store's own page.

## Game jam
**Scope:** Finishing and submitting the game in a timed competition.

**Method**
- Before the theme is announced, write the jam rules to `JAM.md`: duration, allowed ready-made assets, submission format, last hour.
- Vertical slice: finish a single playable loop from start to end, then expand.
- About the last 20% of the time is set aside for shipping: build, page, upload, trying it.
- For a 48-hour jam write an hour-by-hour schedule (the source's breakdown was not read; keep the 20% rule).

**Pitfalls**
- Uploading to itch.io is not a jam entry. The user makes the submission on the jam page.

**Verification**
- Before submitting, the user tries whether the game opens on a clean machine or in a browser.

## Quick prototype
**Scope:** Testing an idea in about 1 hour.

**Method**
- Before starting, write `BRIEF.md` with five fields:
  - QUESTION: the single question being tested.
  - VERB: the player's main action.
  - KEEP IF: what must be seen to keep the idea.
  - KILL IF: what is enough to drop the idea.
  - RESULT: filled in after playing.
- Gray box: no graphics, no sound, no menu; only the verb.
- The agent does not judge fun. The user plays and the user writes the RESULT.
- A "keep" decision is permission for a clean rewrite and the user makes this decision; the prototype code is not carried into the product.

## Steam
**Scope:** Uploading the build to Steam and release preparation.

**Method**
- Uploading is done with the user's explicit permission; if `steamcmd` is not installed, say what is needed and why, and ask permission (#35). The build goes to a beta branch first; the user opens the `default` branch themselves.
- Before uploading, see what will go with a Preview (dry run).
- According to the source's declaration: an app fee of 100 USD, a "Coming Soon" page for at least 2 weeks before release.
- Steam credentials are not written to a file, a script or a log.

**Pitfalls**
- In Unity, LZ4HC compression enlarges the Steam patch (`engine-unity.md`).

## itch.io
**Scope:** Uploading with butler and HTML5 limits.

**Method**
- Use a separate channel for each platform (e.g. Windows, Linux, web separately).
- `--dry-run` before the real upload; the real `butler push` is done with the user's explicit permission. If `butler` is not installed, say what is needed and why, and ask permission (#35).
- `BUTLER_API_KEY` is not written to a file, a commit or a log.

**Thresholds**
| Limit | Value |
|---|---|
| HTML5 file count | 1,000 |
| HTML5 total size | 500 MB |
| Single file | 200 MB |

**Pitfalls**
- If the Godot web build uses threads, the server needs COOP/COEP headers (`engine-godot.md`).

**Verification**
- In the dry run output the file count and size are under the limits.
- Publishing the page is the user's job.

## Game document
**Scope:** The design document (GDD) and the feature note.

**Method**
- A one-page GDD for the game; a separate short feature note for each feature.
- The source wants "six states" to be covered; the list of states was not read. In a feature note write at least the normal flow, the error and the empty states.
- Ask the user at most one round of questions; mark what stays unanswered as an assumption and write it (`[ASSUMPTION]` in the source).

**Verification**
- Every assumption is marked; the document is clear enough for someone who does not know the context to read and implement it.
