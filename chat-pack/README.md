# Chat app pack

**Gates, automatic records and scripts do not work in chat apps.** This pack lets you use the Mindgate rules and note format in ChatGPT, Gemini and similar chat apps. There the rules are only written instructions: nothing blocks a harmful command, nothing scans for secrets, and nothing is saved to your vault on its own.

## What is in the pack
| File | What to do with it |
|---|---|
| `instructions-short.txt` | Paste it where the app allows a short instruction (up to 1,500 characters). |
| `instructions-long.txt` | Paste it where the app allows a longer one (up to 5,000 characters), such as the instructions of a project or of a custom assistant. Use one of the two texts, not both. |
| `rules.md`, `schema.md`, `templates.md` | Upload them as knowledge files to the same project or assistant. |

Menu names and limits change between app versions and plans, so this guide does not name menus. If the long text does not fit, use the short one.

## Building the pack
From the `setup/` folder:

```
py -3 -I chat_pack.py --language en --out <new folder>
```

The folder must be new or empty. `--language tr` builds the Turkish pack. The builder secret-scans every file first and writes nothing if it finds one.

## Saving notes by hand
1. When the app offers a note, read it: is it right, is there anything private in it?
2. In Obsidian, create the file at the path the app gave (for example under `inbox/`) and paste the note.
3. A log line goes at the end of `log.md`; a pending item goes at the end of `inbox/pending.md`.
4. If you also use Mindgate with Claude Code, you can ask it later to add the new notes to the index and check their links.

## What does not work here
| Mindgate part | In chat apps |
|---|---|
| Command, write and site guards | None. The app may suggest a harmful command; you decide whether to run it. |
| Secret scan | None. Check notes yourself before saving. |
| Session records, handoff cards, context check | None. |
| Scripts (search, health, graph) | None. The app cannot read your vault. |
| Skills and agents | Not installed. |
