"""Embeds the dashboard page and its data sets into one local HTML file, so the page can be checked before publishing.

The file holds a small stand-in for the Data artifact runtime (`dash.data`, `dash.onData`, `dash.setLink`). A data set
whose JSON file is missing or unreadable reports the status `missing`. Open the file with `?gradual` to make the data
sets arrive one by one, 40 ms apart, as they do when published; `?tab=<id>` opens that tab.
The output stays under `_system/output/` (outside git).

Run (from the vault root):  python -I _system/dashboard_preview.py [--page PATH] [--data DIR] [--out PATH]
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I does not put the script folder on the path
from dashboard_data import DATASETS, output_folder  # noqa: E402

DEFAULT_PAGE = Path(__file__).resolve().parent / "dashboard.html"
PREVIEW_FILE = "preview.html"
GRADUAL_STEP_MS = 40

RUNTIME = """
(() => {
  const raw = JSON.parse(document.getElementById('mg-preview-data').textContent);
  const listeners = [];
  const gradual = new URLSearchParams(location.search).has('gradual');
  const arrived = new Set(gradual ? [] : Object.keys(raw));
  const state = (status, data = []) => ({ status, data });
  const notify = () => listeners.forEach((fn) => { try { fn(); } catch (error) { reportError(error); } });
  if (gradual) {
    const queue = Object.keys(raw);
    const step = () => { const id = queue.shift(); if (id === undefined) return; arrived.add(id); notify(); setTimeout(step, %(step)d); };
    addEventListener('load', () => setTimeout(step, %(step)d));
  }
  window.dash = {
    data(id) {
      if (!(id in raw) || raw[id] == null) return state('missing');
      if (!arrived.has(id)) return state('loading');
      return state('ok', Array.isArray(raw[id]) ? raw[id] : []);
    },
    onData(fn) { listeners.push(fn); fn(); },
    setLink() {},
  };
})();
""" % {"step": GRADUAL_STEP_MS}


def read_datasets(folder: Path) -> dict:
    """{data set: rows}; None for a file that is missing or is not valid JSON (the runtime reports it as missing)."""
    data = {}
    for dataset in DATASETS:
        path = folder / f"{dataset}.json"
        try:
            data[dataset] = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data[dataset] = None
    return data


def build_preview(page: str, data_folder: Path) -> str:
    """One HTML document: the data, the stand-in runtime, and the page inside <div id="dash-root">."""
    # A raw "<" in the data block ("</script>", "<!--<script") can end it early; "\\u003c" is the same text in JSON.
    data = json.dumps(read_datasets(data_folder), ensure_ascii=False).replace("<", "\\u003c")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dashboard preview</title>
<style>body {{ margin: 0; background: #0b1020; }}</style>
<script type="application/json" id="mg-preview-data">{data}</script>
<script>{RUNTIME}</script>
</head><body><div id="dash-root">
{page}
</div></body></html>
"""


def default_out() -> Path:
    return output_folder() / PREVIEW_FILE


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Builds a local preview of the dashboard page with its data.")
    parser.add_argument("--page", type=Path, default=DEFAULT_PAGE, help="dashboard page (default: dashboard.html)")
    parser.add_argument("--data", type=Path, default=None, help="folder of the data set JSON files")
    parser.add_argument("--out", type=Path, default=None, help="preview file to write")
    options = parser.parse_args(argv)
    try:
        page = options.page.read_text(encoding="utf-8")
    except OSError as error:
        print(f"dashboard page could not be read: {options.page} ({type(error).__name__})")
        return 1
    out = options.out or default_out()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_preview(page, options.data or output_folder()), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
