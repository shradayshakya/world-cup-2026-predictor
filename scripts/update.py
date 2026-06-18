#!/usr/bin/env python3
"""Daily update pipeline (see PRD.md S8, S11). Phases 1-2: scrapers + Poisson-Elo match model."""

import json
from datetime import datetime, timezone
from pathlib import Path

from model.matches import build_matches
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

    raw_groups, raw_matches = scrape_wikipedia()
    groups = {"scraped_at": now, "groups": raw_groups}
    results = {"scraped_at": now, "matches": raw_matches}
    _write_json("groups.json", groups)
    _write_json("results.json", results)

    matches = build_matches(elo, groups, results)
    matches["generated_at"] = now
    _write_json("matches.json", matches)


if __name__ == "__main__":
    main()
