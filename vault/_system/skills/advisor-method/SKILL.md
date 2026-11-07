---
name: advisor-method
description: Method for judging a piece of work with a balanced eye at the start and at the end: is the direction and scope right, what is missing, wrong or should not be there, was the goal reached. Preloaded into the advisor agent; the main chat can also load it when asked "comment on this", "are we on the right track" or "is it done, what is missing".
---

Method skill (not an agent). Related rules: #23, #24, #26.

## At the start
1. **The actual request:** Restate the user's words in one sentence. Does the task card match it?
2. **Direction:** Does this path meet the request? Is there something that must come first?
3. **Scope:** Is there too much (unrequested work, #23) or too little?
4. **Rules and earlier decisions:** Does it conflict with the project's rules and ADRs (#26)?
5. Look at the observations from four angles: **skeptic** (is this finding really true), **builder** (what is the concrete fix), **integrity** (mismatches between files and steps), **end user** (what does the person using this experience).

## Round 2
- Read the hater's report. Accept where it is right; say, with reasons, where it overreaches.
- Propose a path that answers both concerns. If disagreement remains, write the strongest argument of each side and leave the decision to the central agent.

## At the close
- For each acceptance criterion: met / not met, with evidence.
- Order the remaining findings by importance: **breaks** (what exactly breaks, and for whom), **costs** (time, money, usage allowance), **decays over time** (maintenance, consistency).
- Decision recommendation: ready / ready with a fix (which fix) / not ready.
- The single next step.

## Principles
- Few but correct findings: every item has evidence; do not invent findings to fill space. If there are none, say "no findings".
- Write what is going well too; criticism alone is not a balanced comment.
- You do not decide; you write a recommendation.

## Verify before finishing
- [ ] The actual-request sentence was written and compared with the task.
- [ ] Every finding has evidence and a recommendation.
- [ ] At the close, every acceptance criterion was marked one by one.

## Idea sources
- VoltAgent/awesome-claude-code-subagents `surgeon-reviewer` (MIT, per the repository page): three severity levels, the "what concretely breaks" gate question, three-way decision, few but correct findings.
- VoltAgent/awesome-claude-code-subagents `ponder-auditor` (MIT): four angles (skeptic, builder, integrity, end user). Having no round limit was not adopted.
- The two-ended structure (judging at the start and at the end): not found in open source, our own design.
Read from the web on 6 November 2026; no text or code copied.

## Lessons
<!-- The central agent adds verified lessons here: general and reusable, without project names or dates. -->
