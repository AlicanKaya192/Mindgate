---
type: council
status: active
mode: {{mode}}
agents: []
result: {{passed | conditional | failed | running}}
calls: {{count}}
opus: {{count}}
project: "[[{{project}}]]"
decision_note: "[[{{decision-note}}]]"
tags: [council]
created: {{date}}
updated: {{date}}
---

# Council: {{task}}

> Thin note: the real text of the decision is not here, it is in the note [[{{decision-note}}]]. This note only keeps the trace of the council ([[councils]]).

## Summary
One sentence: what the council was formed for, and the result.

## Conflicts and the user's decision
- Topic · the strongest argument of each side (one line) · the user's decision

## Acceptance criteria
- [ ] Criterion · met / not met · evidence

## Cost and measurement
- Calls: {{count}} ({{Opus}} Opus, {{Sonnet}} Sonnet, {{Haiku}} Haiku) · Is it a blind comparison task: yes / no
- Number of problems the council caught and that were fixed before code or decision: {{count}}

## Raw reports
`_system/output/council/{{date-task}}/` (outside git, stays in place)
