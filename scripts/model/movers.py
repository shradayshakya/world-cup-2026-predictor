"""Biggest-movers commentary (PRD.md S6.4): explains day-over-day tournament-winner
probability swings using only structured facts our own pipeline already produced.

Monte Carlo jitter is +-0.2pp run-to-run by design (PRD.md S10) -- MOVER_THRESHOLD_PP
is set well above that so re-simulation noise never gets treated as a real movement
worth asking the LLM to "explain" (which would itself be a kind of hallucination:
explaining noise as if it were signal).
"""

import re
import unicodedata

from .injuries import INJURY_EXTRACTION_MODEL  # PRD S6.4: same Ollama runtime as S6.3
from .ollama_client import generate_json

MOVER_THRESHOLD_PP = 0.5
TOP_N_MOVERS = 5

MOVERS_PROMPT_TEMPLATE = """A football team's probability of winning the 2026 FIFA World Cup changed from {previous_pct:.1f}% to {current_pct:.1f}% (a {direction} of {delta_pp:.1f} percentage points) since the last update.

Team: {team}

Relevant results since the last update:
{results_block}

Current reported injuries/absences for this team:
{injuries_block}

Write a single paragraph of no more than 60 words explaining why {team}'s title odds {moved_verb}, in our own prediction model. Base your explanation ONLY on the facts given above -- do not invent specific stats, scorelines, or events not listed. Do not refer to "the market," "betting odds," or "market sentiment" -- this is our own model's estimate, not a betting market. If the facts given don't suggest a clear connecting reason, just say the model's estimate shifted without a specific event behind it -- don't fabricate a cause.

Respond with ONLY a JSON object: {{"blurb": "<your paragraph>"}}
"""


def _slugify(name: str) -> str:
    decomposed = unicodedata.normalize("NFD", name)
    stripped = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", stripped.lower()).strip("-")


def compute_movers(previous_teams: dict, current_teams: dict, threshold: float = MOVER_THRESHOLD_PP, n: int = TOP_N_MOVERS) -> list:
    deltas = []
    for team, stats in current_teams.items():
        previous_pct = previous_teams.get(team, {}).get("won_tournament", 0) * 100
        current_pct = stats.get("won_tournament", 0) * 100
        delta_pp = current_pct - previous_pct
        if abs(delta_pp) >= threshold:
            deltas.append({"team": team, "previous_pct": previous_pct, "current_pct": current_pct, "delta_pp": delta_pp})
    deltas.sort(key=lambda d: -abs(d["delta_pp"]))
    for d in deltas[:n]:
        d["direction"] = "gainer" if d["delta_pp"] > 0 else "loser"
    return deltas[:n]


def _gather_context(team: str, groups: dict, results: dict, injuries: dict, today: str) -> tuple:
    group_letter = next((letter for letter, standings in groups.items() if any(e["team"] == team for e in standings)), None)
    groupmates = {e["team"] for e in groups.get(group_letter, [])} if group_letter else set()

    recent = [
        m
        for m in results["matches"]
        if m["played"] and m["date"] == today and (m["home_team"] in groupmates or m["away_team"] in groupmates)
    ]
    absences = injuries.get(team, {}).get("absences", [])
    return recent, absences


def _format_results_block(recent: list) -> str:
    if not recent:
        return "(none)"
    return "\n".join(f"- {m['home_team']} {m['home_score']}-{m['away_score']} {m['away_team']}" for m in recent)


def _format_injuries_block(absences: list) -> str:
    if not absences:
        return "(none reported)"
    return "\n".join(f"- {a['player']}: {a['status']}" for a in absences)


def generate_movers_commentary(movers: list, groups: dict, results: dict, injuries: dict, today: str, model: str = INJURY_EXTRACTION_MODEL) -> list:
    enriched = []
    for mover in movers:
        recent, absences = _gather_context(mover["team"], groups, results, injuries, today)
        prompt = MOVERS_PROMPT_TEMPLATE.format(
            previous_pct=mover["previous_pct"],
            current_pct=mover["current_pct"],
            delta_pp=abs(mover["delta_pp"]),
            direction=mover["direction"],
            team=mover["team"],
            results_block=_format_results_block(recent),
            injuries_block=_format_injuries_block(absences),
            moved_verb="rose" if mover["direction"] == "gainer" else "fell",
        )
        parsed = generate_json(model, prompt)
        blurb = parsed.get("blurb", "").strip() if parsed else ""

        sources = [{"label": mover["team"], "href": f"/teams/{_slugify(mover['team'])}"}]
        for m in recent:
            sources.append({"label": f"{m['home_team']} vs {m['away_team']}", "href": f"/teams/{_slugify(m['home_team'])}"})
        for a in absences:
            sources.append({"label": a["source_title"], "href": a["source_link"]})

        enriched.append({**mover, "blurb": blurb, "sources": sources})
    return enriched
