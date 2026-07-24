#!/usr/bin/env python3
"""Cairn validator ('lint'). Report-only: always exit 0. --json for machine output."""
import json, re, sys, os, time, fnmatch, datetime
from cairn_lib import find_root, manifest

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
    another section's findings — that is the entire purpose of the sweep. Date parsers
    catch (ValueError, TypeError) because fromisoformat raises TypeError on non-str input;
    dict-typed fields go through _dict()."""
    out = []
    research = root / "docs" / "RESEARCH.md"
    if research.is_file():
        text = research.read_text()
        for d in REFRESH.findall(text):
            try:
                if datetime.date.fromisoformat(d) < today:
                    out.append({"check": "research_expired", "level": "soft",
                                "file": "docs/RESEARCH.md", "refresh_by": d})
            except (ValueError, TypeError):
                pass
        for d in RESEARCHED.findall(text):
            try:
                if (today - datetime.date.fromisoformat(d)).days > ANNUAL_CEILING_DAYS:
                    out.append({"check": "research_annual_ceiling", "level": "soft",
                                "file": "docs/RESEARCH.md", "researched": d})
            except (ValueError, TypeError):
                pass
    census = m.get("census")
    if isinstance(census, dict):
        try:
            age = (today - datetime.date.fromisoformat(census.get("date", ""))).days
            if age > CENSUS_STALE_DAYS:
                out.append({"check": "census_stale", "level": "soft", "age_days": age})
        except (ValueError, TypeError):
            out.append({"check": "census_stale", "level": "soft", "detail": "unreadable census date"})
    elif census:  # present but wrong type — surface it, don't silently skip
        out.append({"check": "census_stale", "level": "soft", "detail": "census is not an object"})
    elif m.get("data_paths"):
        out.append({"check": "census_stale", "level": "soft",
                    "detail": "data_paths recorded but no census"})
    last = _dict(m.get("metrics")).get("last_revalidated")
    days = _dict(m.get("cadence")).get("proxy_revalidation_days")
    if last and isinstance(days, int) and days > 0:
        try:
            age = (today - datetime.date.fromisoformat(last)).days
            if age > days:
                out.append({"check": "proxy_revalidation_due", "level": "soft", "age_days": age})
        except (ValueError, TypeError):
            pass
    smap = root / "docs" / "SYSTEM-MAP.md"
    if smap.is_file():
        stamp = STAMP.search(smap.read_text())
        review_days = _dict(m.get("cadence")).get("review_days", 30)
        limit = 2 * review_days if isinstance(review_days, int) and review_days > 0 else 60
        if not stamp:
            out.append({"check": "system_map", "level": "soft",
                        "file": "docs/SYSTEM-MAP.md", "detail": "no 'Last reconciled:' stamp"})
        else:
            try:
                age = (today - datetime.date.fromisoformat(stamp.group(1))).days
                if age > limit:
                    out.append({"check": "system_map", "level": "soft",
                                "file": "docs/SYSTEM-MAP.md", "age_days": age})
            except (ValueError, TypeError):
                pass
    return out

def run(root):
    m = manifest(root)
    out = []
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
    stamp = STAMP.search(hot.read_text()) if hot.is_file() else None
    if not stamp:
        out.append({"check": "staleness", "level": "hard", "file": "state/HOT.md", "detail": "no 'Last reconciled:' stamp"})
    else:
        # A well-formed-but-impossible date (2026-02-30) must not blank out every other
        # finding: parse defensively and report the broken stamp as its own hard finding.
        try:
            age = (datetime.date.today() - datetime.date.fromisoformat(stamp.group(1))).days
            triggers = m.get("triggers", [])
            triggers = triggers if isinstance(triggers, list) else []
            limit = next((t.get("days", 14) for t in triggers
                          if isinstance(t, dict) and t.get("template") == "staleness_escalation"), 14)
            if age > limit:
                out.append({"check": "staleness", "level": "soft", "file": "state/HOT.md", "age_days": age})
        except (ValueError, TypeError):
            out.append({"check": "staleness", "level": "hard", "file": "state/HOT.md",
                        "detail": "unparseable 'Last reconciled:' date"})
    for rel in ["state/archive.jsonl", "telemetry/events.jsonl"]:
        p = root / rel
        if p.is_file():
            for i, line in enumerate(p.read_text().splitlines(), 1):
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
