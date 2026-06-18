#!/usr/bin/env python3
"""Daily update pipeline (see PRD.md S8, S11). Phase 1: elo + Wikipedia scrapers."""

import json
from datetime import datetime, timezone
from pathlib import Path

from scrapers.elo import scrape_elo
from scrapers.wikipedia import scrape_wikipedia

DATA_DIR = Path(__file__).resolve().parent.parent / "public" / "data"


def _write_json(name: str, payload: dict) -> None:
    path = DATA_DIR / name
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {path}")


def main() -> None:
    now = datetime.now(timezone.utc).isoformat()

    _write_json("heartbeat.json", {"last_updated": now})

    elo = scrape_elo()
    elo["scraped_at"] = now
    _write_json("elo.json", elo)

    groups, matches = scrape_wikipedia()
    _write_json("groups.json", {"scraped_at": now, "groups": groups})
    _write_json("results.json", {"scraped_at": now, "matches": matches})


if __name__ == "__main__":
    main()
