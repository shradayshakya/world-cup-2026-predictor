#!/usr/bin/env python3
"""Daily update pipeline (see PRD.md S8, S11). Phases 1-5: scrapers, match model, tournament simulation, injury layer."""

import json
from datetime import datetime, timezone
from pathlib import Path

from model.injuries import INJURY_EXTRACTION_MODEL, apply_to_elo, extract_injuries, resolve_and_score
from model.matches import build_matches
from model.simulate import simulate_tournament
from model.teams import TEAM_ALIASES
from scrapers.elo import (
    fetch_team_names,
    fetch_tournament_names,
    scrape_elo,
    scrape_fixtures_win_expectancy,
    scrape_recent_form,
)
from scrapers.news import scrape_headlines
from scrapers.squads import scrape_squads
from scrapers.wikipedia import scrape_wikipedia

DATA_DIR = Path(__file__).resolve().parent.parent / "public" / "data"


def _write_json(name: str, payload: dict) -> None:
    path = DATA_DIR / name
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {path}")


def main() -> None:
    now = datetime.now(timezone.utc).isoformat()

    _write_json("heartbeat.json", {"last_updated": now})

    team_names = fetch_team_names()
    tournament_names = fetch_tournament_names()

    elo = scrape_elo(team_names)
    elo["scraped_at"] = now
    _write_json("elo.json", elo)

    raw_groups, raw_matches = scrape_wikipedia()
    groups = {"scraped_at": now, "groups": raw_groups}
    results = {"scraped_at": now, "matches": raw_matches}
    _write_json("groups.json", groups)
    _write_json("results.json", results)

    wc_team_names = {entry["team"] for standings in raw_groups.values() for entry in standings}
    name_to_code = {name: code for code, name in team_names.items()}
    wc_team_codes = {name_to_code[TEAM_ALIASES.get(name, name)] for name in wc_team_names if TEAM_ALIASES.get(name, name) in name_to_code}

    form = scrape_recent_form(team_names, tournament_names, wc_team_codes)
    _write_json("form.json", {"generated_at": now, "teams": form})

    squads_path = DATA_DIR / "squads.json"
    if squads_path.exists():
        squads = json.loads(squads_path.read_text())["squads"]
    else:
        squads = scrape_squads(sorted(wc_team_names))  # "once + diff" cadence (PRD.md S7), not daily
        _write_json("squads.json", {"scraped_at": now, "squads": squads})

    headlines = scrape_headlines()
    _write_json("headlines.json", {"scraped_at": now, "headlines": headlines})
    extracted = extract_injuries(headlines, INJURY_EXTRACTION_MODEL)
    injuries = resolve_and_score(extracted, squads)
    _write_json("injuries.json", {"generated_at": now, "teams": injuries})
    adjusted_elo = apply_to_elo(elo, injuries)

    win_expectancy = scrape_fixtures_win_expectancy(team_names)
    matches = build_matches(adjusted_elo, groups, results, win_expectancy)
    matches["generated_at"] = now
    _write_json("matches.json", matches)

    simulation = simulate_tournament(adjusted_elo, groups, results, matches)
    probabilities = simulation["probabilities"]
    probabilities["generated_at"] = now
    _write_json("probabilities.json", probabilities)

    bracket = simulation["bracket"]
    bracket["generated_at"] = now
    _write_json("bracket.json", bracket)


if __name__ == "__main__":
    main()
