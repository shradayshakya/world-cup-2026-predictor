import type { PredictedMatch, ResultMatch } from "./types";
import { getMatches } from "./data";

function key(home: string, away: string, date: string | null): string {
  return `${home}|${away}|${date ?? ""}`;
}

let cache: Map<string, PredictedMatch> | null = null;

function predictionsByKey(): Map<string, PredictedMatch> {
  if (!cache) {
    cache = new Map(getMatches().matches.map((m) => [key(m.home_team, m.away_team, m.date), m]));
  }
  return cache;
}

export function getPredictionFor(match: ResultMatch): PredictedMatch | null {
  return predictionsByKey().get(key(match.home_team, match.away_team, match.date)) ?? null;
}
