import type { ResultMatch } from "./types";
import { getGroups, getResults } from "./data";

const COMBINING_DIACRITICS = /[̀-ͯ]/g;

export function slugify(value: string): string {
  return value
    .normalize("NFD")
    .replace(COMBINING_DIACRITICS, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function allTeamNames(): string[] {
  const groups = getGroups().groups;
  return Object.values(groups)
    .flat()
    .map((entry) => entry.team);
}

export function teamNameBySlug(slug: string): string | undefined {
  return allTeamNames().find((name) => slugify(name) === slug);
}

export function matchSlug(match: ResultMatch, index: number): string {
  const date = match.date ?? "tbd";
  return `${slugify(match.home_team)}-vs-${slugify(match.away_team)}-${date}-${index}`;
}

export function matchByValidatedSlug(slug: string): { match: ResultMatch; index: number } | undefined {
  const matches = getResults().matches;
  const index = matches.findIndex((m, i) => matchSlug(m, i) === slug);
  return index === -1 ? undefined : { match: matches[index], index };
}
