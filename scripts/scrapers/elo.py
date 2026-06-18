"""Scrapers for eloratings.net: current ratings, recent results, and fixture win-expectancy (PRD.md S7)."""

from collections import defaultdict

from model.teams import to_wikipedia_name

from .http import fetch

TEAMS_TSV_URL = "https://www.eloratings.net/en.teams.tsv"
TOURNAMENTS_TSV_URL = "https://www.eloratings.net/en.tournaments.tsv"
WORLD_TSV_URL = "https://www.eloratings.net/World.tsv"
LATEST_TSV_URL = "https://www.eloratings.net/latest.tsv"
FIXTURES_TSV_URL = "https://www.eloratings.net/fixtures.tsv"

RECENT_FORM_LIMIT = 10


def _parse_code_dictionary(tsv_text: str) -> dict:
    """Shared parser for en.teams.tsv / en.tournaments.tsv: code, name, then display variants."""
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


def fetch_team_names() -> dict:
    return _parse_code_dictionary(fetch(TEAMS_TSV_URL))


def fetch_tournament_names() -> dict:
    return _parse_code_dictionary(fetch(TOURNAMENTS_TSV_URL))


def scrape_elo(team_names: dict) -> dict:
    teams = []
    for line in fetch(WORLD_TSV_URL).splitlines():
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
    return {"teams": teams}


def scrape_recent_form(team_names: dict, tournament_names: dict, team_codes: set) -> dict:
    """Returns {team_name: [last RECENT_FORM_LIMIT match results, most recent first]} for team_codes only."""
    matches_by_code = defaultdict(list)
    for line in fetch(LATEST_TSV_URL).splitlines():
        if not line.strip():
            continue
        fields = line.split("\t")
        home_code, away_code = fields[3], fields[4]
        if home_code not in team_codes and away_code not in team_codes:
            continue
        date = f"{fields[0]}-{fields[1]}-{fields[2]}"
        home_goals, away_goals = int(fields[5]), int(fields[6])
        tournament = tournament_names.get(fields[7], fields[7])
        venue_code = fields[8] or home_code  # empty venue means it was played in the home team's country
        venue = to_wikipedia_name(team_names.get(venue_code, venue_code))

        for code, opponent_code, goals_for, goals_against in (
            (home_code, away_code, home_goals, away_goals),
            (away_code, home_code, away_goals, home_goals),
        ):
            if code not in team_codes or len(matches_by_code[code]) >= RECENT_FORM_LIMIT:
                continue
            result = "W" if goals_for > goals_against else "L" if goals_for < goals_against else "D"
            matches_by_code[code].append(
                {
                    "date": date,
                    "opponent": to_wikipedia_name(team_names.get(opponent_code, opponent_code)),
                    "goals_for": goals_for,
                    "goals_against": goals_against,
                    "result": result,
                    "tournament": tournament,
                    "venue": venue,
                }
            )

    return {to_wikipedia_name(team_names.get(code, code)): matches for code, matches in matches_by_code.items()}


def scrape_fixtures_win_expectancy(team_names: dict) -> dict:
    """Returns {(home_name, away_name): home_win_expectancy_pct} for World Cup fixtures only."""
    win_expectancy = {}
    for line in fetch(FIXTURES_TSV_URL).splitlines():
        if not line.strip():
            continue
        fields = line.split("\t")
        if fields[5] != "WC":
            continue
        home_name = to_wikipedia_name(team_names.get(fields[3], fields[3]))
        away_name = to_wikipedia_name(team_names.get(fields[4], fields[4]))
        win_expectancy[(home_name, away_name)] = float(fields[11])
    return win_expectancy
