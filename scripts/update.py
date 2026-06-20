#!/usr/bin/env python3
"""Daily update pipeline (see PRD.md S8, S11). Phases 1-6 + 5c: scrapers, match model, tournament simulation, injury layer, editorial layer, calibration + change tracking, parser fallback, top scorer model."""

import json
from datetime import datetime, timezone
from pathlib import Path

from model.calibration import merge_into_log, score_resolved_matches
from model.changes import compute_bracket_changes, compute_match_changes, compute_team_changes
from model.injuries import INJURY_EXTRACTION_MODEL, apply_to_elo, extract_injuries, resolve_and_score
from model.matches import build_matches
from model.movers import compute_movers, generate_movers_commentary
from model.previews import generate_previews
from model.simulate import simulate_tournament
from model.teams import TEAM_ALIASES
from model.top_scorers import compute_top_scorers
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

    # Read before any writes this run -- this *is* "yesterday's" snapshot, since each
    # day's run starts with the prior run's committed output still on disk (PRD.md S6.4
    # movers commentary needs a day-over-day diff; see CLAUDE.md for why no separate
    # snapshot file is needed).
    probabilities_path = DATA_DIR / "probabilities.json"
    previous_probabilities = json.loads(probabilities_path.read_text())["teams"] if probabilities_path.exists() else {}

    # matches.json only ever holds unplayed matches -- a match's prediction would be
    # lost with no audit trail the moment it flips to played, unless captured here
    # before this run's fresh build_matches() overwrites the file (PRD.md S10).
    matches_path = DATA_DIR / "matches.json"
    previous_matches = json.loads(matches_path.read_text()) if matches_path.exists() else {"matches": []}

    calibration_log_path = DATA_DIR / "calibration_log.json"
    existing_calibration_log = json.loads(calibration_log_path.read_text()) if calibration_log_path.exists() else {}

    bracket_path = DATA_DIR / "bracket.json"
    previous_bracket = json.loads(bracket_path.read_text()) if bracket_path.exists() else {}

    # The probability-change arrows (PRD.md S5.1a) compare against this baseline, not
    # against previous_probabilities/previous_matches above -- it only advances when a
    # real match resolves (see newly_resolved below), so a run with no new result keeps
    # comparing against the same fixed point instead of resetting to "no change" against
    # whatever the immediately preceding (possibly also no-op) run happened to produce.
    # No baseline file yet (first run with this mechanism) bootstraps from the immediate
    # previous snapshot, same as the old day-over-day behavior, just once.
    change_baseline_path = DATA_DIR / "change_baseline.json"
    if change_baseline_path.exists():
        change_baseline = json.loads(change_baseline_path.read_text())
        baseline_teams = change_baseline["teams"]
        baseline_matches = change_baseline["matches"]
        baseline_bracket = change_baseline.get("bracket", {})  # .get: older baseline files predate this key
    else:
        baseline_teams = previous_probabilities
        baseline_matches = previous_matches
        baseline_bracket = previous_bracket

    _write_json("heartbeat.json", {"last_updated": now})

    team_names = fetch_team_names()
    tournament_names = fetch_tournament_names()

    elo = scrape_elo(team_names)
    elo["scraped_at"] = now
    _write_json("elo.json", elo)

    raw_groups, raw_matches, wiki_issues = scrape_wikipedia(INJURY_EXTRACTION_MODEL)
    groups = {"scraped_at": now, "groups": raw_groups}
    results = {"scraped_at": now, "matches": raw_matches}
    _write_json("groups.json", groups)
    _write_json("results.json", results)

    newly_resolved = score_resolved_matches(previous_matches, results)
    calibration_log = merge_into_log(existing_calibration_log, newly_resolved)
    _write_json("calibration_log.json", calibration_log)

    wc_team_names = {entry["team"] for standings in raw_groups.values() for entry in standings}
    name_to_code = {name: code for code, name in team_names.items()}
    wc_team_codes = {name_to_code[TEAM_ALIASES.get(name, name)] for name in wc_team_names if TEAM_ALIASES.get(name, name) in name_to_code}

    form = scrape_recent_form(team_names, tournament_names, wc_team_codes)
    _write_json("form.json", {"generated_at": now, "teams": form})

    squads_path = DATA_DIR / "squads.json"
    squad_issues = []
    if squads_path.exists():
        squads = json.loads(squads_path.read_text())["squads"]
    else:
        squads, squad_issues = scrape_squads(sorted(wc_team_names), INJURY_EXTRACTION_MODEL)  # "once + diff" cadence (PRD.md S7), not daily
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

    top_scorers = compute_top_scorers(simulation["team_goals"], squads, injuries)
    _write_json("top_scorers.json", {"generated_at": now, "scorers": top_scorers})

    movers = compute_movers(previous_probabilities, probabilities["teams"])
    movers = generate_movers_commentary(movers, raw_groups, results, injuries, now[:10])
    _write_json("movers.json", {"generated_at": now, "movers": movers})

    previews = generate_previews(matches, adjusted_elo, form, injuries)
    _write_json("previews.json", {"generated_at": now, "previews": previews})

    probability_changes = {
        "teams": compute_team_changes(baseline_teams, probabilities["teams"]),
        "matches": compute_match_changes(baseline_matches, matches),
        "bracket": compute_bracket_changes(baseline_bracket, bracket),
    }
    _write_json("probability_changes.json", {"generated_at": now, **probability_changes})

    # Advance the baseline only when a real match resolved this run -- a no-op run
    # (no new result) must not overwrite it, or the next no-op run after that would
    # diff against "no change" and silently lose today's real movement.
    if newly_resolved:
        _write_json(
            "change_baseline.json", {"generated_at": now, "teams": probabilities["teams"], "matches": matches, "bracket": bracket}
        )

    _write_json("maintenance.json", {"generated_at": now, "issues": wiki_issues + squad_issues})


if __name__ == "__main__":
    main()
