"""Poisson-Elo match model (PRD.md S6.1).

No historical results dataset is available to fit a real Dixon-Coles model in
this zero-budget setup, so the Elo-to-goals mapping below is a documented
heuristic, not a regression fit to match outcomes.

Elo difference is converted to expected goals *multiplicatively*
(ELO_RATIO_SCALE below), not by redistributing a fixed total between the two
teams. An earlier additive version (lambda_home + lambda_away held constant
at AVERAGE_GOALS_PER_MATCH regardless of Elo gap) structurally capped the
favorite's expected goals at AVERAGE_GOALS_PER_MATCH - MIN_EXPECTED_GOALS
(2.45), which caps the Poisson mode at 2 goals forever -- no Elo gap, however
large, could ever produce a 3-0 or 4-0 prediction. Grid-searched
ELO_RATIO_SCALE against eloratings.net's own win expectancy (already
scraped, a free real-world target): 500 both fits eloratings.net better than
the old additive model did (0.74pp avg error vs 1.45pp) and lets blowout
matchups actually predict blowout scorelines (e.g. Spain vs Saudi Arabia ->
4-0 at 96% win), while leaving close matchups (e.g. Switzerland vs Canada,
1-1 at 35/30/35) untouched. Revisit via the PRD S10 Brier-score calibration
check once enough matches have been played.
"""

import math

import numpy as np

AVERAGE_GOALS_PER_MATCH = 2.6  # ~ historical World Cup average (2018: 2.64, 2022: 2.69)
HOME_ADVANTAGE_ELO = 100  # applied only to host-nation matches (PRD S6.1)
ELO_RATIO_SCALE = 500  # calibrated against eloratings.net's win expectancy -- see module docstring
DIXON_COLES_RHO = -0.13  # literature-typical low-score correlation (Dixon & Coles 1997)
MAX_GOALS = 7
MIN_EXPECTED_GOALS = 0.15
MAX_EXPECTED_GOALS = 6.0  # safety cap so an extreme future Elo gap can't push lambda past the score grid's range

_FACTORIALS = np.array([math.factorial(k) for k in range(MAX_GOALS + 1)], dtype=np.float64)


def expected_goals(elo_home: float, elo_away: float, host_home: bool, host_away: bool) -> tuple:
    home_elo = elo_home + (HOME_ADVANTAGE_ELO if host_home else 0)
    away_elo = elo_away + (HOME_ADVANTAGE_ELO if host_away else 0)
    ratio = 10 ** ((home_elo - away_elo) / ELO_RATIO_SCALE)
    avg_per_team = AVERAGE_GOALS_PER_MATCH / 2.0
    lambda_home = min(max(avg_per_team * math.sqrt(ratio), MIN_EXPECTED_GOALS), MAX_EXPECTED_GOALS)
    lambda_away = min(max(avg_per_team / math.sqrt(ratio), MIN_EXPECTED_GOALS), MAX_EXPECTED_GOALS)
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
