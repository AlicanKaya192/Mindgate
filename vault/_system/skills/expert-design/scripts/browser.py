"""Opens the local Edge or Chrome in the background and talks to it through the Chrome DevTools Protocol. Standard library only."""
import base64
import json
import os
import secrets
import shutil
import socket
import struct
import subprocess
import time
import urllib.request
from pathlib import Path

TIMEOUT_S = 30
CLOSE_WAIT_S = 5
PORT_WAIT_S = 20
WINDOWS_CANDIDATES = (
    r"Microsoft\Edge\Application\msedge.exe",
    r"Google\Chrome\Application\chrome.exe",
)
OTHER_CANDIDATES = ("microsoft-edge", "google-chrome", "chromium", "chromium-browser")
MAC_CANDIDATES = (
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
)
# The audited page must not send requests to an outside server; only local addresses are resolved.
NO_EXTERNAL_NETWORK = "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE localhost, EXCLUDE 127.0.0.1, EXCLUDE *.localhost, EXCLUDE *.test"
OPCODE_TEXT = 0x1
OPCODE_CLOSE = 0x8
OPCODE_PING = 0x9
OPCODE_PONG = 0xA


def find_browser() -> Path | None:
    """Path of an installed browser; None if there is none."""
    for root in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles"), os.environ.get("LOCALAPPDATA")):
        for candidate in WINDOWS_CANDIDATES if root else ():
            if (Path(root) / candidate).exists():
                return Path(root) / candidate
    for candidate in MAC_CANDIDATES:
        if Path(candidate).exists():
            return Path(candidate)
    for program in OTHER_CANDIDATES:
        if found := shutil.which(program):
            return Path(found)
    return None


class _WebSocket:
    """The smallest WebSocket client for CDP (RFC 6455): sends text, receives text."""

    def __init__(self, address: str):
        host_port, path = address.removeprefix("ws://").split("/", 1)
        host, port = host_port.rsplit(":", 1)
        self.socket = socket.create_connection((host, int(port)), timeout=TIMEOUT_S)
        key = base64.b64encode(secrets.token_bytes(16)).decode()
        self.socket.sendall(
            f"GET /{path} HTTP/1.1\r\nHost: {host_port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n".encode()
        )
        self.buffer = b""
        while b"\r\n\r\n" not in self.buffer:
            self.buffer += self._chunk()
        header, self.buffer = self.buffer.split(b"\r\n\r\n", 1)
        if b" 101 " not in header.split(b"\r\n", 1)[0]:
            raise ConnectionError(f"WebSocket handshake failed: {header[:80]!r}")

    def _chunk(self) -> bytes:
        data = self.socket.recv(65536)
        if not data:
            raise ConnectionError("The browser closed the connection")
        return data

    def _read(self, count: int) -> bytes:
        while len(self.buffer) < count:
            self.buffer += self._chunk()
        data, self.buffer = self.buffer[:count], self.buffer[count:]
        return data

    def send(self, text: str, opcode: int = OPCODE_TEXT) -> None:
        body = text.encode()
        mask = secrets.token_bytes(4)
        size = len(body)
        if size < 126:
            header = struct.pack("!BB", 0x80 | opcode, 0x80 | size)
        elif size < 65536:
            header = struct.pack("!BBH", 0x80 | opcode, 0x80 | 126, size)
        else:
            header = struct.pack("!BBQ", 0x80 | opcode, 0x80 | 127, size)
        self.socket.sendall(header + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(body)))

    def receive(self) -> str:
        parts = b""
        while True:
            first, second = self._read(2)
            final, opcode, size = first & 0x80, first & 0x0F, second & 0x7F
            if size == 126:
                size = struct.unpack("!H", self._read(2))[0]
            elif size == 127:
                size = struct.unpack("!Q", self._read(8))[0]
            body = self._read(size)
            if opcode == OPCODE_PING:
                self.send(body.decode(errors="replace"), OPCODE_PONG)
            elif opcode == OPCODE_CLOSE:
                raise ConnectionError("The browser closed the WebSocket")
            else:
                parts += body
                if final:
                    return parts.decode()

    def close(self) -> None:
        self.socket.close()


class Browser:
    """A headless browser opened with its own profile. It does not touch the personal browser session; the profile is
    not deleted, it is reused."""

    def __init__(self, profile: Path, external_network: bool = False):
        path = find_browser()
        if not path:
            raise FileNotFoundError("Edge or Chrome not found")
        profile = Path(profile)
        profile.mkdir(parents=True, exist_ok=True)
        port_file = profile / "DevToolsActivePort"
        port_file.unlink(missing_ok=True)
        arguments = [
            str(path), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
            "--disable-extensions", "--disable-sync", "--disable-background-networking", "--disable-component-update",
            "--remote-debugging-address=127.0.0.1", "--remote-debugging-port=0", f"--user-data-dir={profile}", "about:blank",
        ]
        if not external_network:
            arguments.insert(1, NO_EXTERNAL_NETWORK)
        self.process = subprocess.Popen(arguments, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self._id = 0
        self.ws = _WebSocket(self._page_address(self._wait_for_port(port_file)))
        self.command("Page.enable")
        # A headless page does not count itself as focused; without this :focus-visible never matches and the focus
        # check gives a false warning.
        self.command("Emulation.setFocusEmulationEnabled", enabled=True)

    def _wait_for_port(self, file: Path) -> int:
        deadline = time.monotonic() + PORT_WAIT_S
        while time.monotonic() < deadline:
            if file.exists() and (lines := file.read_text(encoding="utf-8").split()):
                return int(lines[0])
            time.sleep(0.1)
        raise TimeoutError(f"The browser did not open the debugging port within {PORT_WAIT_S} s")

    def _page_address(self, port: int) -> str:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(f"http://127.0.0.1:{port}/json/list", timeout=TIMEOUT_S) as answer:
            targets = json.load(answer)
        return next(t["webSocketDebuggerUrl"] for t in targets if t["type"] == "page")

    def command(self, method: str, **params) -> dict:
        self._id += 1
        self.ws.send(json.dumps({"id": self._id, "method": method, "params": params}))
        while True:
            message = json.loads(self.ws.receive())
            if message.get("id") == self._id:
                if "error" in message:
                    raise RuntimeError(f"{method}: {message['error'].get('message')}")
                return message["result"]

    def open(self, address: str) -> None:
        """Opens the address and waits for the load event."""
        result = self.command("Page.navigate", url=address)
        if error := result.get("errorText"):
            raise ConnectionError(f"{address} could not be opened: {error}")
        while json.loads(self.ws.receive()).get("method") != "Page.loadEventFired":
            pass

    def evaluate(self, expression: str):
        """Runs the expression in the page and returns the value of the result."""
        result = self.command("Runtime.evaluate", expression=expression, returnByValue=True, awaitPromise=True)
        if details := result.get("exceptionDetails"):
            raise RuntimeError(f"Error in the page: {details.get('exception', {}).get('description', details.get('text'))}")
        return result["result"].get("value")

    def close(self) -> None:
        """Closes only the process this object opened."""
        try:
            self.command("Browser.close")
        except (ConnectionError, TimeoutError, OSError):
            pass  # The browser may close before it sends the answer to the command; the process is still awaited below.
        self.ws.close()
        try:
            self.process.wait(timeout=CLOSE_WAIT_S)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            self.process.wait(timeout=CLOSE_WAIT_S)
