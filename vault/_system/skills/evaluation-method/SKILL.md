---
name: evaluation-method
description: Use when scoring and comparing the output of an LLM or an agent, a prompt or skill change, two options (A/B) or the result of an ML model. Includes agent-team decisions, skill tests and evaluation in ML projects. Preloaded into the evaluator agent; the main chat loads it, the reviewer may load it.
---

Method skill (not an agent). Used together with `expert-ml` for ML metrics.

## 1. Machine check first
Check with a command everything that a command can decide: do the tests pass, is the schema valid, does the file exist, does the number match. Only the part a command cannot decide is left to a judge (human or model).

## 2. Choose a method
- **If there is a correct answer** (factual accuracy, following instructions, format): **direct scoring.** Write the criteria, the weight of each criterion and the definition of each score level (1–5 is the most balanced).
- **If it is a matter of taste or preference** (style, readability, design): **pairwise comparison (A/B).**

## 3. Reduce biases
| Bias | What happens | Remedy |
|---|---|---|
| Position | The option in first place is favored | Run the comparison twice, swap the order. If results conflict, call it a "tie" with low confidence |
| Length and detail | A long answer is thought better | Say "do not reward length"; let needless detail be penalized in the criteria |
| Self-preference | A model likes its own output | Let the producer and the evaluator differ (e.g. a reviewer with fresh context) |
| Authority | A confident tone is taken as correct | Ask for evidence (quote, file:line, command output) **before** every score |
| Consensus | Agents agreeing is taken as evidence | The same model can share the same error; keep at least one check outside the loop |

## 4. Rubric (scoring scale)
- Write the boundary and observable features of each score level, and leave notes for ambiguous cases.
- Strictness is chosen deliberately: lenient for trials, strict for releases and security.
- The score distribution is not one generic rubric but written in terms specific to the subject (names and functions for code, metrics and data splits for ML).

## 5. Choosing metrics
| Task | Main metric |
|---|---|
| Pass/fail | Precision, recall, F1 |
| Ordinal score (1–5) | Spearman or Kendall rank correlation |
| A/B preference | Agreement rate, order consistency |
| Agreement between two evaluators | Cohen's kappa |

Look at **systematic** disagreement rather than random error: a judge that always disagrees on one particular criterion is more dangerous.

## 6. Measuring a skill or prompt change
1. Pick 2–3 realistic tasks (of the kind the user really gives).
2. Run each task **with the skill** and **without it** (or with the old version).
3. Compare the results with the source hidden (blind A/B; swap the order).
4. Mark expectations pass/fail with evidence. Criticize weak expectations too: an expectation that always passes measures nothing.
5. Do not trust a single run; the same prompt can give different results.

This is a measurement job: it consumes usage allowance. Ask the user before a large trial.

## Report
| Criterion | Score or winner | Evidence | Confidence |
|---|---|---|---|

Add "machine checks" and "what could not be evaluated and why" sections at the end.

## Idea sources
- muratcankoylan/Agent-Skills-for-Context-Engineering `advanced-evaluation` and `evaluation` (MIT).
- anthropics/skills `skill-creator` (Apache-2.0): comparison with and without a skill, the idea of a blind comparator and a grading agent.

All were read from downloaded copies; their match with the official repositories was not verified.

## Lessons
<!-- The central agent adds verified lessons here: general and reusable, without project names or dates. -->
