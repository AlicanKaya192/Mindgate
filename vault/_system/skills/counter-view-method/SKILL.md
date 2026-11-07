---
name: counter-view-method
description: Method for deliberately reading a plan, a decision or a delivered piece of work from the opposite side: pre-mortem, the strongest counter-argument, kill criteria. Preloaded into the hater agent; the main chat can also load it when asked "look at why this could fail", "play devil's advocate" or "give a counter view".
---

Method skill (not an agent). Related rules: #23, #24, #27.

## Round 1 (blind)
1. **Write the thesis in one sentence:** What will this work achieve, for whom, by what measure?
2. **Pre-mortem:** Assume "six months from now this work failed" and work backwards. Produce the 3–5 most likely failure stories.
3. In each story write the **hidden assumption** (something we believe without checking) and 1–2 **observable early warning signs**.
4. Turn the strongest warning sign into a **kill criterion**: measurable, dated or tied to a stage ("if a 200 MB file does not open in 3 seconds, the architecture is rethought").
5. **Objections:** At most 5. Each one: evidence, importance (high / medium / low), proposed answer or mitigation, "what would make me give up this objection".
6. Do not write suspicion without evidence as an objection; list it separately as an "open question".

## Round 2
- Read the reports you were given. Name the view you disagree with most and write, with evidence, why you disagree.
- Withdraw the objection you were convinced of, and say so openly. The aim is not to win but to find the right decision.
- Label each remaining disagreement: **evidence gap** (which check resolves it) or **judgment call** (the user chooses).

## Close
- Was the kill criterion met? Answer yes or no with evidence.
- **The strongest unanswered objection:** one sentence. If none, write "none".
- Decision recommendation: pass / conditional pass (which condition) / fail.

## Limits
- The scope is decision and direction; line-by-line code review, security scanning and vault defense testing are the work of other agents.
- Do not reopen a decision the user gave beforehand; if you see a conflict, leave a one-line note.
- No endless objections: at most two rounds and a close.

## Verify before finishing
- [ ] Every objection has evidence and a condition for giving it up.
- [ ] The kill criterion is measurable.
- [ ] Objections withdrawn in Round 2 are written down openly.

## Idea sources
- vishalsachdev/claude-skills `premortem` (repository MIT): failure story told backwards, hidden assumption, early warning sign. Turning the early warning into a kill criterion is our addition.
- AmrAnwar/objection (MIT): the strongest unanswered objection at the close, pass/fail decision. The unlimited objection loop was not adopted.
- mattpocock/skills `grilling` (MIT): asking questions from the open ends of the decision, adding a proposed answer to each question. Unlimited questioning was not adopted.
- boshu2/agentops `council`: separating a disagreement into "evidence gap" and "judgment call".
Read from the web on 6 November 2026; no text or code copied.

## Lessons
<!-- The central agent adds verified lessons here: general and reusable, without project names or dates. -->
