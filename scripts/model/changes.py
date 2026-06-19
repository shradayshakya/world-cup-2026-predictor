"""Day-over-day probability-change arrows (PRD.md S5.1a): "no arrow if change is
< 0.1pp (avoid noise from Monte Carlo jitter)." Generalizes the diffing movers.py
already does for won_tournament to every stage key, and to per-match W/D/L too.
"""

CHANGE_THRESHOLD_PP = 0.1


def compute_team_changes(previous_teams: dict, current_teams: dict, threshold: float = CHANGE_THRESHOLD_PP) -> dict:
    changes = {}
    for team, stats in current_teams.items():
        previous_stats = previous_teams.get(team, {})
        team_changes = {}
        for stage, value in stats.items():
            delta_pp = (value - previous_stats.get(stage, 0)) * 100
            if abs(delta_pp) >= threshold:
                team_changes[stage] = round(delta_pp, 2)
        if team_changes:
            changes[team] = team_changes
    return changes


def _match_key(home: str, away: str, date) -> str:
    return f"{home}|{away}|{date or ''}"


def compute_match_changes(previous_matches: dict, current_matches: dict, threshold: float = CHANGE_THRESHOLD_PP) -> dict:
    """Only meaningful for a match unplayed both yesterday and today (a newly-resolved
    match is scored by calibration.py instead, and a match with no prior snapshot has
    nothing to diff against)."""
    previous_by_key = {
        _match_key(m["home_team"], m["away_team"], m["date"]): m["prediction"] for m in previous_matches.get("matches", [])
    }
    changes = {}
    for m in current_matches["matches"]:
        key = _match_key(m["home_team"], m["away_team"], m["date"])
        previous_prediction = previous_by_key.get(key)
        if previous_prediction is None:
            continue
        current_prediction = m["prediction"]
        match_changes = {}
        for probability_key in ("home_win_probability", "draw_probability", "away_win_probability"):
            delta_pp = (current_prediction[probability_key] - previous_prediction[probability_key]) * 100
            if abs(delta_pp) >= threshold:
                match_changes[probability_key] = round(delta_pp, 2)
        if match_changes:
            changes[key] = match_changes
    return changes
