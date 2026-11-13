# Chapters and search text

## Chapters
YouTube's rules (`thresholds.md`, official): the first timestamp is 00:00, at least 3 timestamps in ascending order, each chapter at least 10 seconds. If one is broken, the list stays in the description but is not shown as chapters.

```bash
py -3 -I scripts/chapters.py recording.srt --target 6       # suggest
py -3 -I scripts/chapters.py --check list.txt --duration 612
```

- The tool finds chapter boundaries from the pauses in the transcript and how much the words change on either side.
- The titles it suggests are topic words, so they are drafts. Rewrite each as the promise of that section, in the user's voice, in 3–5 words.
- `--check` checks a list the user wrote. Lines without a timestamp (the rest of the description) are skipped and listed; they do not make the list invalid. With `--duration` the length of the last chapter is checked too.
- Chapters are also a retention check: a section that cannot be named in five words is either two sections or filler.

## Search: description and tags
Search is a small factor for a video aimed at the subscriber feed. It matters more for topics people keep searching for. If the video is for the subscriber feed, say so and spend the effort on the title and thumbnail (`packaging.md`).

**Description** (at most 5,000 characters, official):
1. The first two lines: the only part shown above "more"; search results usually show this part too (observation). Say what the video gives, in the words a person would search with.
2. The link or resource, if there is one, right after, before the fold.
3. Chapters.
4. The long version: what is covered, who it is for, what it assumes.

**Tags:** According to YouTube they play a minimal role in discovery and help mainly with words that are often misspelled (official). Use them for spelling variants, tool names and abbreviations; do not add tags unrelated to the topic.

**Query test:** Before handing over, write the three search queries this video should win. Check that the title and the first two lines of the description contain their words. If they do not, the problem is the title, not the description.
