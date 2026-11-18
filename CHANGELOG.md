<div align="right">
  <a href="./CHANGELOG.tr.md">Türkçe</a> · <b>English</b>
</div>

# Changelog

## v1.2.2 — Security update: hooks in skill files

**Updating is recommended.** A skill (`SKILL.md`) or agent definition can carry a `hooks:` field in its frontmatter.
Such a hook runs a command on every tool call while the skill or agent is active, without passing `settings.json`, so
the guards and the health report did not see it.

- **The write guard asks** when a write puts `hooks:` into the frontmatter of a skill or agent definition: any
  `SKILL.md`, and any `.md` under the vault's `_system/skills/` or `_system/agents/`, under `skills/` or `agents/` in
  every assistant's home (`~/.claude`, `~/.codex`, `~/.gemini`, `~/.agents`), or under a project's `.claude/skills/` or
  `.claude/agents/`. For an edit, a non-indented `hooks:` line in the new text is enough. A `hooks:` inside the body,
  such as an indented example in a code block, is not asked.
- **Modes 4 and 5, latest version everywhere:** two new modes, opened only when the user says "Mode 4" or "Mode 5". The council is the Mode 3 council; the difference is the main chat's model, the latest Fable (4) or Mythos (5), switched with the user's approval (without access it stays on Opus and says so; Mythos cannot be a subagent). Models are now given as versionless aliases (`opus`, `sonnet`, `haiku`, `fable`) so a new release is used by itself, unless the user pinned one. Rule #28, `orchestration`, `task-writing`, the global instructions and the schema tables are updated.
- **`health.py` shows existing ones:** the new check *Hooks in skill and agent definitions* scans the skill and agent
  definitions of the vault and of every assistant's home. A definition with `hooks:` is an error with the file name in
  the details; a file that cannot be read is a warning.

**How to update:** follow the v1.2.0 steps below, then run `health.py` once and look at the new check. If it names a
file, open it before you use that skill or agent again; hooks belong in `settings.json`.

**Also in this release**

- **The design audit measures more** (`expert-design`, `page_audit.py`): placeholder text and empty-looking headings
  or buttons, headings that overflow when 3 times longer, full-screen section height (`--section-threshold`), unequal
  left and right margins, images that did not load or have no size, WebGL contexts over a limit (`--webgl-limit`,
  default 4), and, in one extra measurement under `prefers-reduced-motion: reduce`, animations and rAF loops that keep
  running. Page weight comes from Resource Timing; what cannot be measured is printed as `UNMEASURABLE`.
- **The AI-trace list says what to do instead** (`expert-design`): every trace in `references/ai-traces.md` now
  carries its fix, and new **D** traces cover surface, icons, text, charts, the hero, motion and the template a
  cleaned-up screen falls back to. The flow decides first how much an existing screen should change; the direction
  names a character and one signature detail and keeps a real brand; five more interface-text rules; a chart and stat
  card section in `references/visual-craft.md`. Adapted from unslop (Damir Sokolovsky, CC BY 4.0); the text was
  rewritten, and its code, numeric values and absolute bans were not taken. Attribution is in `NOTICE.md`.
- **Searching a skill directory without installing** (`external-source-review`, new step 0): look at your own
  skills first, search only through the browser with permission, never run the directory's install tool, and treat
  install counts and stars as reading order, not as safety. The candidate's `SKILL.md` is read before any decision.
- **New skill: brand content and ads** (`expert-brand-content`): posts and carousels, product shoot briefs, UGC
  scripts, ad angles and test plans, and reading an ad report. An input inventory and a claim ledger come first;
  nothing invented, nothing published. `scripts/ad_metrics.py` computes spend, conversions, revenue, CPA and ROAS from
  a CSV without guessing the format: currency and attribution columns are named or declared absent, mixed currencies
  and broken cells are refused, and so are identical lines unless `--count-duplicates` is given. `expert-content`
  now points to it for brand copy.
- **New skill: game development** (`expert-game`): finds the engine from the project files (Godot, Unity, Unreal,
  Phaser, PixiJS, three.js, Bevy, pygame, LÖVE, Defold, Ebitengine, Roblox), then reads only the needed discipline
  (game feel, camera, level design, AI, procedural generation, saves, dialogue, input, UI, audio, shaders, physics,
  performance), genre and workflow (game jam, prototype, Steam, itch.io, game document) files. A verification ladder
  separates what ran from what was only checked or not verified; fun, feel and sound stay the user's call. Ideas and
  thresholds adapted in our own words; no text or code copied. Attribution is in `NOTICE.md`.

## v1.2.1 — Security update: update check

**Updating is recommended.** This release holds everything in v1.2.0 below and adds a way to hear about the next one.

- **Update check (off by default).** Mindgate is a set of files, not a program, so nothing told you when a release was
  out. `health.py` can now ask GitHub for the latest release and say `Mindgate vX is out (security update)`. Turn it
  on with `"update_check": {"enabled": true}` in `_system/config.json` (`_sistem/` in a Turkish install). It asks only
  `https://api.github.com/repos/AlicanKaya192/Mindgate/releases/latest`; nothing from the vault is sent, and only the
  version number of the answer is used. The daily and weekly tasks run `health.py`, so the warning reaches you there.
  While the check is off, the health report shows how to turn it on.
- **Python 3.10 works again.** A pattern in the command guard used syntax that came with Python 3.11; on 3.10 the
  command guard could not load. It is rewritten, and a test keeps 3.11-only pattern syntax out of the guards.
- **Hear about releases without the check:** on GitHub, *Watch → Custom → Releases* sends you a notice for every
  release.

**How to update:** follow the v1.2.0 steps below. The installer does not overwrite `config.json`; to use the update
check, add the `update_check` block from the release's `vault/_system/config.json` to yours (editing it is asked, by
design).

## v1.2.0 — Security update

**Updating is recommended.** This release tightens the command, write and site guards. On the same test inputs, the
shell commands the command guard let through without a word fell from 68 of 72 to 7 of 72, and its slowest decision
fell from 123 s to under 1 s.

### What changed

**One defense set.** `common.DEFENSE_SET` lists the files the guards stand on: the hook and permission settings of
Claude Code, Codex CLI, Gemini CLI and Antigravity, the vault's `.claude/settings*.json`, any `.claude/launch.json`,
the global and installed instructions, the other assistants' instruction files, scheduled tasks, the vault scripts in
`_system/` and its `config.json`, agent definitions (vault and every assistant), git hooks, the blocklist, the rules,
the master copy of the instructions and the vault schema. The write guard and the command guard both read it.

**Command guard**
- Writing to a defense file with the shell is asked (redirects, `sed -i`, `tee`, `Set-Content`, copy and move targets,
  Python code that opens the file for writing, a defense path given as an argument to a Python script that is not
  one of the vault's own `_system/` scripts). Reading, running a vault script, `git add` and `git commit` stay silent.
- A network call from the shell is asked, with the address in the reason: `curl`, `wget`, `Invoke-WebRequest`,
  `Invoke-RestMethod`, `Start-BitsTransfer`, `certutil -urlcache`; `nc`, `telnet`, `ssh`, `sftp`, `ftp`; `scp` and
  `rsync` with a remote path; .NET network classes; network code given to node, deno or bun; Python network modules,
  and `os.system`/`subprocess` calls that name a download tool; opening an address in the browser; `git clone`,
  `git remote add/set-url`, `git pull/push/fetch` with an address; `gh api`.
- Piping a download into an interpreter is refused, also with other commands in the pipe, an interpreter reading
  stdin (`| py -`), process substitution (`bash <(curl …)`) and decoded base64.
- Hidden command names are opened: quotes or backslashes inside the name (`"r""m"`, `c''url`, `r\m`), leading
  assignments and prefixes (`HUSKY=0`, `command`, `env`, `sudo -E`, `nohup`). A name computed with `$(…)` or a
  backtick is asked. Commands inside `eval "…"` and `Start-Process … -ArgumentList '…'` are checked like the others.
- A command over 20,000 characters is asked before any pattern runs, and refused in an unrecorded chat. The patterns
  that backtracked for minutes were rewritten.
- Skipping the commit hook (`--no-verify`, `-n`, `core.hooksPath`) is asked.
- More deletions are asked: `Clear-Content`, `: > file`, `truncate`, `$_.Delete()`, `git checkout -- <path>`,
  `git restore <path>`, `git worktree remove`, `robocopy /purge`, `rsync --delete`, `tar --remove-files`, `eval`,
  `Remove-Item <target> -Recurse` with the target first, Python `os.replace`/`shutil.move`.
- More ways to kill a process are refused: `kill $(pgrep …)`, `… | xargs kill`, `spps -Name`, `.Kill()`, WMI and CIM.
- Commands that show a secret are asked: `gh auth token`, `git credential`, `cmdkey`, printing the whole environment,
  printing a variable whose name looks like a secret, a secret file matched by a wildcard.
- Persistence and execution policy are asked: `reg add`, the Run key, `Set-ExecutionPolicy`, `-ExecutionPolicy Bypass`,
  `setx`, `git push +ref`.
- Installing a package is asked (`pip`, `pipx`, `uv`, `npm`, `pnpm`, `yarn`, `bun`, `winget`, `choco`, `scoop`).
- Applying a patch (`git apply`, `git am`) and moving a vault file to a temporary folder are asked.
- The terminal tool (`mcp__terminal__run_in_terminal`) is checked like Bash and PowerShell.
- If the guard cannot load its helper modules it asks (other assistants: refuses) instead of crashing.

**Write guard**
- Changing a defense file is asked (refused where the assistant cannot ask); the reason names the defense.
- A file named after a standard library module (`json.py`, `re.pyc`, a `json/` folder) under `_system/` is refused.
- If the guard cannot load its helper modules it asks (other assistants: refuses).

**Site guard**
- `WebSearch` is asked like a page, with the query in the reason.
- A certain sign of attack no longer writes a well-known site or multi-user hosting (`github.io`, `pages.dev`,
  `medium.com` …) to the blocklist on its own: one page must not block the whole site for good; the user decides.
- If a helper module cannot be loaded, every decision except a blocklist deny becomes ask and nothing is written to
  the blocklist.

**All guards** put their own folder at the end of the import path, so a file in `_system/` cannot shadow the
standard library. `hook_io.py` needs only the standard library, so it can still answer when another helper is broken.

**Health check** (`health.py`): security hooks and their matchers (the terminal tool for the command guard,
`WebSearch` for the site guard), broad permission patterns in the settings files, a script named after the standard
library, uncommitted changes in the guard scripts, the commit hook's integrity (`core.hooksPath`, the secret scan).

**Installer**: the Claude Code hook template adds `mcp__terminal__run_in_terminal` to the command guard's matcher and
`WebSearch` to the site guard's.

**Rules**: rule #28 says how an agent is named to the user: by role, model and effort, for example
"Developer Agent (Opus 5.5, High) did X".

### What you will notice

`pip install`, `npm install`, `curl` and `git clone` are now asked. Editing `_system/config.json`, a guard script, an
agent definition or the rules file is asked. A web search is asked.

### How to update

The installer does not overwrite files that already exist, so an existing install is updated by hand:

1. Get the latest release (`git pull` in your Mindgate folder, or download the release).
2. Close Claude Code. Copy every `vault/_system/*.py` file of the release into the `_system/` folder of your vault
   (`_sistem/` in a Turkish install; the script names are the same in both languages). Inside a session the write
   guard would ask for every file, by design.
3. In `~/.claude/settings.json`, add the two tool names to the existing Mindgate hooks: the command guard's matcher
   becomes `Bash|PowerShell|mcp__terminal__run_in_terminal`, and the site guard's PreToolUse matcher starts with
   `WebFetch|WebSearch|`. Uninstalling and installing again does the same.
4. Optional: take the new text of rule #28 from `vault/rules/general-rules.md` (Turkish:
   `locales/tr/vault/rules/general-rules.md`).
5. In the vault, run `py -3 -I _system/health.py` (Turkish install: `_sistem/health.py`): "Security hooks and their
   matchers" should say ok.

### Known limits

- A script that writes a file indirectly (`py tool.py` with the path inside the script) passes the command guard;
  `health.py` shows an uncommitted change in the guard scripts afterwards.
- A path or command name kept in a variable or joined from strings is not resolved.
- The read tools pass no guard. Web searches are guarded only in Claude Code.

## v1.1.0

See the `v1.1.0` tag.
