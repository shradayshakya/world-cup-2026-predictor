"""LLM fallback for the structured BS4 scrapers (PRD.md S7/S11 Phase 5c): when a
parser's sanity check fails, retry extraction from the same raw HTML via the local
Ollama model instead of trusting (or crashing on) bad structured-parse output.

Narrow extraction only, same philosophy as model/injuries.py's headline extraction --
the LLM's output is never trusted outright, the caller re-runs the same deterministic
validator on it before accepting (see scrapers/wikipedia.py and scrapers/squads.py).
"""

from .ollama_client import generate_json

GROUP_STANDINGS_PROMPT_TEMPLATE = """You will be given the raw HTML of one Wikipedia table showing a single World Cup group's standings (4 teams).

Extract each team's row. "host" is true only if the team's name cell contains a host-nation marker (e.g. "(H)" or "(H, X)"); strip any such parenthetical annotation from the team name itself.

Respond with ONLY a JSON object of this exact shape:
{{"standings": [{{"position": <int>, "team": "<name, with any parenthetical flags stripped>", "host": <bool>, "played": <int>, "won": <int>, "drawn": <int>, "lost": <int>, "goals_for": <int>, "goals_against": <int>, "goal_difference": <int>, "points": <int>, "qualification_note": "<text or empty string>"}}]}}

HTML:
{table_html}
"""

SQUAD_PROMPT_TEMPLATE = """You will be given the raw HTML of one Wikipedia table listing a national football squad's players.

Extract each player row. "captain" is true only if the player's name cell marks them as captain (e.g. "(captain)" next to the name).

Respond with ONLY a JSON object of this exact shape:
{{"players": [{{"name": "<full name>", "captain": <bool>, "position": "<e.g. GK, DF, MF, FW>", "caps": <int>, "goals": <int>, "club": "<club name>"}}]}}

HTML:
{table_html}
"""


def extract_group_standings_via_llm(model: str, table_html: str) -> list | None:
    parsed = generate_json(model, GROUP_STANDINGS_PROMPT_TEMPLATE.format(table_html=table_html))
    if not parsed or not isinstance(parsed.get("standings"), list):
        return None
    return parsed["standings"]


def extract_squad_via_llm(model: str, table_html: str) -> list | None:
    parsed = generate_json(model, SQUAD_PROMPT_TEMPLATE.format(table_html=table_html))
    if not parsed or not isinstance(parsed.get("players"), list):
        return None
    return parsed["players"]
