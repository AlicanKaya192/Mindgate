# Title and thumbnail

The title and the thumbnail are one unit. Written separately, the thumbnail often repeats the title and half of the click surface says the same thing twice.

## Flow
1. Write ten titles. Put them in a file and check them with `title_check.py file.txt`; the tool sorts them, fewest issues first.
2. Show the best three with the tool output, and name the single issue of each.
3. For the winning title, write a thumbnail brief:
   - text of at most 3 words (not repeating the title's words)
   - facial expression and framing
   - how the background keeps contrast at feed size
4. Check the title and thumbnail text together: `title_check.py --title "..." --thumb "..."`.

## Rules and why
| Rule | Why | Source |
|---|---|---|
| At most 100 characters | YouTube does not accept a longer title | Official (`thresholds.md`) |
| Past 60 characters it may be cut in search, past 40 in the mobile feed | On desktop the tail goes, on mobile the subject can go | Observation, not official |
| The thumbnail does not repeat the title | Same promise, different words | Method |
| At most 3 words on the thumbnail | At feed size a fourth word cannot be read | Method |
| A number, a name or a date | Says more than any adjective | Method |
| At most 2 words in ALL CAPS | More reads as spam; 3-letter acronyms (SQL, API) do not count | Method |

**Note on word matching:** The tool counts two words as the same when one starts with the other ("thumbnail" and "thumbnails", Turkish "kanal" and "kanalı"), or when only a softened last consonant differs (Turkish "kitap" and "kitabı"; p/b, ç/c, t/d, k/ğ). Look-alikes such as "model" and "modern" are not counted. The result is a warning; the decision is the user's.
