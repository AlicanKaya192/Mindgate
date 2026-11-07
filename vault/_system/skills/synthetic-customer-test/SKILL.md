---
name: synthetic-customer-test
description: Use when testing a product or business idea, an offer, a price or a message on a panel of virtual customers (synthetic personas) before talking to real customers. Includes the questions "will this idea hold", "what will the customer object to", "which idea is stronger", "will they bear this price", and comparing ideas. The main chat (central agent) loads it.
---

Method skill (not an agent). Linked rules: #24 (no invention), #10 and #28 (agents), #27 (outside data), #3 (no personal data).

**The basic warning:** A synthetic customer is not evidence of demand. It only produces objections, weak points and hypotheses; language models drift toward the positive. Even if the report says "it will hold", the last step is a cheap test with real customers. The result is not presented as a percentage or a market share; numbers are written as "K of N personas".

## 1. Write the idea in a testable form
One card per idea: customer (role, company size, country), problem, today's solution, offer (one sentence), price, channel. If there is no card, write the card first; mark an unclear field as "assumption".

## 2. Build the personas from evidence
- Every persona rests on a piece of evidence: a store review, a community post, regulatory data, a research note. The note or URL of the evidence stays on the card; a field with no evidence is marked "assumption". A persona made up from a market description answers just as fluently but has nothing behind it.
- Fields: role, company (size, country, sector), the tool it uses today and its spending, the last concrete event it lived through, decision style, attitude.
- **An attitude mix is required:** Every panel has at least one skeptic, one "already uses the competitor" and one "has no budget or it is not a priority". A panel where everyone is keen is invalid.
- No real person's name, company name or contact information is used; the names are made up and clearly virtual.
- Panel check: no repeated role or country, the attitude mix is complete, every card has evidence or an "assumption" label. If something is missing, rebuild the panel.

## 3. Ask independently
- Every persona answers in a separate agent (`task-writing`; the model is written explicitly, default Haiku; at most 3 at the same time). A persona does not see the others, which idea we favour or the other ideas.
- Task text: the persona card, the idea card, the questions, "do not use tools, do not go to the web, do not write files", "you do not have to be polite; if it does not interest you, say so", the JSON answer format.
- **Question order (Mom Test style):** Past behaviour first, then the offer.
  1. When did you last have this problem, and what did you do?
  2. What does it cost you (time, money, penalty)? Whom do you pay what today?
  3. Have you tried to solve it before, and why did you stop?
  4. (The offer is shown) Your first reaction? Your biggest objection?
  5. What would you do at this price today: nothing / I'd look into it / I'd ask for a free pilot / I'd prepay?
  6. What is the one thing that would put you off? The one thing that would change your mind?
- JSON: `{"persona", "last_event", "cost", "current_solution", "first_reaction", "biggest_objection", "commitment": "none|will_look|pilot|prepayment", "purchase_1_5", "would_deter", "would_convince", "feeling"}`. Broken JSON is requested once more.

## 4. Resolve and decide
- A positive signal counts only if it rests on past behaviour or a commitment ("last event" concrete, "cost" measurable, commitment a pilot or prepayment). "Great idea" is not a signal.
- Decision rule (per panel):
  - **Strong:** More than half of the personas have a concrete last event and at least one says pilot or prepayment; the skeptic persona's objection can be solved by the product.
  - **Weak:** The problem is real but there is no commitment, or the objection is "the competitor already does it" and the difference is not clear.
  - **Will not hold:** Most have no concrete event, or the objection hits the core of the product (trust, liability, a free alternative).
- Group the objections, count the repeated ones, put one quote in each group (with the persona's name, short).

## 5. Suggest a real-world test
For each idea the cheapest real test: 5 real interviews (with whom, where to find them), a landing page and a waiting list, a pre-sale or a paid pilot offer. The success criterion is written beforehand (e.g. "3 pilots in 10 interviews").

## 6. Report
`research/YYYY-MM-DD-<topic>-synthetic-test.md`: method (model, number of personas, date), panel table (with an evidence column), a decision per idea with the reason, objection groups, the real-world test, limits. At the start of every idea a plain description that someone who does not know the field can follow (what, for whom, which pain, how the money comes, a representative example), and a glossary for the terms used in the report. Raw JSON goes to `_system/output/` (outside git). The agents used go to the agent log.

## Verify before finishing
- [ ] Every persona has evidence or an "assumption" label; the attitude mix is complete.
- [ ] The personas were questioned in separate agents; no task text has our preference or the other ideas.
- [ ] The decision was made by the criteria in the rule; numbers are in the "K of N" form.
- [ ] The top of the report has the "not evidence of demand" warning, and there is a real-world test for each idea.
- [ ] There is no real person or company name, no personal data.

## Idea sources
- takechanman1228/claude-persona (MIT; the github.com page was read on 29 October 2026, 60 stars): an isolated call per persona, an attitude mix, panel validation, a structured answer, the "only shows direction" warning. Its code, install script and `claude -p` sub-processes were not taken.
- phuryn/pm-skills (MIT, 27.5 thousand stars; page read): the idea of risky assumptions and experiment design. It has no synthetic-customer skill.
- Rob Fitzpatrick, "The Mom Test": ask about past behaviour, do not count compliments as a signal.

## Lessons
<!-- The central agent adds verified lessons here: general and reusable, without project names or dates. -->
- After a panel called an idea "strong", a search found that the target platform itself had released the same service at a very low price. Do the competition and platform scan BEFORE the panel; look especially at what came out in the last 6 months and at the platform's own products.
- The user could not understand the report because it used field-specific terms they did not know. A report is written assuming the reader does not know the field.
- Small-model personas give the "I'd look into it" answer a lot; in the decision rule "I'd look into it" must not count as a commitment, only a pilot and prepayment do (the rule is that way and must be kept).
