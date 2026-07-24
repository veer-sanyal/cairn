#!/usr/bin/env python3
"""Cairn validator ('lint'). Report-only: always exit 0. --json for machine output."""
import json, re, sys, os, time, fnmatch, datetime
from cairn_lib import find_root, manifest, parse_date, pos_int, read_text_safe

SENTINEL_TTL_H = 24
STAMP = re.compile(r"Last reconciled: (\d{4}-\d{2}-\d{2})")
REFRESH = re.compile(r"Refresh-by: (\d{4}-\d{2}-\d{2})")
RESEARCHED = re.compile(r"— researched (\d{4}-\d{2}-\d{2})")
CENSUS_STALE_DAYS = 180
ANNUAL_CEILING_DAYS = 365

def cap_for(rel, caps):
    for pat, cap in caps.items():
        if rel == pat or fnmatch.fnmatch(rel, pat):
            return cap
    return None

def _dict(x):
    return x if isinstance(x, dict) else {}

def sweeps(root, m, today):
    """Doctrine-expiry sweeps (P22: structural triggers, never model memory). All soft.

    Every section is independently type-robust: a malformed manifest field (census as a
    list, a non-iso date, metrics not a dict) or an impossible date must NEVER suppress
    another section's findings — that is the entire purpose of the sweep. All date parsing
    goes through cairn_lib.parse_date (returns None on any malformed input); dict-typed
    fields go through _dict(); day-count fields through pos_int (which excludes bool)."""
    out = []
    cadence = _dict(m.get("cadence"))
    research = root / "docs" / "RESEARCH.md"
    if research.is_file():
        text = read_text_safe(research)
        for d in REFRESH.findall(text):
            dd = parse_date(d)
            if dd is not None and dd < today:
                out.append({"check": "research_expired", "level": "soft",
                            "file": "docs/RESEARCH.md", "refresh_by": d})
        for d in RESEARCHED.findall(text):
            dd = parse_date(d)
            if dd is not None and (today - dd).days > ANNUAL_CEILING_DAYS:
                out.append({"check": "research_annual_ceiling", "level": "soft",
                            "file": "docs/RESEARCH.md", "researched": d})
    census = m.get("census")
    if isinstance(census, dict) and census:
        dd = parse_date(census.get("date"))
        if dd is None:
            out.append({"check": "census_stale", "level": "soft", "detail": "unreadable census date"})
        elif (today - dd).days > CENSUS_STALE_DAYS:
            out.append({"check": "census_stale", "level": "soft", "age_days": (today - dd).days})
    elif census and not isinstance(census, dict):  # present but wrong type — surface it
        out.append({"check": "census_stale", "level": "soft", "detail": "census is not an object"})
    elif m.get("data_paths"):
        # covers both absent census and an empty {} — never populated is the same finding
        out.append({"check": "census_stale", "level": "soft",
                    "detail": "data_paths recorded but no census"})
    last = _dict(m.get("metrics")).get("last_revalidated")
    days = pos_int(cadence.get("proxy_revalidation_days"))
    if days:
        dd = parse_date(last)
        if dd is not None and (today - dd).days > days:
            out.append({"check": "proxy_revalidation_due", "level": "soft",
                        "age_days": (today - dd).days})
    smap = root / "docs" / "SYSTEM-MAP.md"
    if smap.is_file():
        stamp = STAMP.search(read_text_safe(smap))
        review_days = pos_int(cadence.get("review_days"))
        limit = 2 * review_days if review_days else 60
        if not stamp:
            out.append({"check": "system_map", "level": "soft",
                        "file": "docs/SYSTEM-MAP.md", "detail": "no 'Last reconciled:' stamp"})
        else:
            dd = parse_date(stamp.group(1))
            if dd is not None and (today - dd).days > limit:
                out.append({"check": "system_map", "level": "soft",
                            "file": "docs/SYSTEM-MAP.md", "age_days": (today - dd).days})
    return out

def run(root):
    m = manifest(root)
    out = []
    # a top-level "concluded" (misplaced conclude.md edit) is silently ignored by every
    # reader — the user thinks the instance is concluded; the system keeps nagging
    if "concluded" in m:
        out.append({"check": "misplaced_concluded", "level": "soft", "file": "manifest.json",
                    "detail": "top-level 'concluded' is ignored — it belongs at instance.concluded"})
    caps = m.get("caps", {})
    for rel in ["CLAUDE.md", "state/HOT.md",
                *[f"state/working/{p.name}" for p in (root / "state" / "working").glob("*") if p.is_file()]]:
        p = root / rel
        cap = cap_for(rel, caps)
        if p.is_file() and cap:
            size = p.stat().st_size
            if size > cap.get("hard", 1 << 30):
                out.append({"check": "size_cap", "level": "hard", "file": rel, "size": size, "cap": cap["hard"]})
            elif size > cap.get("soft", 1 << 30):
                out.append({"check": "size_cap", "level": "soft", "file": rel, "size": size, "cap": cap["soft"]})
    hot = root / "state" / "HOT.md"
    stamp = STAMP.search(read_text_safe(hot)) if hot.is_file() else None
    if not stamp:
        out.append({"check": "staleness", "level": "hard", "file": "state/HOT.md", "detail": "no 'Last reconciled:' stamp"})
    else:
        # A well-formed-but-impossible date (2026-02-30) must not blank out every other
        # finding — and only a bad DATE may be reported as unparseable: the limit lookup
        # is guarded separately so a malformed trigger days value can't be mislabeled.
        d = parse_date(stamp.group(1))
        if d is None:
            out.append({"check": "staleness", "level": "hard", "file": "state/HOT.md",
                        "detail": "unparseable 'Last reconciled:' date"})
        else:
            age = (datetime.date.today() - d).days
            triggers = m.get("triggers", [])
            triggers = triggers if isinstance(triggers, list) else []
            limit = next((pos_int(t.get("days")) for t in triggers
                          if isinstance(t, dict) and t.get("template") == "staleness_escalation"), None) or 14
            if age > limit:
                out.append({"check": "staleness", "level": "soft", "file": "state/HOT.md", "age_days": age})
    for rel in ["state/archive.jsonl", "telemetry/events.jsonl"]:
        p = root / rel
        if p.is_file():
            for i, line in enumerate(read_text_safe(p).splitlines(), 1):
                if line.strip():
                    try:
                        json.loads(line)
                    except json.JSONDecodeError:
                        out.append({"check": "jsonl_integrity", "level": "hard", "file": rel, "line": i})
                        break
    s = root / ".cairn" / "review-in-progress"
    if s.exists() and time.time() - s.stat().st_mtime > SENTINEL_TTL_H * 3600:
        out.append({"check": "stale_sentinel", "level": "soft", "file": ".cairn/review-in-progress"})
    try:
        out += sweeps(root, m, datetime.date.today())
    except Exception:
        pass  # ponytail: sweeps never break the validator's other findings
    return out

def main():
    try:
        root = find_root(os.getcwd())
        if not root:
            print("[]" if "--json" in sys.argv else "not a cairn instance")
            return
        out = run(root)
        if "--json" in sys.argv:
            print(json.dumps(out))
        else:
            for f in out:
                print(f"[{f['level']}] {f['check']}: {f.get('file','')} {f.get('detail','')}".strip())
            if not out:
                print("validator: clean")
    except Exception:
        print("[]" if "--json" in sys.argv else "validator error (fail-soft)")

if __name__ == "__main__":
    main()
