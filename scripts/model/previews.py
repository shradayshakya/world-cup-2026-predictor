"""Match preview blurbs (PRD.md S6.4): one per upcoming match, refreshed daily.

Like movers.py, fed only structured facts our own pipeline already produced
(elo, form, head-to-head, key absences, predicted scoreline) -- the prompt
forbids inventing anything not in that list (PRD.md S6.4a).
"""

from .injuries import INJURY_EXTRACTION_MODEL  # PRD S6.4: same Ollama runtime as S6.3
from .ollama_client import generate_json
from .teams import resolve_rating

PREVIEW_PROMPT_TEMPLATE = """Write a brief preview for an upcoming football match at the 2026 FIFA World Cup, using ONLY the facts below. Do not invent specific stats, scorelines, or events not listed, and do not mention any player or fact not explicitly given here.

{home_team} (Elo {home_elo}) vs {away_team} (Elo {away_elo})

{home_team}'s last 5 results: {home_form}
{away_team}'s last 5 results: {away_form}

Head-to-head meetings on file: {h2h}

Key absences:
{home_team}: {home_absences}
{away_team}: {away_absences}

Our own model's predicted scoreline: {predicted_home_score}-{predicted_away_score} ({home_team} win {home_win_pct:.0f}% / draw {draw_pct:.0f}% / {away_team} win {away_win_pct:.0f}%)

Write a single paragraph of 60-80 words previewing this match. Respond with ONLY a JSON object: {{"preview": "<your paragraph>"}}
"""


def _format_form(matches: list) -> str:
    if not matches:
        return "(none on file)"
    return "; ".join(f"{m['result']} {m['goals_for']}-{m['goals_against']} vs {m['opponent']} ({m['tournament']})" for m in matches[:5])


def _format_h2h(home_form: list, away_team: str) -> str:
    meetings = [m for m in home_form if m["opponent"] == away_team]
    if not meetings:
        return "(none on file)"
    return "; ".join(f"{m['date']}: {m['goals_for']}-{m['goals_against']} ({m['tournament']})" for m in meetings)


def _format_absences(absences: list) -> str:
    if not absences:
        return "(none reported)"
    return ", ".join(f"{a['player']} ({a['status']})" for a in absences)


def _key(home: str, away: str, date) -> str:
    return f"{home}|{away}|{date or ''}"


def generate_previews(matches: dict, elo: dict, form: dict, injuries: dict, model: str = INJURY_EXTRACTION_MODEL) -> dict:
    elo_by_name = {t["name"]: t["rating"] for t in elo["teams"]}
    previews = {}

    for m in matches["matches"]:
        home_team, away_team = m["home_team"], m["away_team"]
        home_form = form.get(home_team, [])
        away_form = form.get(away_team, [])
        prediction = m["prediction"]

        prompt = PREVIEW_PROMPT_TEMPLATE.format(
            home_team=home_team,
            away_team=away_team,
            home_elo=round(resolve_rating(home_team, elo_by_name)),
            away_elo=round(resolve_rating(away_team, elo_by_name)),
            home_form=_format_form(home_form),
            away_form=_format_form(away_form),
            h2h=_format_h2h(home_form, away_team),
            home_absences=_format_absences(injuries.get(home_team, {}).get("absences", [])),
            away_absences=_format_absences(injuries.get(away_team, {}).get("absences", [])),
            predicted_home_score=prediction["predicted_home_score"],
            predicted_away_score=prediction["predicted_away_score"],
            home_win_pct=prediction["home_win_probability"] * 100,
            draw_pct=prediction["draw_probability"] * 100,
            away_win_pct=prediction["away_win_probability"] * 100,
        )
        parsed = generate_json(model, prompt)
        text = parsed.get("preview", "").strip() if parsed else ""
        if not text:
            continue

        sources = [{"label": a["source_title"], "href": a["source_link"]} for a in injuries.get(home_team, {}).get("absences", [])]
        sources += [{"label": a["source_title"], "href": a["source_link"]} for a in injuries.get(away_team, {}).get("absences", [])]
        previews[_key(home_team, away_team, m["date"])] = {"text": text, "sources": sources}

    return previews
