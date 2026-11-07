"""Renders the running page in a real browser at 6 widths and measures it; audit, preservation counter and round record
in one command.

    python -I page_audit.py http://localhost:3000/ --output audit --record design-record.json --baseline

By default only local addresses are opened and the page is blocked from reaching the external network.
Exit code: 0 passed, 1 failed, 2 usage error.
"""
import argparse
import base64
import datetime
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import audit_summary as summ  # noqa: E402
import browser as br  # noqa: E402

DEFAULT_WIDTHS = (320, 375, 768, 1280, 1440, 1920)
DARK_WIDTHS = (375, 1440)
MOBILE_LIMIT = 768
MOBILE_HEIGHT = 800
DESKTOP_HEIGHT = 900
LOCAL_NAMES = {"localhost", "127.0.0.1", "::1"}
LOCAL_SUFFIXES = (".localhost", ".test")
MEASURE_SCRIPT = HERE / "page_measure.js"
LIGHT, DARK = "light", "dark"
EMPTY_RECORD = {"keep": [], "add": [], "exemptions": [], "removed": [], "baseline_inventory": {}, "rounds": []}


def is_local_address(address: str) -> bool:
    parts = urlsplit(address)
    if parts.scheme == "file":
        return parts.hostname in (None, "", "localhost")
    if parts.scheme not in ("http", "https"):
        return False
    host = parts.hostname or ""
    return host in LOCAL_NAMES or host.endswith(LOCAL_SUFFIXES)


def _file_name(address: str, width: int, theme: str) -> str:
    path = urlsplit(address).path.rstrip("/").rsplit("/", 1)[-1] or "home"
    return f"{re.sub(r'[^A-Za-z0-9_-]+', '-', path)}-{width}-{theme}.png"


def measure_page(browser: br.Browser, address: str, width: int, theme: str, output: Path) -> dict:
    """Opens the page at the given width and theme, measures it and saves a full-page image."""
    mobile = width < MOBILE_LIMIT
    browser.command(
        "Emulation.setDeviceMetricsOverride", width=width, height=MOBILE_HEIGHT if mobile else DESKTOP_HEIGHT, deviceScaleFactor=1, mobile=mobile
    )
    browser.command("Emulation.setEmulatedMedia", features=[{"name": "prefers-color-scheme", "value": theme}])
    browser.open(address)
    browser.evaluate("document.fonts.ready.then(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))))")
    result = browser.evaluate(MEASURE_SCRIPT.read_text(encoding="utf-8"))
    output.mkdir(parents=True, exist_ok=True)
    image = output / _file_name(address, width, theme)
    image.write_bytes(base64.b64decode(browser.command("Page.captureScreenshot", format="png", captureBeyondViewport=True)["data"]))
    return {**result, "url": address, "width": width, "theme": theme, "image": str(image)}


def _take_measurements(browser: br.Browser, addresses: list[str], widths: list[int], output: Path) -> list[dict]:
    reports = []
    for address in addresses:
        for width in widths:
            reports.append(measure_page(browser, address, width, LIGHT, output))
        for width in [w for w in DARK_WIDTHS if w in widths]:
            reports.append(measure_page(browser, address, width, DARK, output))
    return reports


def _inventories(reports: list[dict]) -> dict:
    """The inventory at the widest screen of every page: items hidden on a narrow screen are still counted in the DOM."""
    chosen: dict[str, dict] = {}
    for report in sorted(reports, key=lambda r: r["width"]):
        if report["theme"] == LIGHT:
            chosen[report["url"]] = report["inventory"]
    return chosen


def _read_record(path: Path) -> dict:
    if not path.exists():
        return {**EMPTY_RECORD}
    return {**EMPTY_RECORD, **json.loads(path.read_text(encoding="utf-8"))}


def _preservation(record: dict, inventories: dict) -> dict:
    return {
        address: summ.compare_preservation(record["baseline_inventory"][address], inventory, record["removed"])
        for address, inventory in inventories.items()
        if address in record["baseline_inventory"]
    }


def _add_round(record: dict, summary: dict, user_note: str | None) -> dict:
    previous = record["rounds"][-1] if record["rounds"] else None
    difference = summ.compare_rounds(previous, summary)
    record["rounds"].append({
        "round": len(record["rounds"]) + 1,
        "date": datetime.date.today().isoformat(),
        "error": summary["error"],
        "warning": summary["warning"],
        "note": summary["note"],
        "exempt": summary["exempt"],
        "user_note": user_note or "",
        "keys": summary["keys"],
    })
    return difference


def _print(summary: dict, preservation: dict, difference: dict, round_no: int, output: Path) -> None:
    passed = summary["passed"] and all(p["ok"] for p in preservation.values())
    print(f"{'PASSED' if passed else 'FAILED'} | round {round_no} | error {summary['error']}, warning {summary['warning']}, "
          f"note {summary['note']}, exempt {summary['exempt']}")
    for finding in summary["findings"]:
        print(f"  {finding['severity'].upper():7} {finding['rule']} {finding['selector']} [{','.join(map(str, finding['widths']))}] {finding['detail']}")
    for address, result in preservation.items():
        print(f"Preservation {address}: " + ", ".join(f"{kind} {b}/{a}" for kind, (b, a) in result["counts"].items()))
        for lost in result["lost"]:
            print(f"  LOST {lost['type']}: {lost['name']}")
    if difference["regressed"]:
        print("REGRESSED, new findings: " + "; ".join(difference["new"]))
    if difference["fixed"]:
        print(f"Fixed: {len(difference['fixed'])}")
    for record in summary["invalid_exemptions"]:
        print(f"Exemption without a reason is invalid: {record.get('rule')}")
    for record in summary["unused_exemptions"]:
        print(f"Unused exemption: {record.get('rule')} {record.get('scope', '')}")
    for rule in summary["house_style"]:
        print(f"{rule} is exempt on many pages: write it to the project's design decisions as a house style")
    print(f"Images and summary.json: {output}")


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Measures the running page in a real browser.")
    parser.add_argument("addresses", nargs="+")
    parser.add_argument("--output", type=Path, required=True, help="folder for images and the summary")
    parser.add_argument("--record", type=Path, help="the project's design record (default: <output>/design-record.json)")
    parser.add_argument("--widths", default=",".join(map(str, DEFAULT_WIDTHS)))
    parser.add_argument("--baseline", action="store_true", help="save this measurement as the inventory before the redesign")
    parser.add_argument("--note", dest="user_note", help="the user's feedback for this round")
    parser.add_argument("--external-url", action="store_true", help="open a non-local address and the external network (only with site permission, #32)")
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    options = _arguments()
    refused = [a for a in options.addresses if not is_local_address(a)]
    if refused and not options.external_url:
        print(f"Non-local address refused: {', '.join(refused)}. With site permission use --external-url.", file=sys.stderr)
        return 2
    record_path = options.record or options.output / "design-record.json"
    record = _read_record(record_path)
    browser = br.Browser(options.output / ".browser-profile", external_network=options.external_url)
    try:
        reports = _take_measurements(browser, options.addresses, [int(w) for w in options.widths.split(",")], options.output)
    finally:
        browser.close()
    inventories = _inventories(reports)
    if options.baseline:
        record["baseline_inventory"].update(inventories)
    summary = summ.summarize(reports, record["exemptions"])
    preservation = _preservation(record, inventories)
    difference = _add_round(record, summary, options.user_note)
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    (options.output / "summary.json").write_text(json.dumps({"summary": summary, "preservation": preservation, "round_difference": difference, "reports": reports}, ensure_ascii=False, indent=2), encoding="utf-8")
    _print(summary, preservation, difference, record["rounds"][-1]["round"], options.output)
    return 0 if summary["passed"] and all(p["ok"] for p in preservation.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
