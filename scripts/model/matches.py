"""Joins elo.json + groups.json + results.json into matches.json predictions (PRD.md S11 Phase 2)."""

from .poisson import expected_goals, score_grid, summarize
from .teams import resolve_rating


def build_matches(elo: dict, groups: dict, results: dict) -> dict:
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
            }
        )

    if skipped_unresolved:
        print(f"matches: skipped {skipped_unresolved} fixtures with unresolved team slots (e.g. knockout TBDs)")

    return {"matches": matches}
