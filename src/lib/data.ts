import eloRaw from "../../public/data/elo.json";
import groupsRaw from "../../public/data/groups.json";
import resultsRaw from "../../public/data/results.json";
import matchesRaw from "../../public/data/matches.json";
import probabilitiesRaw from "../../public/data/probabilities.json";
import formRaw from "../../public/data/form.json";
import bracketRaw from "../../public/data/bracket.json";
import squadsRaw from "../../public/data/squads.json";
import injuriesRaw from "../../public/data/injuries.json";
import type {
  EloData,
  GroupsData,
  ResultsData,
  MatchesData,
  ProbabilitiesData,
  FormData,
  BracketData,
  SquadsData,
  InjuriesData,
} from "./types";

export function getElo(): EloData {
  return eloRaw as EloData;
}

export function getGroups(): GroupsData {
  return groupsRaw as GroupsData;
}

export function getResults(): ResultsData {
  return resultsRaw as ResultsData;
}

export function getMatches(): MatchesData {
  return matchesRaw as MatchesData;
}

export function getProbabilities(): ProbabilitiesData {
  return probabilitiesRaw as ProbabilitiesData;
}

export function getForm(): FormData {
  return formRaw as FormData;
}

export function getBracket(): BracketData {
  return bracketRaw as BracketData;
}

export function getSquads(): SquadsData {
  return squadsRaw as SquadsData;
}

export function getInjuries(): InjuriesData {
  return injuriesRaw as InjuriesData;
}

export function getLastUpdated(): string {
  return getProbabilities().generated_at;
}
