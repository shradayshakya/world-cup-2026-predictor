"""Shared team-identity helpers for joining elo.json against Wikipedia-sourced data."""

# results.json / groups.json (Wikipedia) -> elo.json (eloratings.net) name mismatches.
TEAM_ALIASES = {
    "Czech Republic": "Czechia",
}


def resolve_rating(team_name: str, elo_by_name: dict):
    return elo_by_name.get(TEAM_ALIASES.get(team_name, team_name))
