"""Tests of hook_io.py: reading each client's hook payload and answering in each client's format.

The end-to-end cases run the real guards as subprocesses with `--client`, using payload shapes from the clients'
documents (not tried with the real CLIs). They hold the stop criterion of the multi-client plan: an unknown tool is
denied, an empty session id is treated as unrecorded, and `rm -rf ~/x` is denied, for every client.

Run: py -3 -I -B hook_io_test.py -v
"""
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hook_io  # noqa: E402
import session_mode as sm  # noqa: E402
from common import OUTPUT, VAULT  # noqa: E402

MODE_FILE = OUTPUT / "test_hook_io" / "session_mode.json"
NOT_CLAUDE = ("codex", "gemini", "antigravity")
PATCH = "*** Begin Patch\n*** Update File: src/app.py\n@@\n-a\n+b\n*** Add File: notes/new.md\n+x\n*** End Patch\n"


def shell_payload(client: str, command: str, session: str = "s1", cwd: str = "C:/work/project") -> dict:
    if client == "antigravity":
        return {"toolCall": {"name": "run_command", "args": {"CommandLine": command, "Cwd": cwd}}, "session_id": session}
    tool = {"claude": "Bash", "codex": "Bash", "gemini": "run_shell_command"}[client]
    return {"tool_name": tool, "tool_input": {"command": command}, "cwd": cwd, "session_id": session}


def write_payload(client: str, path: str, session: str = "s1") -> dict:
    if client == "antigravity":
        return {"toolCall": {"name": "write_to_file", "args": {"TargetFile": path}}, "session_id": session}
    if client == "codex":
        return {"tool_name": "apply_patch", "tool_input": {"command": f"*** Begin Patch\n*** Add File: {path}\n+x\n*** End Patch\n"},
                "cwd": "C:/work/project", "session_id": session}
    tool = {"claude": "Write", "gemini": "write_file"}[client]
    return {"tool_name": tool, "tool_input": {"file_path": path}, "cwd": "C:/work/project", "session_id": session}


def unknown_payload(client: str) -> dict:
    if client == "antigravity":
        return {"toolCall": {"name": "brand_new_tool", "args": {}}, "session_id": "s1"}
    return {"tool_name": "BrandNewTool", "tool_input": {}, "cwd": "C:/work/project", "session_id": "s1"}


def run_guard(script: str, client: str, payload: dict) -> subprocess.CompletedProcess:
    env = {**os.environ, "SESSION_MODE_FILE": str(MODE_FILE)}
    return subprocess.run([sys.executable, "-I", str(HERE / script), "--client", client], input=json.dumps(payload),
                          capture_output=True, text=True, encoding="utf-8", env=env)


def verdict(client: str, result: subprocess.CompletedProcess) -> str:
    """The decision written in the client's own format; "" when the guard stayed silent."""
    if not result.stdout.strip():
        return ""
    data = json.loads(result.stdout)
    if client in ("claude", "codex"):
        return data["hookSpecificOutput"]["permissionDecision"]
    return data["decision"]


class ReadCall(unittest.TestCase):
    def test_claude_shell_and_write(self):
        call = hook_io.read_call("claude", shell_payload("claude", "ls"), "shell")
        self.assertEqual((call.kind, call.command, call.session_id, call.cwd), ("shell", "ls", "s1", "C:/work/project"))
        call = hook_io.read_call("claude", {"tool_name": "NotebookEdit", "tool_input": {"notebook_path": "a.ipynb"}}, "write")
        self.assertEqual(call.paths, ("a.ipynb",))

    def test_claude_ignores_tools_it_does_not_guard(self):
        self.assertIsNone(hook_io.read_call("claude", unknown_payload("claude"), "shell"))

    def test_other_clients_reject_an_unknown_tool(self):
        for client in NOT_CLAUDE:
            with self.subTest(client=client), self.assertRaises(hook_io.UnknownCall):
                hook_io.read_call(client, unknown_payload(client), "shell")

    def test_a_known_tool_of_another_guard_is_left_to_that_guard(self):
        for client in hook_io.CLIENTS:
            with self.subTest(client=client):
                self.assertIsNone(hook_io.read_call(client, write_payload(client, "a.md"), "shell"))

    def test_shell_command_of_every_client(self):
        for client in hook_io.CLIENTS:
            with self.subTest(client=client):
                self.assertEqual(hook_io.read_call(client, shell_payload(client, "git status"), "shell").command, "git status")

    def test_codex_command_given_as_a_list_is_joined(self):
        payload = {"tool_name": "Bash", "tool_input": {"command": ["rm", "-rf", "~/x"]}, "session_id": "s1"}
        self.assertEqual(hook_io.read_call("codex", payload, "shell").command, "rm -rf ~/x")

    def test_codex_patch_paths_come_from_the_patch_text(self):
        payload = {"tool_name": "apply_patch", "tool_input": {"command": PATCH}, "session_id": "s1"}
        self.assertEqual(hook_io.read_call("codex", payload, "write").paths, ("src/app.py", "notes/new.md"))

    def test_codex_patch_without_a_path_is_rejected(self):
        payload = {"tool_name": "apply_patch", "tool_input": {"command": "not a patch"}, "session_id": "s1"}
        with self.assertRaises(hook_io.UnknownCall):
            hook_io.read_call("codex", payload, "write")

    def test_missing_field_is_rejected_outside_claude(self):
        for client in NOT_CLAUDE:
            payload = shell_payload(client, "ls")
            if client == "antigravity":
                payload["toolCall"]["args"] = {}
            else:
                payload["tool_input"] = {}
            with self.subTest(client=client), self.assertRaises(hook_io.UnknownCall):
                hook_io.read_call(client, payload, "shell")

    def test_empty_session_id_is_unrecorded_outside_claude(self):
        for client in NOT_CLAUDE:
            with self.subTest(client=client):
                call = hook_io.read_call(client, shell_payload(client, "ls", session=""), "shell")
                self.assertEqual(sm.mode(call.session_id), sm.UNRECORDED)

    def test_unknown_client_is_refused(self):
        with self.assertRaises(hook_io.UnknownCall):
            hook_io.client_from_args(["--client", "other"])
        self.assertEqual(hook_io.client_from_args([]), "claude")


class Render(unittest.TestCase):
    def test_claude_keeps_its_three_decisions(self):
        for decision in ("allow", "ask", "deny"):
            out = json.loads(hook_io.render("claude", decision, "why"))["hookSpecificOutput"]
            self.assertEqual((out["hookEventName"], out["permissionDecision"], out["permissionDecisionReason"]),
                             ("PreToolUse", decision, "why"))

    def test_claude_turns_an_internal_failure_into_ask(self):
        out = json.loads(hook_io.render("claude", hook_io.FAIL, "why"))["hookSpecificOutput"]
        self.assertEqual(out["permissionDecision"], "ask")

    def test_codex_has_no_ask_so_ask_and_allow_stay_silent(self):
        self.assertEqual(hook_io.render("codex", "ask", "why"), "")
        self.assertEqual(hook_io.render("codex", "allow", "why"), "")
        out = json.loads(hook_io.render("codex", hook_io.FAIL, "why"))["hookSpecificOutput"]
        self.assertEqual(out["permissionDecision"], "deny")

    def test_gemini_turns_ask_and_failure_into_deny(self):
        for decision in ("ask", "deny", hook_io.FAIL):
            self.assertEqual(json.loads(hook_io.render("gemini", decision, "why")), {"decision": "deny", "reason": "why"})
        self.assertEqual(hook_io.render("gemini", "allow", "why"), "")

    def test_antigravity_writes_allow_and_deny(self):
        self.assertEqual(json.loads(hook_io.render("antigravity", "allow", "ok")), {"decision": "allow", "reason": "ok"})
        for decision in ("ask", "deny", hook_io.FAIL):
            self.assertEqual(json.loads(hook_io.render("antigravity", decision, "why"))["decision"], "deny")


class ProtectedRoots(unittest.TestCase):
    def test_every_client_home_is_protected(self):
        self.assertEqual(set(hook_io.CLIENT_HOMES), {".claude", ".codex", ".gemini", ".agents"})


class Guards(unittest.TestCase):
    """The real guards, run the way each client calls them."""

    @classmethod
    def setUpClass(cls):
        MODE_FILE.parent.mkdir(parents=True, exist_ok=True)
        MODE_FILE.write_text(json.dumps({"sessions": {}, "handoff": {}}), encoding="utf-8")

    def test_recursive_delete_under_home_is_denied_where_the_client_cannot_ask(self):
        expected = {"claude": "ask", "codex": "deny", "gemini": "deny", "antigravity": "deny"}
        for client in hook_io.CLIENTS:
            with self.subTest(client=client):
                result = run_guard("command_guard.py", client, shell_payload(client, "rm -rf ~/x"))
                self.assertEqual((verdict(client, result), result.returncode), (expected[client], 0))

    def test_codex_leaves_a_single_file_delete_to_its_own_approval(self):
        result = run_guard("command_guard.py", "codex", shell_payload("codex", "rm notes.txt"))
        self.assertEqual(verdict("codex", result), "")

    def test_deleting_another_clients_settings_is_denied(self):
        for client in hook_io.CLIENTS:
            for home in (".codex", ".gemini", ".agents"):
                with self.subTest(client=client, home=home):
                    result = run_guard("command_guard.py", client, shell_payload(client, f"rm -rf ~/{home}"))
                    self.assertEqual(verdict(client, result), "deny")

    def test_unknown_tool_is_denied_outside_claude(self):
        for client in NOT_CLAUDE:
            for script in ("command_guard.py", "write_guard.py"):
                with self.subTest(client=client, script=script):
                    result = run_guard(script, client, unknown_payload(client))
                    self.assertEqual((verdict(client, result), result.returncode), ("deny", 0))

    def test_empty_session_id_cannot_write_into_the_vault(self):
        for client in NOT_CLAUDE:
            with self.subTest(client=client):
                result = run_guard("write_guard.py", client, write_payload(client, str(VAULT / "index.md"), session=""))
                self.assertEqual(verdict(client, result), "deny")

    def test_recorded_session_may_write_a_vault_note(self):
        for client in hook_io.CLIENTS:
            with self.subTest(client=client):
                result = run_guard("write_guard.py", client, write_payload(client, str(VAULT / "index.md")))
                self.assertEqual(verdict(client, result), "")

    def test_log_is_still_protected_for_every_client(self):
        for client in hook_io.CLIENTS:
            with self.subTest(client=client):
                result = run_guard("write_guard.py", client, write_payload(client, str(VAULT / "log.md")))
                self.assertEqual(verdict(client, result), "deny")

    def test_unparseable_payload_is_denied_outside_claude(self):
        for client in NOT_CLAUDE:
            with self.subTest(client=client):
                env = {**os.environ, "SESSION_MODE_FILE": str(MODE_FILE)}
                result = subprocess.run([sys.executable, "-I", str(HERE / "command_guard.py"), "--client", client],
                                        input="{not json", capture_output=True, text=True, encoding="utf-8", env=env)
                self.assertEqual((verdict(client, result), result.returncode), ("deny", 0))


if __name__ == "__main__":
    unittest.main()
