"""Predicted top scorer leaderboard (PRD.md S6.5): each team's Monte-Carlo-averaged
total tournament goals (model/simulate.py's team_goals output) distributed to players
by their historical (career, pre-tournament) share of the team's total squad goals,
scaled by an availability factor from the injury layer.

We don't scrape per-match goal scorers -- Phase 1's "one fetch per source" scraping
discipline never added a per-match-page scraper (see CLAUDE.md) -- so this has no
visibility into who has *actually* scored at WC26 so far. It's purely a forward-looking
estimate from pre-tournament career scoring history, not a cumulative real tally.
Documented v1 simplification, same "no fallback guess" spirit as injuries.py's strict
single-candidate fuzzy match.
"""

TOP_SCORERS_LIMIT = 50
AVAILABILITY_FACTOR = {"out": 0.0, "suspended": 0.0, "doubt": 0.5}


def compute_top_scorers(team_goals: dict, squads: dict, injuries: dict) -> list:
    scorers = []
    for team, squad in squads.items():
        total_historical_goals = sum(p["goals"] for p in squad)
        if total_historical_goals == 0:
            continue  # no historical scoring signal to distribute -- not a guess

        absences = injuries.get(team, {}).get("absences", [])
        status_by_player = {a["player"]: a["status"] for a in absences}

        for p in squad:
            if p["goals"] == 0:
                continue
            share = p["goals"] / total_historical_goals
            availability = AVAILABILITY_FACTOR.get(status_by_player.get(p["name"]), 1.0)
            predicted_goals = team_goals.get(team, 0) * share * availability
            if predicted_goals <= 0:
                continue
            scorers.append(
                {
                    "player": p["name"],
                    "team": team,
                    "position": p["position"],
                    "historical_goals": p["goals"],
                    "predicted_goals": round(predicted_goals, 2),
                }
            )

    scorers.sort(key=lambda s: -s["predicted_goals"])
    return scorers[:TOP_SCORERS_LIMIT]
