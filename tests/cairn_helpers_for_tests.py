import json, datetime
from pathlib import Path

def seed_event(root, days_ago=0, **fields):
    ts = (datetime.datetime.now(datetime.timezone.utc)
          - datetime.timedelta(days=days_ago)).isoformat(timespec="seconds")
    with open(Path(root) / "telemetry" / "events.jsonl", "a") as f:
        f.write(json.dumps({"ts": ts, **fields}) + "\n")
