"""Monte Carlo tournament simulation (PRD.md S6.2, S11 Phase 3).

Each run simulates the rest of the tournament N times: group matches are
sampled from the Phase 2 Poisson grids, the 8 best third-placed teams are
picked and matched against the bracket's candidate-list slots (a small
bipartite matching, since a group's third-place team is a candidate for
several slots but can only fill one), and knockout matches are simulated
with extra-time + a lightly Elo-weighted penalty shootout for draws.
"""

import random
from collections import Counter, defaultdict

import numpy as np

from .bracket import (
    FINAL_CONNECTIVITY,
    QF_CONNECTIVITY,
    R16_CONNECTIVITY,
    ROUND_OF_32_SLOTS,
    SF_CONNECTIVITY,
    THIRD_PLACE_CONNECTIVITY,
)
from .poisson import HOME_ADVANTAGE_ELO, expected_goals, sample_score, score_grid
from .teams import resolve_rating

N_SIMULATIONS = 50_000
EXTRA_TIME_LAMBDA_FACTOR = 1 / 3  # PRD S6.2: "extend lambda by 1/3 for ET"
PENALTY_ELO_DIVISOR = 2000.0  # PRD S6.2: penalty coin-flip "weighted lightly by Elo"
PENALTY_PROB_MIN = 0.35
PENALTY_PROB_MAX = 0.65

GROUP_LETTERS = list("ABCDEFGHIJKL")


def _group_sort_key(stats: dict) -> tuple:
    return (-stats["points"], -(stats["gf"] - stats["ga"]), -stats["gf"])


def _head_to_head(a: str, b: str, match_log: list):
    a_pts = b_pts = 0
    for home, away, hg, ag in match_log:
        if home == a and away == b:
            a_pts, b_pts = (3, 0) if hg > ag else (0, 3) if hg < ag else (1, 1)
        elif home == b and away == a:
            b_pts, a_pts = (3, 0) if hg > ag else (0, 3) if hg < ag else (1, 1)
    if a_pts > b_pts:
        return a
    if b_pts > a_pts:
        return b
    return None


def _rank_group(teams: list, stats: dict, match_log: list, rng: random.Random) -> list:
    ordered = sorted(teams, key=lambda t: _group_sort_key(stats[t]))
    result = []
    i = 0
    while i < len(ordered):
        j = i + 1
        while j < len(ordered) and _group_sort_key(stats[ordered[j]]) == _group_sort_key(stats[ordered[i]]):
            j += 1
        block = ordered[i:j]
        if len(block) == 2:
            winner = _head_to_head(block[0], block[1], match_log)
            if winner == block[1]:
                block = [block[1], block[0]]
            elif winner is None:
                rng.shuffle(block)
        elif len(block) > 1:
            rng.shuffle(block)
        result.extend(block)
        i = j
    return result


def _rank_thirds(candidates: list, rng: random.Random) -> list:
    """candidates: list of (letter, team, points, goal_diff, goals_for)."""
    ordered = sorted(candidates, key=lambda c: (-c[2], -c[3], -c[4]))
    result = []
    i = 0
    while i < len(ordered):
        j = i + 1
        while j < len(ordered) and ordered[j][2:] == ordered[i][2:]:
            j += 1
        block = ordered[i:j]
        if len(block) > 1:
            rng.shuffle(block)
        result.extend(block)
        i = j
    return result


def _match_third_place_slots(slot_candidates: dict, qualifying_groups: set) -> dict:
    """Bipartite matching (Kuhn's algorithm): each of the 8 qualifying groups'
    third-place team can fill several candidate slots but only one slot total,
    and each slot needs exactly one group. Returns slot_key -> group_letter."""
    adjacency = {node: [g for g in cands if g in qualifying_groups] for node, cands in slot_candidates.items()}
    group_to_node = {}

    def try_assign(node, visited_groups):
        for g in adjacency[node]:
            if g in visited_groups:
                continue
            visited_groups.add(g)
            if g not in group_to_node or try_assign(group_to_node[g], visited_groups):
                group_to_node[g] = node
                return True
        return False

    for node in adjacency:
        try_assign(node, set())

    return {node: g for g, node in group_to_node.items()}


def _resolve_selector(selector: tuple, group_rankings: dict, third_assignment: dict, node_key) -> str:
    selector_type, value = selector
    if selector_type == "winner":
        return group_rankings[value][0]
    if selector_type == "runner_up":
        return group_rankings[value][1]
    return group_rankings[third_assignment[node_key]][2]  # selector_type == "third"


def _simulate_knockout_match(home, away, elo_by_name, host_by_team, grid_cache, rng, np_rng):
    key = (home, away)
    if key not in grid_cache:
        home_rating = resolve_rating(home, elo_by_name)
        away_rating = resolve_rating(away, elo_by_name)
        lam_h, lam_a = expected_goals(home_rating, away_rating, host_by_team.get(home, False), host_by_team.get(away, False))
        grid_cache[key] = (home_rating, away_rating, lam_h, lam_a, score_grid(lam_h, lam_a))
    home_rating, away_rating, lam_h, lam_a, grid = grid_cache[key]

    hg, ag = sample_score(grid, np_rng)
    if hg == ag:
        et_key = ("ET", home, away)
        if et_key not in grid_cache:
            grid_cache[et_key] = score_grid(lam_h * EXTRA_TIME_LAMBDA_FACTOR, lam_a * EXTRA_TIME_LAMBDA_FACTOR)
        et_hg, et_ag = sample_score(grid_cache[et_key], np_rng)
        hg, ag = hg + et_hg, ag + et_ag

    if hg == ag:
        elo_diff = (home_rating + (HOME_ADVANTAGE_ELO if host_by_team.get(home) else 0)) - (
            away_rating + (HOME_ADVANTAGE_ELO if host_by_team.get(away) else 0)
        )
        p_home = min(max(0.5 + elo_diff / PENALTY_ELO_DIVISOR, PENALTY_PROB_MIN), PENALTY_PROB_MAX)
        winner = home if rng.random() < p_home else away
    else:
        winner = home if hg > ag else away
    return (winner, away if winner == home else home)


def _simulate_round(matchups, elo_by_name, host_by_team, grid_cache, rng, np_rng):
    return [_simulate_knockout_match(home, away, elo_by_name, host_by_team, grid_cache, rng, np_rng) for home, away in matchups]


def simulate_tournament(elo: dict, groups: dict, results: dict, matches: dict, n_simulations: int = N_SIMULATIONS) -> dict:
    elo_by_name = {t["name"]: t["rating"] for t in elo["teams"]}
    host_by_team = {entry["team"]: entry["host"] for standings in groups["groups"].values() for entry in standings}
    group_teams = {letter: [e["team"] for e in standings] for letter, standings in groups["groups"].items()}
    wc_teams = sorted({t for teams in group_teams.values() for t in teams})

    played_by_group = defaultdict(list)
    remaining_by_group = defaultdict(list)
    for m in results["matches"]:
        if m["round"] == "Group stage":
            target = played_by_group if m["played"] else remaining_by_group
            target[m["group"]].append(m)

    base_stats = {}
    for letter in GROUP_LETTERS:
        stats = {t: {"points": 0, "gf": 0, "ga": 0} for t in group_teams[letter]}
        for m in played_by_group[letter]:
            _apply_result(stats, m["home_team"], m["away_team"], m["home_score"], m["away_score"])
        base_stats[letter] = stats

    base_match_log = {
        letter: [(m["home_team"], m["away_team"], m["home_score"], m["away_score"]) for m in played_by_group[letter]]
        for letter in GROUP_LETTERS
    }

    def _normalized_grid(score_grid_list):
        grid = np.array(score_grid_list)
        return grid / grid.sum()  # matches.json grids are rounded to 4dp for display; renormalize for sampling

    precomputed_grids = {
        (m["home_team"], m["away_team"]): _normalized_grid(m["prediction"]["score_grid"])
        for m in matches["matches"]
        if m["round"] == "Group stage"
    }

    slot_candidates = {}
    for slot_idx, (home_sel, away_sel) in enumerate(ROUND_OF_32_SLOTS):
        if home_sel[0] == "third":
            slot_candidates[(slot_idx, "home")] = home_sel[1]
        if away_sel[0] == "third":
            slot_candidates[(slot_idx, "away")] = away_sel[1]

    stage_counts = {t: Counter() for t in wc_teams}
    rng = random.Random()
    np_rng = np.random.default_rng()
    knockout_grid_cache = {}

    for _ in range(n_simulations):
        group_rankings = {}
        group_stats = {}
        for letter in GROUP_LETTERS:
            stats = {t: dict(v) for t, v in base_stats[letter].items()}
            match_log = list(base_match_log[letter])
            for m in remaining_by_group[letter]:
                grid = precomputed_grids[(m["home_team"], m["away_team"])]
                hg, ag = sample_score(grid, np_rng)
                _apply_result(stats, m["home_team"], m["away_team"], hg, ag)
                match_log.append((m["home_team"], m["away_team"], hg, ag))
            ranking = _rank_group(group_teams[letter], stats, match_log, rng)
            group_rankings[letter] = ranking
            group_stats[letter] = stats

            stage_counts[ranking[0]]["group_winner"] += 1
            stage_counts[ranking[1]]["group_runner_up"] += 1
            stage_counts[ranking[2]]["group_third"] += 1
            stage_counts[ranking[3]]["group_fourth"] += 1

        third_candidates = [
            (
                letter,
                group_rankings[letter][2],
                group_stats[letter][group_rankings[letter][2]]["points"],
                group_stats[letter][group_rankings[letter][2]]["gf"] - group_stats[letter][group_rankings[letter][2]]["ga"],
                group_stats[letter][group_rankings[letter][2]]["gf"],
            )
            for letter in GROUP_LETTERS
        ]
        qualifying_thirds = _rank_thirds(third_candidates, rng)[:8]
        qualifying_letters = {c[0] for c in qualifying_thirds}
        third_assignment = _match_third_place_slots(slot_candidates, qualifying_letters)

        for letter in qualifying_letters:
            stage_counts[group_rankings[letter][2]]["group_third_advanced"] += 1

        r32_matchups = []
        for slot_idx, (home_sel, away_sel) in enumerate(ROUND_OF_32_SLOTS):
            home_team = _resolve_selector(home_sel, group_rankings, third_assignment, (slot_idx, "home"))
            away_team = _resolve_selector(away_sel, group_rankings, third_assignment, (slot_idx, "away"))
            r32_matchups.append((home_team, away_team))

        for home, away in r32_matchups:
            stage_counts[home]["advanced_to_r32"] += 1
            stage_counts[away]["advanced_to_r32"] += 1

        r32_results = _simulate_round(r32_matchups, elo_by_name, host_by_team, knockout_grid_cache, rng, np_rng)
        r32_winners = [w for w, _ in r32_results]
        for w in r32_winners:
            stage_counts[w]["reached_r16"] += 1

        r16_matchups = [(r32_winners[a], r32_winners[b]) for a, b in R16_CONNECTIVITY]
        r16_results = _simulate_round(r16_matchups, elo_by_name, host_by_team, knockout_grid_cache, rng, np_rng)
        r16_winners = [w for w, _ in r16_results]
        for w in r16_winners:
            stage_counts[w]["reached_qf"] += 1

        qf_matchups = [(r16_winners[a], r16_winners[b]) for a, b in QF_CONNECTIVITY]
        qf_results = _simulate_round(qf_matchups, elo_by_name, host_by_team, knockout_grid_cache, rng, np_rng)
        qf_winners = [w for w, _ in qf_results]
        for w in qf_winners:
            stage_counts[w]["reached_sf"] += 1

        sf_matchups = [(qf_winners[a], qf_winners[b]) for a, b in SF_CONNECTIVITY]
        sf_results = _simulate_round(sf_matchups, elo_by_name, host_by_team, knockout_grid_cache, rng, np_rng)
        sf_winners = [w for w, _ in sf_results]
        sf_losers = [l for _, l in sf_results]
        for w in sf_winners:
            stage_counts[w]["reached_final"] += 1

        final_matchup = (sf_winners[FINAL_CONNECTIVITY[0]], sf_winners[FINAL_CONNECTIVITY[1]])
        (champion, _runner_up), = _simulate_round([final_matchup], elo_by_name, host_by_team, knockout_grid_cache, rng, np_rng)
        stage_counts[champion]["won_tournament"] += 1

        third_place_matchup = (sf_losers[THIRD_PLACE_CONNECTIVITY[0]], sf_losers[THIRD_PLACE_CONNECTIVITY[1]])
        (third_place_winner, _fourth), = _simulate_round([third_place_matchup], elo_by_name, host_by_team, knockout_grid_cache, rng, np_rng)
        stage_counts[third_place_winner]["won_third_place_match"] += 1

    teams_output = {
        team: {stage: round(count / n_simulations, 4) for stage, count in counts.items()} for team, counts in stage_counts.items()
    }
    return {"n_simulations": n_simulations, "teams": teams_output}


def _apply_result(stats: dict, home: str, away: str, home_goals: int, away_goals: int) -> None:
    stats[home]["gf"] += home_goals
    stats[home]["ga"] += away_goals
    stats[away]["gf"] += away_goals
    stats[away]["ga"] += home_goals
    if home_goals > away_goals:
        stats[home]["points"] += 3
    elif home_goals < away_goals:
        stats[away]["points"] += 3
    else:
        stats[home]["points"] += 1
        stats[away]["points"] += 1
