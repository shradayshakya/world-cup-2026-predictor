"""Scraper for eloratings.net current World football Elo ratings (PRD.md S7)."""

from .http import fetch

WORLD_TSV_URL = "https://www.eloratings.net/World.tsv"
TEAMS_TSV_URL = "https://www.eloratings.net/en.teams.tsv"


def _parse_team_names(tsv_text: str) -> dict:
    names = {}
    for line in tsv_text.splitlines():
        if not line.strip():
            continue
        fields = line.split("\t")
        code = fields[0]
        if code.endswith("_loc"):
            continue
        names[code] = fields[1]
    return names


def _parse_ratings(tsv_text: str, team_names: dict) -> list:
    teams = []
    for line in tsv_text.splitlines():
        if not line.strip():
            continue
        fields = line.split("\t")
        code = fields[2]
        teams.append(
            {
                "rank": int(fields[1]),
                "code": code,
                "name": team_names.get(code, code),
                "rating": int(fields[3]),
            }
        )
    return teams


def scrape_elo() -> dict:
    team_names = _parse_team_names(fetch(TEAMS_TSV_URL))
    teams = _parse_ratings(fetch(WORLD_TSV_URL), team_names)
    return {"teams": teams}
