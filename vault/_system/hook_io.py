"""Hook input and output for every supported assistant: the guards read one shape and answer in the client's format.

The guard scripts take `--client <name>` (default `claude`). This module turns that client's PreToolUse payload into
a `Call` and writes the guard's decision the way that client reads it.

Fail-closed outside Claude: an unknown tool name, a missing field, a patch without a path or an internal error is
denied. An empty session id becomes `session_mode.UNKNOWN_SESSION`, which counts as unrecorded. Claude keeps its old
behaviour (a tool it does not guard is ignored; an internal error asks the user).

Payload fields come from the clients' documents and were not tried with the real CLIs. Antigravity (docs/hooks):
`conversationId`, `workspacePaths`, `toolCall.name`, `toolCall.args`; run_command `CommandLine`, `Cwd`; the file tools
`TargetFile`; read_url_content `Url`. If a field is missing or renamed, the call is denied, never allowed.
"""
from __future__ import annotations

import json
import re
import shlex
from dataclasses import dataclass

import session_mode as sm

CLIENTS = ("claude", "codex", "gemini", "antigravity")
CLIENT_HOMES = (".claude", ".codex", ".gemini", ".agents")   # settings, hooks, instructions and skills of each client
FAIL = "fail"   # the guard could not read the call
ASK_OR_DENY = "ask-or-deny"   # a recursive delete: always ask where the client can ask, deny where it cannot
ASK_OR_CLIENT = "ask-or-client"   # a single delete: ask, or leave it to the client's own approval (Codex)

SHELL, WRITE, WEB = "shell", "write", "web"
TOOLS = {
    "claude": {"Bash": SHELL, "PowerShell": SHELL, "Write": WRITE, "Edit": WRITE, "MultiEdit": WRITE, "NotebookEdit": WRITE},
    "codex": {"Bash": SHELL, "apply_patch": WRITE},
    "gemini": {"run_shell_command": SHELL, "write_file": WRITE, "replace": WRITE, "web_fetch": WEB},
    "antigravity": {"run_command": SHELL, "write_to_file": WRITE, "replace_file_content": WRITE,
                    "multi_replace_file_content": WRITE, "read_url_content": WEB},
}
ARGUMENTS = {   # client → (command key, file path key); Codex carries its paths inside the patch text
    "codex": ("command", None),
    "gemini": ("command", "file_path"),
    "antigravity": ("CommandLine", "TargetFile"),
}
# web tools: an address runs to the next space, so "https://ok.com)@evil.com" is checked whole (as evil.com)
WEB_ADDRESS = re.compile(r"(?i)https?://\S+")
ADDRESS_TAIL = ".,;:!?'\")]}>"   # closing punctuation of the sentence around an address
PATCH_LINE = re.compile(r"^\s*\*\*\*\s*(Begin Patch|End Patch|End of File|(?:Add|Update|Delete) File:|Move to:)\s*(.*?)\s*$")
PATCH_MARK = re.compile(r"^\s*\*\*\*")
CWD_FIELDS = {"gemini": "dir_path"}   # a tool argument that sets the command's own folder (Gemini CLI docs)
_emitted = []   # decisions printed by this process; Antigravity needs one decision on every call


class UnknownCall(ValueError):
    """The payload is not one this guard can judge; outside Claude it is denied."""


@dataclass(frozen=True)
class Call:
    client: str
    kind: str
    tool: str
    command: str = ""
    paths: tuple = ()
    urls: tuple = ()
    cwd: str = ""
    session_id: str = ""


def client_from_args(args: list) -> str:
    """`--client name` or `--client=name`; no flag means Claude. A wrong or empty name raises UnknownCall."""
    client = None
    for i, arg in enumerate(args):
        if arg == "--client":
            client = args[i + 1] if i + 1 < len(args) else ""
        elif arg.startswith("--client="):
            client = arg.split("=", 1)[1]
    if client is None:
        return "claude"
    if client not in CLIENTS:
        raise UnknownCall(f"unknown client: {client or '(none)'}")
    return client


def required(fields: dict, key: str) -> str:
    value = fields.get(key)
    if isinstance(value, list):   # an argv list: quoted, so a part holding a quote cannot hide the rest
        value = shlex.join(str(part) for part in value)
    if not isinstance(value, str) or not value.strip():
        raise UnknownCall(f"missing field: {key}")
    return value


def patch_paths(patch: str) -> tuple:
    """Every file a Codex patch touches. Headers may carry spaces around them; a `***` line that is not a known
    instruction, or a patch without a path, is not understood."""
    paths = []
    for line in patch.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if not PATCH_MARK.match(line):
            continue
        m = PATCH_LINE.match(line)
        if not m:
            raise UnknownCall(f"unknown patch instruction: {line.strip()[:60]}")
        if m.group(1).endswith(":"):
            if not m.group(2):
                raise UnknownCall("patch header without a path")
            paths.append(m.group(2))
    if not paths:
        raise UnknownCall("no file path in the patch")
    return tuple(paths)


def web_addresses(fields: dict) -> tuple:
    """Every web address in the text arguments, whatever their names; none found means the call is not understood."""
    texts = [value for value in fields.values() if isinstance(value, str)]
    texts += [item for value in fields.values() if isinstance(value, list) for item in value if isinstance(item, str)]
    urls = tuple(m.group(0).rstrip(ADDRESS_TAIL) for text in texts for m in WEB_ADDRESS.finditer(text))
    if not urls:
        raise UnknownCall("no web address in the tool input")
    return urls


def envelope(client: str, data: dict) -> tuple:
    """(tool name, tool arguments, working folder, session id) as the client sends them."""
    if client == "antigravity":
        tool_call = data.get("toolCall") or {}
        args = tool_call.get("args")
        workspaces = data.get("workspacePaths") or []
        workspace = workspaces[0] if isinstance(workspaces, list) and workspaces else ""
        cwd = (args.get("Cwd") if isinstance(args, dict) else None) or workspace   # run_command carries its own folder
        return str(tool_call.get("name") or ""), args, str(cwd), str(data.get("conversationId") or "")
    fields = data.get("tool_input")
    own_folder = fields.get(CWD_FIELDS[client]) if client in CWD_FIELDS and isinstance(fields, dict) else None
    return (str(data.get("tool_name") or ""), fields, str(own_folder or data.get("cwd") or ""),
            str(data.get("session_id") or ""))


def claude_call(tool: str, fields: dict, cwd: str, session: str, kind: str) -> Call:
    if kind == SHELL:
        return Call("claude", kind, tool, command=str(fields.get("command") or ""), cwd=cwd, session_id=session)
    path = fields.get("file_path") or fields.get("notebook_path")
    return Call("claude", kind, tool, paths=(str(path),) if path else (), cwd=cwd, session_id=session)


def other_call(client: str, tool: str, fields: dict, cwd: str, session: str, kind: str) -> Call:
    session = session.strip() or sm.UNKNOWN_SESSION
    if kind == WEB:
        return Call(client, kind, tool, urls=web_addresses(fields), cwd=cwd, session_id=session)
    command_key, path_key = ARGUMENTS[client]
    if kind == SHELL:
        return Call(client, kind, tool, command=required(fields, command_key), cwd=cwd, session_id=session)
    paths = patch_paths(required(fields, command_key)) if path_key is None else (required(fields, path_key),)
    return Call(client, kind, tool, paths=paths, cwd=cwd, session_id=session)


def read_call(client: str, data: dict, kind: str) -> Call | None:
    """The call if this guard (`kind`) judges it; None if another guard does. Raises UnknownCall when unsure."""
    tool, fields, cwd, session = envelope(client, data)
    known = TOOLS[client].get(tool)
    if known is None:
        if client == "claude":
            return None
        raise UnknownCall(f"unknown tool: {tool or '(none)'}")
    if known != kind:
        return None
    if fields is None and client == "claude":
        fields = {}
    if not isinstance(fields, dict):
        raise UnknownCall("tool input is not an object")
    if client == "claude":
        return claude_call(tool, fields, cwd, session, kind)
    return other_call(client, tool, fields, cwd, session, kind)


def render(client: str, decision: str, reason: str) -> str:
    """The text to print for `decision` (allow, ask, deny, ASK_OR_DENY or FAIL); "" means stay silent. Every client
    exits with 0."""
    if client == "claude":
        claude_decision = "ask" if decision in (FAIL, ASK_OR_DENY, ASK_OR_CLIENT) else decision
        return json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": claude_decision,
                                                  "permissionDecisionReason": reason}}, ensure_ascii=False)
    if client == "codex":
        # Codex has no "ask": a single delete is left to Codex's own approval (the user's decision); everything else
        # Claude would ask is denied.
        if decision in ("allow", ASK_OR_CLIENT):
            return ""
        return json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                  "permissionDecisionReason": reason}}, ensure_ascii=False)
    if client == "antigravity":
        # "allow" defers to the next hook or the default policy; "force_ask" asks even when a permission was cached.
        answer = {"allow": "allow", "ask": "ask", ASK_OR_CLIENT: "ask", ASK_OR_DENY: "force_ask"}.get(decision, "deny")
        return json.dumps({"decision": answer, "reason": reason}, ensure_ascii=False)
    if decision == "allow":
        return ""
    # Gemini CLI: no "ask" was confirmed in its documents, so ask is denied with its reason.
    return json.dumps({"decision": "deny", "reason": reason}, ensure_ascii=False)


def deny_for_every_client(reason: str) -> str:
    """For a hook started with a wrong --client: one answer every client reads as a denial."""
    return json.dumps({"decision": "deny", "reason": reason,
                       "hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                              "permissionDecisionReason": reason}}, ensure_ascii=False)


def emit(client: str, decision: str, reason: str) -> None:
    text = render(client, decision, reason)
    if text:
        print(text)
        _emitted.append(decision)


def finish(client: str) -> None:
    """Antigravity requires a decision on every PreToolUse call: a guard that said nothing defers with "allow"."""
    if client == "antigravity" and not _emitted:
        emit(client, "allow", "")
