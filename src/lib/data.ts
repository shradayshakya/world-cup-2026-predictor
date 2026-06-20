import eloRaw from "../../public/data/elo.json";
import groupsRaw from "../../public/data/groups.json";
import resultsRaw from "../../public/data/results.json";
import matchesRaw from "../../public/data/matches.json";
import probabilitiesRaw from "../../public/data/probabilities.json";
import formRaw from "../../public/data/form.json";
import bracketRaw from "../../public/data/bracket.json";
import squadsRaw from "../../public/data/squads.json";
import injuriesRaw from "../../public/data/injuries.json";
import moversRaw from "../../public/data/movers.json";
import previewsRaw from "../../public/data/previews.json";
import calibrationLogRaw from "../../public/data/calibration_log.json";
import probabilityChangesRaw from "../../public/data/probability_changes.json";
import maintenanceRaw from "../../public/data/maintenance.json";
import topScorersRaw from "../../public/data/top_scorers.json";
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
  MoversData,
  PreviewsData,
  CalibrationLog,
  ProbabilityChangesData,
  MaintenanceData,
  TopScorersData,
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

export function getMovers(): MoversData {
  return moversRaw as MoversData;
}

export function getPreviews(): PreviewsData {
  return previewsRaw as PreviewsData;
}

export function getCalibrationLog(): CalibrationLog {
  return calibrationLogRaw as CalibrationLog;
}

export function getProbabilityChanges(): ProbabilityChangesData {
  return probabilityChangesRaw as ProbabilityChangesData;
}

export function getMaintenance(): MaintenanceData {
  return maintenanceRaw as MaintenanceData;
}

export function getTopScorers(): TopScorersData {
  return topScorersRaw as TopScorersData;
}

export function getLastUpdated(): string {
  return getProbabilities().generated_at;
}
