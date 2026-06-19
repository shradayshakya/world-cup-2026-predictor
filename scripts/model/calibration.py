"""Calibration audit (PRD.md S10): after each match, compare our prediction to the
actual result, log Brier score and log-loss, surface on /about so users can audit
the model.

matches.json only ever holds *unplayed* matches -- once a match is played it drops
out, with no archive of what we predicted, unless captured at the transition. So
this reads the *previous* run's matches.json (the same snapshot-before-overwrite
trick used for movers.py) and cross-references it against the freshly scraped
results.json to find whichever matches flipped from unplayed to played since the
last run.
"""

import math

OUTCOME_KEYS = ("home", "draw", "away")


def _outcome(home_score: int, away_score: int) -> str:
    if home_score > away_score:
        return "home"
    if home_score < away_score:
        return "away"
    return "draw"


def score_resolved_matches(previous_matches: dict, results: dict) -> list:
    played_by_key = {(m["home_team"], m["away_team"], m["date"]): m for m in results["matches"] if m["played"]}

    entries = []
    for pm in previous_matches.get("matches", []):
        key = (pm["home_team"], pm["away_team"], pm["date"])
        actual = played_by_key.get(key)
        if actual is None:
            continue

        prediction = pm["prediction"]
        probabilities = {
            "home": prediction["home_win_probability"],
            "draw": prediction["draw_probability"],
            "away": prediction["away_win_probability"],
        }
        outcome = _outcome(actual["home_score"], actual["away_score"])
        brier_score = sum((probabilities[o] - (1.0 if o == outcome else 0.0)) ** 2 for o in OUTCOME_KEYS)
        log_loss = -math.log(max(probabilities[outcome], 1e-9))  # floor avoids log(0) if we ever predicted exactly 0%
        scoreline_correct = (
            prediction["predicted_home_score"] == actual["home_score"] and prediction["predicted_away_score"] == actual["away_score"]
        )

        entries.append(
            {
                "date": pm["date"],
                "home_team": pm["home_team"],
                "away_team": pm["away_team"],
                "predicted_home_score": prediction["predicted_home_score"],
                "predicted_away_score": prediction["predicted_away_score"],
                "home_win_probability": probabilities["home"],
                "draw_probability": probabilities["draw"],
                "away_win_probability": probabilities["away"],
                "actual_home_score": actual["home_score"],
                "actual_away_score": actual["away_score"],
                "actual_outcome": outcome,
                "brier_score": round(brier_score, 4),
                "log_loss": round(log_loss, 4),
                "scoreline_correct": scoreline_correct,
            }
        )
    return entries


def merge_into_log(existing_log: dict, new_entries: list) -> dict:
    """Append-only across the whole tournament -- unlike every other public/data/*.json
    file, this one is never simply overwritten. Keyed by (date, home, away) so re-running
    update.py twice in one day (or any other accidental re-run) doesn't double-count."""
    entries = list(existing_log.get("entries", []))
    seen = {(e["date"], e["home_team"], e["away_team"]) for e in entries}
    for entry in new_entries:
        key = (entry["date"], entry["home_team"], entry["away_team"])
        if key not in seen:
            entries.append(entry)
            seen.add(key)

    n = len(entries)
    summary = {
        "n": n,
        "avg_brier_score": round(sum(e["brier_score"] for e in entries) / n, 4) if n else None,
        "avg_log_loss": round(sum(e["log_loss"] for e in entries) / n, 4) if n else None,
        "scoreline_accuracy": round(sum(1 for e in entries if e["scoreline_correct"]) / n, 4) if n else None,
    }
    return {"entries": entries, "summary": summary}
