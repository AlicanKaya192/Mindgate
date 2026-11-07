"""Merges measurement reports; applies exemptions, the preservation counter and the round comparison. Pure computation:
no file, network or browser."""
from collections import Counter

SEVERITY_ORDER = {"error": 0, "warning": 1, "note": 2}
HOUSE_STYLE_PAGES = 3


def _is_valid(record: dict) -> bool:
    return bool((record.get("reason") or "").strip())


def _find_exemption(finding: dict, exemptions: list[dict]) -> dict | None:
    for exemption in exemptions:
        if exemption.get("rule") == finding["rule"] and (exemption.get("scope") or "") in finding["selector"]:
            return exemption
    return None


def _merge(reports: list[dict]) -> list[dict]:
    merged: dict[tuple, dict] = {}
    for report in reports:
        for finding in report["findings"]:
            key = (report["url"], finding["rule"], finding["selector"], finding["severity"])
            record = merged.setdefault(key, {**finding, "url": report["url"], "widths": set(), "themes": set()})
            record["widths"].add(report["width"])
            record["themes"].add(report["theme"])
    ordered = sorted(merged.values(), key=lambda f: (SEVERITY_ORDER[f["severity"]], f["rule"], f["url"], f["selector"]))
    return [{**f, "widths": sorted(f["widths"]), "themes": sorted(f["themes"])} for f in ordered]


def summarize(reports: list[dict], exemptions: list[dict]) -> dict:
    """Reduces the reports to one summary. An exemption without a reason is ignored and fails the check."""
    valid = [e for e in exemptions if _is_valid(e)]
    invalid = [e for e in exemptions if not _is_valid(e)]
    remaining, exempt, used = [], [], []
    for finding in _merge(reports):
        exemption = _find_exemption(finding, valid)
        if exemption is None:
            remaining.append(finding)
            continue
        exempt.append(finding)
        used.append(id(exemption))
    pages = Counter()
    for rule, url in {(f["rule"], f["url"]) for f in exempt}:
        pages[rule] += 1
    counts = Counter(f["severity"] for f in remaining)
    return {
        "error": counts["error"],
        "warning": counts["warning"],
        "note": counts["note"],
        "exempt": len(exempt),
        "passed": counts["error"] == 0 and not invalid,
        "findings": remaining,
        "exempt_findings": exempt,
        "invalid_exemptions": invalid,
        "unused_exemptions": [e for e in valid if id(e) not in used],
        "house_style": sorted(r for r, number in pages.items() if number >= HOUSE_STYLE_PAGES),
        "keys": sorted(f"{f['url']}|{f['rule']}|{f['selector']}" for f in remaining if f["severity"] != "note"),
    }


def _differences(before: Counter, after: Counter) -> list[str]:
    return sorted((before - after).elements())


def compare_preservation(before: dict, after: dict, removed: list[dict]) -> dict:
    """Compares the inventories item by item: every vanished item is reported by name; with a written reason it is not a loss."""
    justified_names = Counter((r.get("type"), r.get("name")) for r in removed if _is_valid(r))
    result = {"counts": {}, "lost": [], "justified": [], "added": []}
    for kind in sorted(set(before) | set(after)):
        old, new = Counter(before.get(kind, [])), Counter(after.get(kind, []))
        result["counts"][kind] = [sum(old.values()), sum(new.values())]
        for item in _differences(old, new):
            if justified_names[(kind, item)] > 0:
                justified_names[(kind, item)] -= 1
                result["justified"].append({"type": kind, "name": item})
            else:
                result["lost"].append({"type": kind, "name": item})
        result["added"] += [{"type": kind, "name": item} for item in _differences(new, old)]
    result["ok"] = not result["lost"]
    return result


def compare_rounds(previous: dict | None, current: dict) -> dict:
    """New and fixed errors and warnings compared with the previous round. A new finding is a regression."""
    if previous is None:
        return {"new": [], "fixed": [], "regressed": False}
    old, new = set(previous["keys"]), set(current["keys"])
    return {"new": sorted(new - old), "fixed": sorted(old - new), "regressed": bool(new - old)}
