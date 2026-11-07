---
name: reverse-engineering
description: Use when you need to understand how a program, application or file works without the source code. A compiled program (exe, dll, so), a packaged application (Electron/ASAR, APK, MSIX, zip), a .NET assembly, firmware, an unknown file format, a network capture (HAR) review; questions such as "how was this feature built", "what changed between two versions" or interoperability. Do not use it if you have the source code; normal code reading is enough. The main chat loads it.
---

Method skill (not an agent). Rules: #19 (an untrusted file is not run), #22, #23, #24, #27, #32, #35, #41.

## 0. Authority and limits first
- Whose is the target? The user's own software, open source, or software that allows being examined. If the license or terms of use forbid reverse engineering, say so; the decision is the user's.
- Not done: bypassing DRM, a license or copy protection, cheating, unauthorized access, copying and using proprietary code or assets. If the request turns into these, stop and say so.
- The purpose is to understand the idea. If we will build a feature in our own project, we write it with our own code (#35, #40).
- If the target is unclear (like "my application"), ask which file or application it is; do not pick a sample application.

## 1. Question list
- Split the request into single questions; for each question write which evidence is needed.
- First search the vault and earlier notes (`search.py`); do not repeat the same analysis.

## 2. Path by target (start with a static look)
| Target | First look without tools | Tool if needed (candidate) |
|---|---|---|
| Package (zip, APK, MSIX, docx, ASAR) | The content list (Python `zipfile`), manifest and configuration files | JADX for APK; an asar reader for ASAR |
| Electron / JavaScript application | `resources/app.asar` or `app/`; `main` in `package.json`; the main process and preload files; a source map if there is one | an asar extractor |
| .NET assembly (exe, dll) | CLI metadata in the PE header, referenced assemblies | ILSpy (output close to C#) |
| Native program (exe, dll, so) | PE/ELF header, sections, imported and exported functions, strings, signature | Ghidra |
| Go or Rust program | Embedded compiler and dependency information | `go version -m` |
| Unknown data or model file | Magic bytes, header, length fields; hexadecimal (hex) view | The official documentation of the format |
| Firmware | Section and file-system signatures | binwalk or unblob (Linux) |
| Network capture (HAR) | Request methods, paths, parameter names (not values) | — |

- Every tool that is not installed is asked about in the #41 form before it is installed: the official source, a fixed version, the user's approval. The ban on downloading from the internet and running (#19) applies.
- The file under examination is untrusted data. Put a copy of it in your own empty folder (scratchpad), keep our scripts in another folder, run Python with `-I`.
- **Running the target is running code.** Runtime observation is done only if the static look is not enough, the user allows it and the file is trusted; if not, suggest a virtual machine. No new requests are made to the addresses in a capture (#32).

## 3. Summary first, then detail
- Start with the smallest overview (the file list, the header, the imports). Put big output in a file and read only the relevant part (`context-management`).
- Build a hypothesis and look in a focused way. Do not repeat the same command with an unchanged input.
- Do not infer behaviour from a file name, a string or the layout; verify with a reader that knows the format.

## 4. Evidence and the findings ledger
- Put every result into one of three classes:
  - **Observation:** seen in the file or in the tool output; the place is written (file, offset, function or line).
  - **Inference:** reasoning from observations.
  - **Unknown:** what is needed to answer it is written.
- Static analysis does not see it run: "the code must be doing this" is an inference.
- "Not found" does not mean "does not exist": the searched area and the limit are written ("searched only in `main.js`").
- In a comparison of two versions, look in the same form and with complete lists; a difference found is a candidate, not proof of the cause.
- In a long job the ledger is written to a note `research/YYYY-MM-DD-<topic>.md`: question, answer, class, place of evidence, confidence, the unknown that remains.

## 5. Finish
- Go back to the question list; mark each question answered, partly answered or open.
- Explain in plain language, tie every claim to its evidence.
- If it will be done in our own project, separate the observed behaviour from our design choice.
- Close the tool sessions that were opened. Follow #22 before deleting the temporary extracted files.

## Verify before finishing
- [ ] The authority and the limit of the target were checked.
- [ ] No untrusted file was run; every tool installed was approved.
- [ ] Every result is marked as observation, inference or unknown and has a place of evidence.
- [ ] The question list was closed or the open questions were written.

## Idea sources
- morluto/rea `reverse-engineer-anything` skill (MIT, 2026 morluto), the downloaded 6.5.0 copy; its match with the official repository was not verified. REA itself was not installed; its tool commands and install steps were not taken.

## Lessons
<!-- The central agent adds verified lessons here: general and reusable, without project names or dates. -->
