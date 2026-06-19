"""Scraper for the Wikipedia 2026 FIFA World Cup squads page (PRD.md S7).

Cadence is "once + diff" (PRD.md S7), not daily like the other scrapers --
see update.py, which only calls this when public/data/squads.json doesn't
already exist yet.
"""

from bs4 import BeautifulSoup

from model.parser_fallback import extract_squad_via_llm

from .http import fetch

SQUADS_URL = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_squads"

# FIFA squad rules allow 23-26; real 2026 data is uniformly 26 per team. Widened a
# bit beyond that exact range so a minor future rules change doesn't false-positive.
MIN_SQUAD_SIZE = 18
MAX_SQUAD_SIZE = 30


def _link_text(cell) -> str:
    """Squad tables hide a numeric sort key as plain text before the visible link
    (e.g. position cells are '<span style="display:none">1</span><a>GK</a>') --
    take the link text, not the cell's full text, to skip that hidden prefix."""
    link = cell.find("a")
    return link.get_text(strip=True) if link else cell.get_text(" ", strip=True)


def _parse_squad_table(table) -> list:
    players = []
    for row in table.find_all("tr")[1:]:
        cells = row.find_all(["th", "td"])
        if len(cells) < 7:
            continue
        name_cell = cells[2]
        players.append(
            {
                "name": _link_text(name_cell),
                "captain": "captain" in name_cell.get_text(" ", strip=True).lower(),
                "position": _link_text(cells[1]),
                "caps": int(cells[4].get_text(strip=True)),
                "goals": int(cells[5].get_text(strip=True)),
                "club": cells[6].get_text(" ", strip=True),
            }
        )
    return players


def _validate_squad(players: list) -> list:
    issues = []
    if not (MIN_SQUAD_SIZE <= len(players) <= MAX_SQUAD_SIZE):
        issues.append(f"squad size {len(players)} outside expected [{MIN_SQUAD_SIZE}, {MAX_SQUAD_SIZE}]")
    for p in players:
        if not p["name"]:
            issues.append("empty player name")
        if p["caps"] < 0 or p["goals"] < 0:
            issues.append(f"{p['name'] or '<empty>'}: negative caps/goals")
    return issues


def scrape_squads(team_names: list, fallback_model: str | None = None) -> tuple:
    """fallback_model: when given, a team's squad that fails _validate_squad gets one
    retry via Ollama extraction from the same table's raw HTML (PRD.md S7/S11 Phase 5c)."""
    soup = BeautifulSoup(fetch(SQUADS_URL), "html.parser")
    squads = {}
    issues = []
    for name in team_names:
        heading = soup.find(id=name.replace(" ", "_"))
        if not heading:
            print(f"squads: no heading found for {name!r}, skipping")
            continue
        table = heading.find_next("table")
        players = _parse_squad_table(table)
        problems = _validate_squad(players)

        if problems and fallback_model:
            fallback = extract_squad_via_llm(fallback_model, str(table))
            fallback_problems = _validate_squad(fallback) if fallback is not None else None
            if fallback is not None and not fallback_problems:
                players = fallback
                issues.append({"source": "squads", "detail": f"{name}: {'; '.join(problems)}", "fallback_attempted": True, "fallback_succeeded": True})
            else:
                issues.append({"source": "squads", "detail": f"{name}: {'; '.join(problems)}", "fallback_attempted": True, "fallback_succeeded": False})
        elif problems:
            issues.append({"source": "squads", "detail": f"{name}: {'; '.join(problems)}", "fallback_attempted": False, "fallback_succeeded": None})

        squads[name] = players
    return squads, issues
