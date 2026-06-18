"""Shared team-identity helpers for joining elo.json against Wikipedia-sourced data."""

# results.json / groups.json (Wikipedia) -> elo.json (eloratings.net) name mismatches.
TEAM_ALIASES = {
    "Czech Republic": "Czechia",
}

REVERSE_TEAM_ALIASES = {eloratings_name: wikipedia_name for wikipedia_name, eloratings_name in TEAM_ALIASES.items()}


def resolve_rating(team_name: str, elo_by_name: dict):
    return elo_by_name.get(TEAM_ALIASES.get(team_name, team_name))


def to_wikipedia_name(team_name: str) -> str:
    """Normalizes an eloratings.net-sourced name back to the Wikipedia naming used elsewhere."""
    return REVERSE_TEAM_ALIASES.get(team_name, team_name)
