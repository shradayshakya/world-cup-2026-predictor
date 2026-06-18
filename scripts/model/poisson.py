"""Poisson-Elo match model (PRD.md S6.1).

No historical results dataset is available to fit a real Dixon-Coles model in
this zero-budget setup, so the Elo-to-goals mapping below is a documented
heuristic, not a regression fit to match outcomes. GOAL_SUPREMACY_PER_400_ELO
*was* calibrated, though: grid-searched against eloratings.net's own win
expectancy (which we already scrape) as a free, real-world target, since our
v1 value of 1.0 was badly undershooting -- it disagreed with eloratings.net
by ~12.6pp average on the 48 group-stage matches available on 2026-06-18,
and collapsed almost every predicted scoreline to 1-1 (41/48) regardless of
how lopsided the matchup actually was. 2.5 cuts that disagreement to ~1.5pp.
Revisit via the PRD S10 Brier-score calibration check once enough matches
have been played.
"""

import math

import numpy as np

AVERAGE_GOALS_PER_MATCH = 2.6  # ~ historical World Cup average (2018: 2.64, 2022: 2.69)
HOME_ADVANTAGE_ELO = 100  # applied only to host-nation matches (PRD S6.1)
GOAL_SUPREMACY_PER_400_ELO = 2.5  # calibrated against eloratings.net's win expectancy -- see module docstring
DIXON_COLES_RHO = -0.13  # literature-typical low-score correlation (Dixon & Coles 1997)
MAX_GOALS = 7
MIN_EXPECTED_GOALS = 0.15

_FACTORIALS = np.array([math.factorial(k) for k in range(MAX_GOALS + 1)], dtype=np.float64)


def expected_goals(elo_home: float, elo_away: float, host_home: bool, host_away: bool) -> tuple:
    home_elo = elo_home + (HOME_ADVANTAGE_ELO if host_home else 0)
    away_elo = elo_away + (HOME_ADVANTAGE_ELO if host_away else 0)
    goal_supremacy = (home_elo - away_elo) / 400.0 * GOAL_SUPREMACY_PER_400_ELO
    avg_per_team = AVERAGE_GOALS_PER_MATCH / 2.0
    lambda_home = max(avg_per_team + goal_supremacy / 2.0, MIN_EXPECTED_GOALS)
    lambda_away = max(avg_per_team - goal_supremacy / 2.0, MIN_EXPECTED_GOALS)
    return lambda_home, lambda_away


def _poisson_pmf(lam: float) -> np.ndarray:
    ks = np.arange(MAX_GOALS + 1)
    return np.exp(-lam) * lam**ks / _FACTORIALS


def _dixon_coles_tau(x: int, y: int, lam: float, mu: float, rho: float) -> float:
    if x == 0 and y == 0:
        return 1 - lam * mu * rho
    if x == 0 and y == 1:
        return 1 + lam * rho
    if x == 1 and y == 0:
        return 1 + mu * rho
    if x == 1 and y == 1:
        return 1 - rho
    return 1.0


def score_grid(lambda_home: float, lambda_away: float, rho: float = DIXON_COLES_RHO) -> np.ndarray:
    """Returns a (MAX_GOALS+1) x (MAX_GOALS+1) probability grid, grid[h][a] = P(home=h, away=a)."""
    grid = np.outer(_poisson_pmf(lambda_home), _poisson_pmf(lambda_away))
    for x in range(2):
        for y in range(2):
            grid[x, y] *= _dixon_coles_tau(x, y, lambda_home, lambda_away, rho)
    grid /= grid.sum()
    return grid


def sample_score(grid: np.ndarray, rng: np.random.Generator) -> tuple:
    """Draws one (home_goals, away_goals) sample from a score probability grid."""
    flat_index = rng.choice(grid.size, p=grid.ravel())
    home_goals, away_goals = np.unravel_index(flat_index, grid.shape)
    return int(home_goals), int(away_goals)


def summarize(grid: np.ndarray) -> dict:
    home_idx, away_idx = np.unravel_index(np.argmax(grid), grid.shape)
    home_goals, away_goals = np.indices(grid.shape)
    return {
        "predicted_home_score": int(home_idx),
        "predicted_away_score": int(away_idx),
        "home_win_probability": round(float(grid[home_goals > away_goals].sum()), 4),
        "draw_probability": round(float(grid[home_goals == away_goals].sum()), 4),
        "away_win_probability": round(float(grid[home_goals < away_goals].sum()), 4),
        "score_grid": [[round(float(p), 4) for p in row] for row in grid],
    }
