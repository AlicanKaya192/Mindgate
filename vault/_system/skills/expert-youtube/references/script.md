# Script and opening hook

Turning an idea into spoken text a viewer watches to the end.

## The first 15 seconds
The opening does three jobs. If one is missing, viewers leave early:
1. **Confirm the click:** Restate the title's promise in the first sentence, in different words.
2. **Open a question:** One question the viewer cannot close on their own.
3. **Show the answer exists:** The result, the screen or the proof is really in the video.

An opening that only does the third is a summary, not a hook.

## Flow
1. **Hook:** Write five openings, each with a different pattern (table below). Run all of them through `hook_check.py`. Show the user the two with the fewest missing features, with the tool output. Never offer a single option.
2. **Bridge (0:15–0:45):** Say what the video will do in one sentence and start doing it. No channel intro, no "before we start", no subscribe pitch here; they lose viewers early.
3. **Body:** One idea per section. Write an `[ON SCREEN: ...]` note for each section. With nothing to look at, the video becomes a podcast.
4. **Payoff:** Deliver what the hook promised, explicitly, and say that you are delivering it ("that's the template, it's in the description").
5. **Close:** One ask.

## What to hand back
- The two best hooks and their tool output
- The script section by section, each with `[ON SCREEN: ...]`
- A runtime estimate: word count ÷ words per minute (`thresholds.md`). The speaking rate for Turkish is not verified; ask the user for their own.
- One line: the winning hook's pattern and why it fits this idea

## What the tool looks at
| Feature | Present when | If missing |
|---|---|---|
| Specificity | A number or a name, and no vague adjective | Swap an adjective for a number, a name or a date |
| Address | In the first 6 words: you/your (Turkish: sen/siz, 2nd-person verb endings -sın/-sınız, negative imperative -mayın, or an imperative as the first word, "Bak,") | Speak to the viewer directly |
| Stakes | A loss or risk word and a number | Say what continuing costs them |
| Curiosity | A question word or a question mark, and the line does not answer itself | Cut the half that starts with "because" |
| Length | Turkish 7–20, English 9–24 words | Read it out loud and stop where your breath runs out |

Ranking follows the weakest feature. An opening strong in four features and missing one loses viewers at the missing one.

**Known limits:** In Turkish, a word like "kanalın" can be "your channel" or a genitive ("of the channel"); the tool does not count that ending as address on its own. Verb endings (-ıyorsun, -arsın, -amazsın) are only looked for in words of at least 7 letters, so "dersin" ("you say") is missed and "Bu dersin konusu" ("the topic of this lesson") is not taken for address. Third-person imperatives such as "göstersin" and proper nouns such as "Mersin" go on the exception list in `lang_tr.json`.

## Patterns
A pattern name is judged from the words only; it does not explain why a video was watched.

| Pattern | Shape | When it fails |
|---|---|---|
| Striking figure | An unknown number, then what it means | The source of the number cannot be named |
| Proven result | An outcome reached, then how | The result cannot be shown |
| Mistake warning | The mistake the viewer is making now | The mistake is rare |
| Contrarian turn | The advice everyone repeats, then why it is wrong | No evidence follows quickly |
| Open question | One question that cannot be answered alone | The answer is obvious or yes/no |
| I tried it | Something tried for a set time | It was not really tried |
| Clock is running | What is delivered within a time | The promise is not kept |
| Comparison | Two options side by side | The winner is obvious |
| Behind the scenes | A workings that is usually left out | It is common knowledge |
| Numbered list | How many items, best one last | The items are weak |
| Story opening | A specific moment: when, where | It does not meet the title within 15 seconds |
| Direct address | An "if you ..." situation | The situation is too general |

Full definitions and expressions: `scripts/hook_patterns.json`.
