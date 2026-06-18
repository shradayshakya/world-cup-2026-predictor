// Mirrors scripts/model/teams.py's TEAM_ALIASES: Wikipedia naming -> eloratings.net naming.
const TEAM_ALIASES: Record<string, string> = {
  "Czech Republic": "Czechia",
};

export function resolveEloName(wikipediaName: string): string {
  return TEAM_ALIASES[wikipediaName] ?? wikipediaName;
}
