"""Probability-change arrows (PRD.md S5.1a): "no arrow if change is < 0.1pp (avoid
noise from Monte Carlo jitter)." Generalizes the diffing movers.py already does for
won_tournament to every stage key, and to per-match W/D/L too.

The caller (update.py) diffs against a "change baseline" that only advances when a
real match resolves, not against whatever the immediately preceding pipeline run
happened to produce -- so the delta means "since the last result," and survives any
number of no-op runs in between (e.g. multiple manual `make update` runs in one day
with no new match) without resetting to zero.
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
    """Only meaningful for a match unplayed both at the baseline and now (a newly-resolved
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


LIST_ROUND_KEYS = ("round_of_32", "round_of_16", "quarter_finals", "semi_finals")
SINGLE_SLOT_ROUND_KEYS = ("final", "third_place")


def _bracket_slot_changes(round_key: str, slot_index: int, previous_slot: dict, current_slot: dict, threshold: float) -> dict:
    """Only produces a delta when the SAME team occupies a side in both snapshots --
    a different most-likely occupant isn't a probability change to arrow, it's a new
    occupant, already visible from the name itself."""
    changes = {}
    for side in ("home", "away"):
        current_occupant = current_slot.get(side)
        previous_occupant = (previous_slot or {}).get(side)
        if not current_occupant or not previous_occupant:
            continue
        if current_occupant["team"] != previous_occupant["team"]:
            continue
        delta_pp = (current_occupant["probability"] - previous_occupant["probability"]) * 100
        if abs(delta_pp) >= threshold:
            changes[f"{round_key}|{slot_index}|{side}"] = round(delta_pp, 2)
    return changes


def compute_bracket_changes(previous_bracket: dict, current_bracket: dict, threshold: float = CHANGE_THRESHOLD_PP) -> dict:
    changes = {}
    for round_key in LIST_ROUND_KEYS:
        previous_slots = previous_bracket.get(round_key, [])
        for i, current_slot in enumerate(current_bracket.get(round_key, [])):
            previous_slot = previous_slots[i] if i < len(previous_slots) else {}
            changes.update(_bracket_slot_changes(round_key, i, previous_slot, current_slot, threshold))
    for round_key in SINGLE_SLOT_ROUND_KEYS:
        changes.update(_bracket_slot_changes(round_key, 0, previous_bracket.get(round_key, {}), current_bracket.get(round_key, {}), threshold))
    return changes
