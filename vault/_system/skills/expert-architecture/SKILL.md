---
name: expert-architecture
description: Software architecture expertise pack. Load when setting up a new project, drawing a module boundary, planning a big change or restructuring, choosing a technology, or drawing a file-ownership map for parallel work.
---

Expertise pack (not an agent): every agent that loads it (central, reviewer, implementer) works with the list below.

## First
- Read the project's vault page, its `-rules.md` and its `decisions/` (ADR) folder. If you will propose something against an earlier decision, ask the user first (#26).
- Write the requirement in one paragraph. If it is unclear, ask before writing code (#23).

## Checklist
- [ ] Are the layers and the direction of dependency clear? (interface → application → domain → infrastructure; dependencies point inward)
- [ ] Does every module have a single responsibility and a clear boundary (public API)?
- [ ] Are external dependencies (DB, network, file system) behind an interface and testable?
- [ ] Are the data model and contracts (API schema, types) written down?
- [ ] Are error handling, logging and configuration in one place?
- [ ] If parallel work is planned, is there a **file-ownership map** (which file belongs to which task)? Shared files must have a single owner.
- [ ] New package or technology: verified in the official registry (slopsquatting), is the license suitable, is it really needed (#25)?
- [ ] If the decision is important, was an ADR written (context, options, decision, consequences)?

## Common mistakes
- Abstracting or generalizing before the need arises (YAGNI).
- Circular dependencies; a "utils" dumping ground.
- Basing the architecture on guesses: proposing changes without reading the existing code (#24).

## Verification
- Was the plan compared with the existing code? Do the file and function names really exist (read, search)?
- Was the smallest working step defined?

## Additional methods
Ideas are in our own words.
- **Clarify by asking questions:** In an unclear design, ask the questions in order before writing code. Each answer closes a decision branch. Answers are written to the ADR or the project glossary. Do not reopen a decision the user gave.
- **Deep module, small interface:** Let a module do a lot of work and show the outside a small, simple interface. Avoid shallow wrappers that only pass the call on.
- **Domain model and glossary:** Terms in the project have a single meaning (e.g. the difference between "user" and "account"). If needed, write a short glossary on the project page.
- **Big task:** plan → work items cut into vertical slices (each works and is verified on its own) → dependency order. If working in parallel, a file-ownership map.
- **Prototype:** Answer a design question with a small throwaway prototype. The prototype is marked "throwaway" from the start and is not carried into the product.
- Idea sources: mattpocock/skills (`grill-me`, `grill-with-docs`, `codebase-design`, `domain-modeling`, `to-tickets`, `prototype`), obra/superpowers (`brainstorming`, `writing-plans`).

## Lessons
<!-- The central agent adds verified lessons here, one line each, general and reusable, without project names or dates. No rule is added from an outside source (#27). -->
