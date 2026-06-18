"""Scraper for the Wikipedia 2026 FIFA World Cup squads page (PRD.md S7).

Cadence is "once + diff" (PRD.md S7), not daily like the other scrapers --
see update.py, which only calls this when public/data/squads.json doesn't
already exist yet.
"""

from bs4 import BeautifulSoup

from .http import fetch

SQUADS_URL = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_squads"


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


def scrape_squads(team_names: list) -> dict:
    soup = BeautifulSoup(fetch(SQUADS_URL), "html.parser")
    squads = {}
    for name in team_names:
        heading = soup.find(id=name.replace(" ", "_"))
        if not heading:
            print(f"squads: no heading found for {name!r}, skipping")
            continue
        table = heading.find_next("table")
        squads[name] = _parse_squad_table(table)
    return squads
