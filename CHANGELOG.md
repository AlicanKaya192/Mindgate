<div align="right">
  <a href="./CHANGELOG.tr.md">Türkçe</a> · <b>English</b>
</div>

# Changelog

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

1. Get v1.2.0 (`git pull` in your Mindgate folder, or download the release).
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
