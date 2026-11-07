# Notice

Mindgate is released under the MIT License (see [`LICENSE`](LICENSE)).

Several skills and agents took ideas from the sources below. No text or code was copied from them: the ideas were adapted and written in our own words, under the vault's rules. Licenses are given as the skill files record them; "per the repository page" means the license was read from the repository page, not from its LICENSE file. Where no license is given, the skill file does not record one.

Each skill and agent keeps its own list in an "Idea sources" section (`Fikir kaynakları` in the Turkish files).

## Design patterns

| Source | Where |
|---|---|
| Karpathy's "LLM Wiki" pattern, PARA, atomic notes | vault schema (`vault/CLAUDE.md`, `schema-details.md`) |
| Memento-Skills: the idea of rewriting a skill that keeps failing, with human approval | skills registry (`skills-registry.md`) |

## Repositories and skills

| Source | License | Used in |
|---|---|---|
| anthropics/skills: `skill-creator` and its grader, comparator and analyzer agents | Apache-2.0 | `evaluator` agent, `evaluation-method`, `skill-writing` |
| anthropics/skills: `webapp-testing` | Apache-2.0 | `test-writing`, `expert-frontend` |
| anthropics/skills: `doc-coauthoring` | Apache-2.0 (repository) | `expert-writing` |
| anthropics/skills: `frontend-design` | not recorded | `expert-design` |
| anthropics/knowledge-work-plugins: `design/skills/ux-copy` | Apache-2.0 (repository) | `expert-writing` |
| anthropics/claude-code plugins: `code-review`, `pr-review-toolkit`, `feature-dev` | not recorded | `review-method`, `scouting-method`, `expert-backend` |
| anthropics/claude-code-security-review | not recorded | `review-method`, `expert-security` |
| obra/superpowers (Jesse Vincent): `systematic-debugging`, `test-driven-development`, `verification-before-completion`, `writing-skills`, `writing-plans`, `dispatching-parallel-agents`, `receiving-code-review`, `requesting-code-review`, `brainstorming` | MIT | `debugging`, `test-writing`, `verification`, `skill-writing`, `task-writing`, `review-method`, `obsidian-writing`, `expert-architecture`, `expert-backend` |
| muratcankoylan/Agent-Skills-for-Context-Engineering: `context-compression`, `context-degradation`, `filesystem-context`, `advanced-evaluation`, `evaluation`, `long-horizon-prompting` | MIT | `context-management`, `evaluation-method`, `review-method`, `task-writing` |
| ruvnet/claude-flow (ruflo) 3.58.1: `verification-quality`, `sparc/specification.md`, `sparc/refinement.md`, `core/planner.md`, `nested-queen.md`, `testing/production-validator.md` | MIT | `review-method`, `task-writing`, `expert-backend`, `verification` |
| mattpocock/skills: `grilling`, `research`, `grill-me`, `grill-with-docs`, `codebase-design`, `domain-modeling`, `to-tickets`, `prototype`, `tdd`, `diagnosing-bugs` | MIT (for `grilling`) | `counter-view-method`, `scouting-method`, `expert-architecture`, `expert-backend` |
| The "grill-me" pattern | not recorded | `interview` |
| VoltAgent/awesome-claude-code-subagents: `surgeon-reviewer`, `ponder-auditor`, `multi-agent-coordinator`, `research-analyst`, `search-specialist`, `docker-expert`, `kubernetes-specialist` | MIT | `advisor-method`, `orchestration`, `scouting-method`, `expert-docker` |
| vishalsachdev/claude-skills: `premortem` | MIT (repository) | `counter-view-method` |
| AmrAnwar/objection | MIT | `counter-view-method` |
| boshu2/agentops: `council` | not recorded | `counter-view-method`, `orchestration` |
| tsenart/council-skill: `council` | not recorded | `orchestration` |
| trailofbits/skills: `differential-review`, `fp-check`, `insecure-defaults`, `sharp-edges`, `supply-chain-risk-auditor`, `variant-analysis`, `agentic-actions-auditor` | not recorded | `review-method`, `expert-security`, `expert-server` |
| semgrep/skills: `code-security`, `llm-security` | not recorded | `expert-security`, `expert-docker`, `expert-server` |
| kepano/obsidian-skills (Steph Ango): `obsidian-markdown`, `obsidian-bases`, `json-canvas` | MIT | `obsidian-writing` |
| coreyhaines31/marketingskills (Corey Haines): `copywriting`, `copy-editing`, `content-strategy`, `social`, `seo-audit`, `schema`, `site-architecture`, `ai-seo` | MIT | `expert-content`, `expert-seo` |
| agricidaniel/claude-seo: `seo-content`, `seo-audit`, `seo-technical`, `seo-schema`, `seo-geo` | MIT | `expert-content`, `expert-seo` |
| blader/humanizer | MIT (per the repository page) | `expert-language` (`references/ai-traces.md`) |
| conorbronsdon/avoid-ai-writing, jooray/humanizer | MIT (per the repository pages) | `expert-language` (`references/ai-traces.md`) |
| ghanemzadeh/claude-skills: `line-and-copy-editor` | MIT (per the repository page) | `expert-language` (`references/ai-traces.md`) |
| alexconner-79/ill-communication | MIT (per the repository page) | `expert-writing` |
| jamditis/claude-skills-journalism | MIT (per the repository page); its skill files could not be opened, no content was taken | `news-method` |
| graphify | Apache-2.0 | `graph` |
| morluto/rea: `reverse-engineer-anything` (downloaded copy of 6.5.0) | MIT | `reverse-engineering` |
| takechanman1228/claude-persona | MIT | `synthetic-customer-test` |
| phuryn/pm-skills | MIT | `synthetic-customer-test` |
| massgen/MassGen: `skill-organizer` | not recorded | `skill-writing` |
| everything-claude-code: `api-design`, `database-migrations`, `eval-harness`, `mle-workflow` | not recorded | `expert-backend`, `expert-ml` |
| huggingface/skills: `huggingface-trackio`, `huggingface-community-evals`, `hf-mem`, `trl-training` | not recorded | `expert-ml` |
| alirezarezvani/claude-skills: `rag-architect` | not recorded | `expert-ml` |
| K-Dense-AI/scientific-agent-skills: `scikit-learn`, `statsmodels` | not recorded | `expert-ml` |
| vercel-labs/agent-skills: `web-design-guidelines`, `react-best-practices`, `composition-patterns` | not recorded | `expert-frontend`, `expert-design` |
| wshobson/agents: `ui-design`, `observability-monitoring`, `incident-response` | not recorded | `expert-design`, `expert-server` |
| hashicorp/agent-skills (Terraform) | not recorded | `expert-server` |
| ui-ux-pro-max (taken as an idea; not installed) | not recorded | `expert-design` |
| Hallmark skill: the idea of a measuring audit and a preservation counter, from its output records (the skill itself was not read) | not recorded | `expert-design` |
| bilawalsidhu/gods-eye-view | code MIT; data and 3D models licensed separately | `expert-geodata` |
| A public `/stil` skill text (address given with the text: `smokich.gosem.dev/stil`; the site was not opened, owner and license not verified) | not verified | `style` |

Several skill files note that a source was read from a downloaded copy and that its match with the official repository was not verified.

## Methods, research and references

| Source | Used in |
|---|---|
| SIFT (Mike Caulfield) | `news-method` |
| Rob Fitzpatrick, "The Mom Test" | `synthetic-customer-test` |
| Guimerà and Amaral (2005), "Functional cartography of complex metabolic networks", Nature 433 (participation coefficient) | `graph` |
| NN/g (Wang, Brown), Laws of UX (Yablonski), Smashing Magazine | `expert-design` |
| Designers: Anthony Hobday, Rauno Freiberg, Emil Kowalski, Adam Wathan and Steve Schoger (Refactoring UI), Josh Comeau, Ahmad Shadeed, Nikita Prokopov, Matthew Butterick, Luke Wroblewski | `expert-design` |
| Companies: Vercel, Linear, Stripe, Evil Martians, Microsoft Fluent | `expert-design` |
| WCAG 2.2 (https://www.w3.org/TR/WCAG22/) | `expert-design` |
| OWASP GenAI LLM Top 10 (https://genai.owasp.org/llm-top-10/) | `expert-security` |
| Turkish Language Association (TDK) spelling rule pages; the addresses are in `references/tdk.md` | `expert-language` |
| A social media image, "20 things to tell Claude" (source unknown) | `expert-security` |

## Our own design

The skill files mark these as our own design, with no outside source: the two-ended structure of `advisor-method` (judging at the start and at the end), the off-by-default bridge of `external-agent`, and the council of `orchestration` run through the central agent with a blind first round and at most two rounds.
