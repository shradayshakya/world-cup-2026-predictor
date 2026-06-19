export interface EloTeam {
  rank: number;
  code: string;
  name: string;
  rating: number;
}

export interface EloData {
  teams: EloTeam[];
  scraped_at: string;
}

export interface GroupStanding {
  position: number;
  team: string;
  host: boolean;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  points: number;
  qualification_note: string;
}

export interface GroupsData {
  scraped_at: string;
  groups: Record<string, GroupStanding[]>;
}

export interface ResultMatch {
  round: string;
  group: string | null;
  date: string | null;
  home_team: string;
  away_team: string;
  played: boolean;
  home_score: number | null;
  away_score: number | null;
  venue: string | null;
  attendance: number | null;
  referee: string | null;
}

export interface ResultsData {
  scraped_at: string;
  matches: ResultMatch[];
}

export interface MatchPrediction {
  predicted_home_score: number;
  predicted_away_score: number;
  home_win_probability: number;
  draw_probability: number;
  away_win_probability: number;
  score_grid: number[][];
}

export interface EloWinExpectancy {
  home: number;
  away: number;
}

export interface PredictedMatch {
  round: string;
  group: string | null;
  date: string | null;
  home_team: string;
  away_team: string;
  venue: string | null;
  prediction: MatchPrediction;
  elo_win_expectancy: EloWinExpectancy | null;
}

export interface MatchesData {
  matches: PredictedMatch[];
  generated_at: string;
}

export interface TeamStageProbabilities {
  group_winner?: number;
  group_runner_up?: number;
  group_third?: number;
  group_third_advanced?: number;
  group_fourth?: number;
  advanced_to_r32?: number;
  reached_r16?: number;
  reached_qf?: number;
  reached_sf?: number;
  reached_final?: number;
  won_tournament?: number;
  won_third_place_match?: number;
}

export interface ProbabilitiesData {
  n_simulations: number;
  teams: Record<string, TeamStageProbabilities>;
  generated_at: string;
}

export interface FormMatch {
  date: string;
  opponent: string;
  goals_for: number;
  goals_against: number;
  result: "W" | "D" | "L";
  tournament: string;
  venue: string | null;
}

export interface FormData {
  generated_at: string;
  teams: Record<string, FormMatch[]>;
}

export interface BracketOccupant {
  team: string;
  probability: number;
}

export interface BracketSlot {
  home: BracketOccupant | null;
  away: BracketOccupant | null;
}

export interface BracketData {
  round_of_32: BracketSlot[];
  round_of_16: BracketSlot[];
  quarter_finals: BracketSlot[];
  semi_finals: BracketSlot[];
  final: BracketSlot;
  third_place: BracketSlot;
  generated_at: string;
}

export interface SquadPlayer {
  name: string;
  captain: boolean;
  position: string;
  caps: number;
  goals: number;
  club: string;
}

export interface SquadsData {
  scraped_at: string;
  squads: Record<string, SquadPlayer[]>;
}

export interface InjuryAbsence {
  player: string;
  status: "out" | "doubt" | "suspended";
  until: string | null;
  key_player: boolean;
  source_title: string;
  source_link: string;
}

export interface TeamInjuries {
  elo_penalty: number;
  absences: InjuryAbsence[];
}

export interface InjuriesData {
  generated_at: string;
  teams: Record<string, TeamInjuries>;
}

export interface AiSource {
  label: string;
  href: string;
}

export interface Mover {
  team: string;
  previous_pct: number;
  current_pct: number;
  delta_pp: number;
  direction: "gainer" | "loser";
  blurb: string;
  sources: AiSource[];
}

export interface MoversData {
  generated_at: string;
  movers: Mover[];
}

export interface MatchPreview {
  text: string;
  sources: AiSource[];
}

export interface PreviewsData {
  generated_at: string;
  previews: Record<string, MatchPreview>;
}

export interface CalibrationEntry {
  date: string;
  home_team: string;
  away_team: string;
  predicted_home_score: number;
  predicted_away_score: number;
  home_win_probability: number;
  draw_probability: number;
  away_win_probability: number;
  actual_home_score: number;
  actual_away_score: number;
  actual_outcome: "home" | "draw" | "away";
  brier_score: number;
  log_loss: number;
  scoreline_correct: boolean;
}

export interface CalibrationSummary {
  n: number;
  avg_brier_score: number | null;
  avg_log_loss: number | null;
  scoreline_accuracy: number | null;
}

export interface CalibrationLog {
  entries: CalibrationEntry[];
  summary: CalibrationSummary;
}

export type TeamChanges = Partial<Record<keyof TeamStageProbabilities, number>>;

export interface MatchChanges {
  home_win_probability?: number;
  draw_probability?: number;
  away_win_probability?: number;
}

export interface ProbabilityChangesData {
  generated_at: string;
  teams: Record<string, TeamChanges>;
  matches: Record<string, MatchChanges>;
  bracket: Record<string, number>;
}

export interface MaintenanceIssue {
  source: "wikipedia_groups" | "wikipedia_matches" | "squads";
  detail: string;
  fallback_attempted: boolean;
  fallback_succeeded: boolean | null;
}

export interface MaintenanceData {
  generated_at: string;
  issues: MaintenanceIssue[];
}
