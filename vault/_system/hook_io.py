"""Hook input and output for every supported assistant: the guards read one shape and answer in the client's format.

The guard scripts take `--client <name>` (default `claude`). This module turns that client's PreToolUse payload into
a `Call` and writes the guard's decision the way that client reads it.

Fail-closed outside Claude: an unknown tool name, a missing field, a patch without a path or an internal error is
denied. An empty session id becomes `session_mode.UNKNOWN_SESSION`, which counts as unrecorded. Claude keeps its old
behaviour (a tool it does not guard is ignored; an internal error asks the user).

Payload fields come from the clients' documents and were not tried with the real CLIs. The Antigravity argument
names (`CommandLine`, `TargetFile`, `Cwd`) are not confirmed by a document; if they are wrong, every call is denied,
never allowed.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

import session_mode as sm

CLIENTS = ("claude", "codex", "gemini", "antigravity")
CLIENT_HOMES = (".claude", ".codex", ".gemini", ".agents")   # settings, hooks, instructions and skills of each client
FAIL = "fail"   # the guard could not read the call
ASK_OR_DENY = "ask-or-deny"   # ask where the client can ask the user (Claude), deny elsewhere: a recursive delete

SHELL, WRITE = "shell", "write"
TOOLS = {
    "claude": {"Bash": SHELL, "PowerShell": SHELL, "Write": WRITE, "Edit": WRITE, "MultiEdit": WRITE, "NotebookEdit": WRITE},
    "codex": {"Bash": SHELL, "apply_patch": WRITE},
    "gemini": {"run_shell_command": SHELL, "write_file": WRITE, "replace": WRITE},
    "antigravity": {"run_command": SHELL, "write_to_file": WRITE, "replace_file_content": WRITE},
}
PATCH_PATH = re.compile(r"(?m)^\*\*\* (?:Add|Update|Delete) File: (.+?)\s*$|^\*\*\* Move to: (.+?)\s*$")


class UnknownCall(ValueError):
    """The payload is not one this guard can judge; outside Claude it is denied."""


@dataclass(frozen=True)
class Call:
    client: str
    kind: str
    tool: str
    command: str = ""
    paths: tuple = ()
    cwd: str = ""
    session_id: str = ""


def client_from_args(args: list) -> str:
    if "--client" not in args:
        return "claude"
    position = args.index("--client") + 1
    client = args[position] if position < len(args) else ""
    if client not in CLIENTS:
        raise UnknownCall(f"unknown client: {client or '(none)'}")
    return client


def required(fields: dict, key: str) -> str:
    value = fields.get(key)
    if isinstance(value, list):
        value = " ".join(str(part) for part in value)
    if not isinstance(value, str) or not value.strip():
        raise UnknownCall(f"missing field: {key}")
    return value


def patch_paths(patch: str) -> tuple:
    paths = tuple(m.group(1) or m.group(2) for m in PATCH_PATH.finditer(patch))
    if not paths:
        raise UnknownCall("no file path in the patch")
    return paths


def tool_and_fields(client: str, data: dict) -> tuple:
    if client == "antigravity":
        tool_call = data.get("toolCall") or {}
        return str(tool_call.get("name") or ""), tool_call.get("args") or {}, str((tool_call.get("args") or {}).get("Cwd") or "")
    return str(data.get("tool_name") or ""), data.get("tool_input") or {}, str(data.get("cwd") or "")


def claude_call(tool: str, fields: dict, cwd: str, session: str, kind: str) -> Call:
    if kind == SHELL:
        return Call("claude", kind, tool, command=str(fields.get("command") or ""), cwd=cwd, session_id=session)
    path = fields.get("file_path") or fields.get("notebook_path")
    return Call("claude", kind, tool, paths=(str(path),) if path else (), cwd=cwd, session_id=session)


def other_call(client: str, tool: str, fields: dict, cwd: str, session: str, kind: str) -> Call:
    session = session or sm.UNKNOWN_SESSION
    if kind == SHELL:
        key = "CommandLine" if client == "antigravity" else "command"
        return Call(client, kind, tool, command=required(fields, key), cwd=cwd, session_id=session)
    if client == "codex":
        paths = patch_paths(required(fields, "command"))
    else:
        paths = (required(fields, "TargetFile" if client == "antigravity" else "file_path"),)
    return Call(client, kind, tool, paths=paths, cwd=cwd, session_id=session)


def read_call(client: str, data: dict, kind: str) -> Call | None:
    """The call if this guard (`kind`) judges it; None if another guard does. Raises UnknownCall when unsure."""
    tool, fields, cwd = tool_and_fields(client, data)
    known = TOOLS[client].get(tool)
    if known is None:
        if client == "claude":
            return None
        raise UnknownCall(f"unknown tool: {tool or '(none)'}")
    if known != kind:
        return None
    if not isinstance(fields, dict):
        raise UnknownCall("tool input is not an object")
    session = str(data.get("session_id") or "")
    if client == "claude":
        return claude_call(tool, fields, cwd, session, kind)
    return other_call(client, tool, fields, cwd, session, kind)


def render(client: str, decision: str, reason: str) -> str:
    """The text to print for `decision` (allow, ask, deny, ASK_OR_DENY or FAIL); "" means stay silent. Every client
    exits with 0."""
    if client == "claude":
        claude_decision = "ask" if decision in (FAIL, ASK_OR_DENY) else decision
        return json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": claude_decision,
                                                  "permissionDecisionReason": reason}}, ensure_ascii=False)
    if client == "codex":
        # Codex has no "ask": a single delete is left to Codex's own approval; only a clear danger is denied.
        if decision not in ("deny", FAIL, ASK_OR_DENY):
            return ""
        return json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                  "permissionDecisionReason": reason}}, ensure_ascii=False)
    if decision == "allow":
        return json.dumps({"decision": "allow", "reason": reason}, ensure_ascii=False) if client == "antigravity" else ""
    # Gemini CLI and Antigravity: no "ask" was confirmed in their documents, so ask is denied with its reason.
    return json.dumps({"decision": "deny", "reason": reason}, ensure_ascii=False)


def emit(client: str, decision: str, reason: str) -> None:
    text = render(client, decision, reason)
    if text:
        print(text)
