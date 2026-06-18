"""Joins elo.json + groups.json + results.json into matches.json predictions (PRD.md S11 Phase 2)."""

from .poisson import expected_goals, score_grid, summarize
from .teams import resolve_rating


def _elo_win_expectancy(home: str, away: str, win_expectancy: dict):
    """win_expectancy maps (home_name, away_name) -> eloratings.net's published home win-expectancy %.

    This is their "expected score" metric (win=1, draw=0.5, loss=0), not a 3-way W/D/L split like
    our own model -- shown for comparison ("according to Elo" vs "what we calculated"), see CLAUDE.md.
    """
    if (home, away) in win_expectancy:
        home_pct = win_expectancy[(home, away)]
    elif (away, home) in win_expectancy:
        home_pct = 100 - win_expectancy[(away, home)]
    else:
        return None
    return {"home": home_pct, "away": round(100 - home_pct, 1)}


def build_matches(elo: dict, groups: dict, results: dict, win_expectancy: dict = None) -> dict:
    win_expectancy = win_expectancy or {}
    elo_by_name = {t["name"]: t["rating"] for t in elo["teams"]}
    host_by_team = {
        entry["team"]: entry["host"]
        for standings in groups["groups"].values()
        for entry in standings
    }

    matches = []
    skipped_unresolved = 0
    for match in results["matches"]:
        if match["played"]:
            continue

        home_rating = resolve_rating(match["home_team"], elo_by_name)
        away_rating = resolve_rating(match["away_team"], elo_by_name)
        if home_rating is None or away_rating is None:
            skipped_unresolved += 1
            continue

        lambda_home, lambda_away = expected_goals(
            home_rating,
            away_rating,
            host_by_team.get(match["home_team"], False),
            host_by_team.get(match["away_team"], False),
        )
        prediction = summarize(score_grid(lambda_home, lambda_away))

        matches.append(
            {
                "round": match["round"],
                "group": match["group"],
                "date": match["date"],
                "home_team": match["home_team"],
                "away_team": match["away_team"],
                "venue": match["venue"],
                "prediction": prediction,
                "elo_win_expectancy": _elo_win_expectancy(match["home_team"], match["away_team"], win_expectancy),
            }
        )

    if skipped_unresolved:
        print(f"matches: skipped {skipped_unresolved} fixtures with unresolved team slots (e.g. knockout TBDs)")

    return {"matches": matches}
