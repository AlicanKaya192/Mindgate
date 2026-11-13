# Edit decision list and Shorts

## Edit decision list
`dead_air.py` reads a timestamped transcript and lists the places to cut: dead air, filler and retakes. It does not touch the video; the user makes the cuts in their own editor.

```bash
py -3 -I scripts/dead_air.py recording.srt --floor 0.6
```

If there is no transcript, ask for one. The automatic captions of a video uploaded to YouTube as unlisted can be downloaded from Studio. Do not guess timings.

| Kind | What | Note |
|---|---|---|
| DEAD | Silence longer than `--floor` seconds | Cut from the middle, keeping a 0.15 s breath on each side; cutting flush against speech sounds breathless |
| FILLER | A cue made only of filler words ("um", "uh", Turkish "eee", "yani") | A sentence such as "So this method works" is not cut |
| REPEAT | A restarted sentence | When the previous speech cue matches the start of the next one and there is a pause between them, the first attempt is cut; an "um" in between does not count. Rolling caption cues that touch end to end are not counted |

**Careful:** The shortening percentage is measured on speech time only. If the video has a long silent demo, the real runtime differs. Do not trust the runtime before checking it against the footage.

**Known limits:** Whether automatic captions write out "um" or Turkish "eee" was not verified; if they do not, filler shows up only as a pause. The real format of YouTube's own VTT files was not verified either. A file saved as UTF-16 (Notepad's "Unicode") is not read; the tool says so, save it as UTF-8.

## Shorts
A Short cut from a long video is not a clip of the best moment. It is a moment that **makes sense without the rest of the video**, which is a much smaller set.

Look for 20–55 second spans in the transcript. All three must hold:
1. It opens on a complete thought; the first sentence does not need the previous minute.
2. There is a turning point in it: a claim, and something that complicates or proves it.
3. It ends on a sentence, not a trail-off.

Rank the candidates; show the first five with timestamp and first sentence so the user can reject one without reading the transcript. For each, write:
- **A new first line:** The long video's sentence needs context. Write a new one and run it through `hook_check.py`.
- **On-screen text for the first 2 seconds:** different words from the spoken line.
- **A loop point:** build the last line so it leads back into the first line when the video replays.
- **A vertical framing note:** what is cropped out of a 16:9 frame, and does it matter?
