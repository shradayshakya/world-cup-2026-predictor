#!/usr/bin/env python3
"""Phase 0 stub for the daily update pipeline (see PRD.md S8, S11)."""

import json
from datetime import datetime, timezone
from pathlib import Path

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "public" / "data" / "heartbeat.json"


def main() -> None:
    payload = {"last_updated": datetime.now(timezone.utc).isoformat()}
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
