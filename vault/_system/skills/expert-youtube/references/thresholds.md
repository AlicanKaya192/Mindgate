# Thresholds and their sources

The official ones were read from YouTube Help (13 November 2026). The rest are heuristics; they were not validated against channel data. If a threshold changes, update this table first, then the constant in the script.

| Threshold | Value | Where | Source | Status |
|---|---|---|---|---|
| Title length | at most 100 characters | `title_check.py` `YOUTUBE_TITLE_LIMIT` | YouTube Help, "Edit video settings" (support.google.com/youtube/answer/57404) | Official |
| Description length | at most 5,000 characters | `chapters-search.md` | Same page | Official |
| Effect of tags | minimal role in discovery | `chapters-search.md` | Same page | Official |
| Chapter rules | first 00:00; at least 3, ascending; each at least 10 s | `chapters.py` | YouTube Help, "Video Chapters" (support.google.com/youtube/answer/9884579) | Official |
| Cut in search | 60 characters | `title_check.py` `SEARCH_CUT` | Observation in the original pack (Idea sources) | Not verified |
| Cut in the mobile feed | 40 characters | `title_check.py` `MOBILE_CUT` | Observation in the original pack (Idea sources) | Not verified |
| ALL CAPS words | at most 2 (4+ letters) | `title_check.py` | Method | Heuristic |
| Thumbnail text | at most 3 words | `title_check.py` | Method | Heuristic |
| Hook length (English) | 9–24 words | `lang_en.json` `hook_words` | Original pack: ~10 s at ~150 words/min | Not verified |
| Hook length (Turkish) | 7–20 words | `lang_tr.json` `hook_words` | Shortened for an agglutinative language (Turkish) | Not verified |
| Address window | first 6 words | `hook_check.py` `ADDRESS_WINDOW` | Method | Heuristic |
| Speaking rate | ~150 words/min (English) | `script.md` runtime estimate | Common estimate | Unknown for Turkish; ask the user |
| Dead air | 0.6 s, with 0.15 s breath each side | `dead_air.py` | This pack's default | Tune per speaker |
| Short length | 20–55 s | `editing.md` | Method | Heuristic |
| Opening loss | first 30 s | `channel.md` | Method | Heuristic; no "healthy" rate is given |
| Videos for a median | at least 4 per channel | `channel.md` | Method | Heuristic |
| Weekly uploads | 1 anchor + 1 light + 3 Shorts | `channel.md` | Method | Heuristic |
