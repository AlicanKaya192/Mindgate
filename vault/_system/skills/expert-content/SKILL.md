---
name: expert-content
description: Personal technical content writing expertise pack. Load when writing or editing, in the user's voice, a blog post, a LinkedIn post, a GitHub README or a portfolio page text; when choosing topics for the publishing pipeline (drafts); or when removing AI traces from a text. Not for sales and marketing copy.
---

Expertise pack (not an agent). The publishing pipeline rules come first: §7.9 of the vault `CLAUDE.md` and `_templates/draft.md`.
- The text is written in the user's voice, in the first person singular. It carries no AI signature or trace (#14).
- Claude publishes, shares or schedules nothing. The text belongs to the user: Claude proposes, the user decides.

## Before writing
1. **Who is the reader?** Student, ML engineer, recruiter… What is the reader's problem, in which words do they describe it?
2. **One message:** What will the reader take away from this piece? Write it in one sentence ("One-sentence message" in the draft template).
3. **What is new?** Write in one sentence what similar posts do not have. This is usually the user's own experience: a measurement, an error, a fix. If you cannot write it, the topic is not ready yet.
4. **Evidence:** What is in the vault? Problem notes (`problems`), experiment notes, progress logs, command outputs, measurement tables. Numbers are taken only from these notes.
5. **The one thing asked of the reader:** to try it, to review the code, to write a comment.

## Writing principles
- Clarity comes first, cleverness later. Simple words, active voice, definite statements.
- Describe the gain, not the feature: what will the reader learn, what will they be able to do?
- **Concreteness:** Write a measure instead of a vague phrase. Not "it got faster" but "training time dropped from 40 minutes to 12 minutes". The number comes from a vault note.
- **Every claim has evidence.** If there is none, soften the claim or remove it. Mark missing evidence in the draft as `[EVIDENCE NEEDED: …]`. No invented numbers or sources (#24).
- The opening starts with the reader's problem or the result reached. Not with "Hello, today I'll show you…" or a long backstory.
- A paragraph is 2–4 sentences; each section carries one idea. Read the text aloud and fix where you stumble.
- The reader's own words and the error message can be used verbatim (e.g. `CUDA out of memory`).
- Emotion serves the message. Sales patterns such as urgency, scarcity and fear of missing out are not used.

## AI traces: do not write these
- Opening with a contrast: "Not X, but Y". State Y directly with its reason.
- Lists of negations: "No X, no Y, no Z". Say what there is.
- Finishing a sentence and then stretching it with a comma and an add-on.
- Answering your own question ("The result? 3x speed.") or explaining the outcome with a colon.
- Ready-made openings: "In today's fast-changing world", "Here's the thing", "X, reimagined", "Unlock the power of …".
- Empty words: "flawless", "powerful", "revolutionary", "seamless", "take it to the next level". Write the fact instead.
- No em dash (—) in posts. Use a period or a line break.
- One sentence per line ("broetry"), emoji at the start of a line, engagement traps ("Do you agree?", "Read that again").
- Saying "to be honest, I was terrified" when there is no real story. Write it if there is a real experience, otherwise do not.
- At most one triple list and one sentence fragment per section.

Swapping words produces a new trace. Rewrite the problem sentence starting from the fact.

## Editing: seven passes
Look at only one thing in each pass. Mark the problems first, then fix.
1. **Clarity:** Does the reader understand every sentence on first reading?
2. **Voice:** Do "I" and "we" get mixed? Is the tone like the user's from start to end?
3. **"So what?":** After every claim, is there an answer to "why does this matter to this reader?"
4. **Evidence:** Does every claim have a source or a measurement?
5. **Concreteness:** Were vague words turned into measures?
6. **Emotion:** Does emotion serve the message, or is it exaggeration?
7. **Objections:** Are the "but…" questions that will occur to the reader answered?

Final check: the list in the draft template. No secrets (#18), no AI traces, numbers consistent with the notes, links working.

## By platform
- **Technical blog:** Problem → what was tried → solution → result → lessons (case structure). Use code snippets, measurement tables and error output.
  - Subheadings should be understandable on their own.
  - The publish and update dates should be visible.
  - Link to the primary source.
- **LinkedIn:**
  - **Hook:** A real fact, number or story in the first line.
  - **Body:** Normal paragraphs; no more than one list.
  - **Close:** A concluding sentence, or a single question whose answer you genuinely want to know.
  - Putting the link in the first comment rather than in the body is the source's recommendation.
  - Documenting a learning journey is a fitting pattern for someone who is learning.
- **README / portfolio:**
  - First paragraph: what the project does, whose work it helps.
  - Then: how to run it (commands), results and measurements, architecture in brief, limits.
  - No "generated with AI" notice (#14).

## Topic selection (the idea pool of the publishing pipeline)
- Sources: solved problems, measured experiment results, finished project stages, notes on current projects.
- Two kinds of content:
  - **Searchable:** how-to, error fix.
  - **Shareable:** experience, opinion, lesson learned.
- **Topic clusters:** 3–5 main areas (e.g. ML, LLM agents, Python tools). Every post is tied to one cluster.
- **Priority:** How many times was this problem met? Is there evidence at hand? How well does it fit the user's goals (see `me/profile.md`)?
- Candidates are written to the "Idea pool" on the [[drafts]] page. If the user chooses one, the draft is written to `drafts/`.

## Quality (experience, expertise, trust)
- **Experience is shown:** own code, measurement, error and fix.
- **Expertise:** Claims are correct and sourced; technical depth suits the reader.
- **Trust:** date, correction note, primary source.
- **Thin-content signs:** generic statements, no original insight, every section in the same pattern, wrong information.
- No word-count target is set; write as much as the topic requires.

## Idea sources
- coreyhaines31/marketingskills (MIT, Corey Haines): `copywriting`, `copy-editing` (seven passes), `content-strategy`, `social`.
- agricidaniel/claude-seo (MIT): `seo-content` (experience, expertise, trust).

Both were read from downloaded copies on 13 October 2026; their match with the official repositories was not verified. The following were not adopted:
- sales patterns, cold outreach
- automatic sharing and scheduling tools, paid tools
- scraping recipes
- scripts that hide traces
- unverified statistics

## Lessons
<!-- The central agent adds verified lessons here: general and reusable, without project names or dates. -->
