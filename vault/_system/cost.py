"""Local cost meter: tokens and API-equivalent cost per session and per subagent, from the Claude Code transcripts on
this computer.

Why: cost was never measured. Every message in a transcript carries its token usage (`message.usage`); the cost is
computed without sending any data out. The desktop app does not fill its own cost record (`cost-state`) in
interactive chats, so the prices come from the `prices` table in `config.json` (its source and date are there).

Usage (from the vault root):
  python _system/cost.py             last 7 days: total per day and the most expensive sessions (today included)
  python _system/cost.py --days 30   last 30 days

Limits: the same message repeats on several lines of a transcript; it is deduplicated by (message id, request id).
The cost of a model missing from the price table is not computed (not invented); it shows in the `unpriced_models`
field. Haiku's separate price above 100k prompt tokens is not kept. The result is the API-price equivalent; it is not
an amount paid on top of a subscription.
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the -I flag does not add the script folder to the path
import session_mode as sm  # noqa: E402
from common import CONFIG_FILE  # noqa: E402

PROJECTS = Path.home() / ".claude" / "projects"
WRITE_5MIN, WRITE_1HOUR = 1.25, 2.0          # cache write multipliers (relative to the input price)
MILLION = 1_000_000
SESSION, AGENT = "session", "agent"


def read_prices(config: Path = CONFIG_FILE) -> dict:
    return json.loads(config.read_text(encoding="utf-8")).get("prices", {}).get("models", {})


def folder_name(transcript_folder: str) -> str:
    """'C--Users-name-Desktop-My-Project' -> 'My-Project': the full path on the computer is never shown."""
    return re.sub(r"^[A-Za-z]--Users-[^-]+-(?:Desktop-)?", "", transcript_folder) or transcript_folder


def local_date(stamp: str) -> str:
    """ISO time stamp -> local calendar date (after local midnight UTC can still show the previous day)."""
    try:
        return datetime.fromisoformat(stamp.replace("Z", "+00:00")).astimezone().date().isoformat()
    except ValueError:
        return stamp[:10]


def usages(path: Path) -> tuple[dict, str]:
    """Day -> model -> deduplicated token totals of a transcript, and its title.

    Split by day: if the whole cost of a session that ran for weeks went to its last day, daily totals would mislead."""
    last_usage: dict[tuple, tuple[str, str, dict]] = {}
    title = ""
    with path.open(encoding="utf-8") as transcript:
        for raw in transcript:
            try:
                line = json.loads(raw)
            except ValueError:
                continue
            if line.get("type") == "custom-title":
                title = str(line.get("customTitle") or "").strip() or title
            elif line.get("type") == "agent-name" and not title:
                title = str(line.get("agentName") or "").strip()
            message = line.get("message")
            if line.get("type") != "assistant" or not isinstance(message, dict) or not message.get("usage"):
                continue
            day = local_date(str(line.get("timestamp") or ""))
            last_usage[(message.get("id"), line.get("requestId"))] = (day, str(message.get("model") or ""), message["usage"])
    days: dict[str, dict] = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for day, model, usage in last_usage.values():
        breakdown = usage.get("cache_creation") or {}
        write_1h = int(breakdown.get("ephemeral_1h_input_tokens") or 0)
        t = days[day][model]
        t["input"] += int(usage.get("input_tokens") or 0)
        t["output"] += int(usage.get("output_tokens") or 0)
        t["cache_read"] += int(usage.get("cache_read_input_tokens") or 0)
        t["write_1h"] += write_1h
        t["write_5min"] += int(usage.get("cache_creation_input_tokens") or 0) - write_1h
    return days, title


def compute_cost(totals: dict, prices: dict) -> tuple[float, list[str]]:
    """USD from the token totals per model; models with an unknown price are listed apart (their cost is not invented)."""
    usd, unpriced = 0.0, []
    for model, t in totals.items():
        if not any(t.values()):
            continue
        p = prices.get(model)
        if not p:
            unpriced.append(model)
            continue
        usd += (t["input"] * p["input"] + t["output"] * p["output"] + t["cache_read"] * p["cache_read"]
                + t["write_5min"] * p["input"] * WRITE_5MIN + t["write_1h"] * p["input"] * WRITE_1HOUR) / MILLION
    return usd, unpriced


def row(kind: str, key: str, totals: dict, prices: dict, **fields) -> dict:
    usd, unpriced = compute_cost(totals, prices)
    main_model = max(totals, key=lambda m: totals[m]["output"], default="")
    return {"key": key, "kind": kind, "model": main_model,
            "input": sum(t["input"] for t in totals.values()), "output": sum(t["output"] for t in totals.values()),
            "cache_read": sum(t["cache_read"] for t in totals.values()),
            "cache_write": sum(t["write_5min"] + t["write_1h"] for t in totals.values()),
            "cost_usd": round(usd, 6), "unpriced_models": ", ".join(unpriced), **fields}


def rows(projects: Path = PROJECTS, prices: dict | None = None) -> list[dict]:
    """One row for every day of every session and of every subagent run."""
    prices = read_prices() if prices is None else prices
    result = []
    unrecorded = sm.unrecorded_filter()   # the title and folder of a temporary chat appear nowhere
    for path in sorted(projects.glob("*/*.jsonl")):
        if unrecorded(path.stem):
            continue
        days, title = usages(path)
        sid, chat = path.stem, title or folder_name(path.parent.name)
        folder = folder_name(path.parent.name)
        for day, totals in sorted(days.items()):
            result.append(row(SESSION, f"{SESSION}:{sid}:{day}", totals, prices, chat=chat, folder=folder,
                              agent="", date=day))
        for agent_path in sorted((path.parent / sid / "subagents").glob("agent-*.jsonl")):
            meta_path = agent_path.with_suffix(".meta.json")
            meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.is_file() else {}
            agent_days, _ = usages(agent_path)
            for day, totals in sorted(agent_days.items()):
                result.append(row(AGENT, f"{AGENT}:{sid}:{agent_path.stem}:{day}", totals, prices, chat=chat,
                                  folder=folder, agent=str(meta.get("agentType") or "unknown"), date=day))
    return result


def finished_rows(all_rows: list[dict]) -> list[dict]:
    """Only rows of days that ended before today: a running session changes with every message, so its row is never final."""
    today = date.today().isoformat()
    chosen = sorted((r for r in all_rows if r["date"] < today), key=lambda r: (r["date"], r["key"]))
    return [{**r, "order": i} for i, r in enumerate(chosen)]


def print_summary(all_rows: list[dict], days: int) -> None:
    start = (date.today() - timedelta(days=days - 1)).isoformat()
    period = [r for r in all_rows if r["date"] >= start]
    daily: dict[str, float] = defaultdict(float)
    for r in period:
        if r["kind"] == SESSION:
            daily[r["date"]] += r["cost_usd"]
    agents: dict[str, float] = defaultdict(float)
    for r in period:
        if r["kind"] == AGENT:
            agents[r["agent"]] += r["cost_usd"]
    print(f"Last {days} days (API-price equivalent; session totals do not include subagents)")
    for d in sorted(daily):
        print(f"  {d}  ${daily[d]:8.2f}")
    print(f"  Total: sessions ${sum(daily.values()):.2f} · subagents ${sum(agents.values()):.2f}")
    for agent, usd in sorted(agents.items(), key=lambda x: -x[1]):
        print(f"    agent {agent:14} ${usd:.2f}")
    sessions: dict[str, list] = defaultdict(lambda: [0.0, "", set()])   # session -> [usd, chat, days]
    for r in period:
        if r["kind"] == SESSION:
            s = sessions[r["key"].rsplit(":", 1)[0]]
            s[0] += r["cost_usd"]
            s[1] = r["chat"]
            s[2].add(r["date"])
    print("Most expensive sessions (their share in this period):")
    for usd, chat, session_days in sorted(sessions.values(), key=lambda s: -s[0])[:8]:
        print(f"  ${usd:8.2f}  {len(session_days)} days  {chat[:50]}")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    p.add_argument("--days", type=int, default=7)
    print_summary(rows(), p.parse_args().days)


if __name__ == "__main__":
    main()
