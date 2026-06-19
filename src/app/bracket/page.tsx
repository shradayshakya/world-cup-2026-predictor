import BracketNode, { type BracketSide } from "@/components/BracketNode";
import BracketRound from "@/components/BracketRound";
import { getBracket, getProbabilityChanges, getResults } from "@/lib/data";
import { allTeamNames, matchSlug } from "@/lib/slug";
import type { BracketSlot, ResultMatch } from "@/lib/types";

function sideFor(name: string, slotSide: BracketSlot["home"], knownTeams: Set<string>, deltaPp: number | undefined): BracketSide {
  if (knownTeams.has(name)) {
    return { name, confirmed: true };
  }
  return { name: slotSide?.team ?? name, probability: slotSide?.probability, deltaPp, confirmed: false };
}

function roundEntries(allMatches: Array<{ match: ResultMatch; index: number }>, round: string) {
  return allMatches.filter(({ match }) => match.round === round);
}

export default function BracketPage() {
  const bracket = getBracket();
  const bracketChanges = getProbabilityChanges().bracket;
  const knownTeams = new Set(allTeamNames());
  const allMatches = getResults().matches.map((match, index) => ({ match, index }));

  const rounds: Array<{ title: string; round: string; roundKey: string; slots: BracketSlot[] }> = [
    { title: "Round of 32", round: "Round of 32", roundKey: "round_of_32", slots: bracket.round_of_32 },
    { title: "Round of 16", round: "Round of 16", roundKey: "round_of_16", slots: bracket.round_of_16 },
    { title: "Quarter-finals", round: "Quarter-finals", roundKey: "quarter_finals", slots: bracket.quarter_finals },
    { title: "Semi-finals", round: "Semi-finals", roundKey: "semi_finals", slots: bracket.semi_finals },
  ];

  return (
    <div className="flex flex-col gap-10">
      <h1 className="text-2xl font-bold tracking-tight">Knockout bracket</h1>
      <p className="text-sm text-neutral-500">
        Where a slot isn&apos;t determined yet, it shows our model&apos;s most likely occupant and the probability of that team
        landing there.
      </p>

      <div className="flex flex-wrap gap-10 overflow-x-auto">
        {rounds.map(({ title, round, roundKey, slots }) => {
          const entries = roundEntries(allMatches, round);
          return (
            <BracketRound key={round} title={title}>
              {slots.map((slot, i) => {
                const entry = entries[i];
                const home = sideFor(entry.match.home_team, slot.home, knownTeams, bracketChanges[`${roundKey}|${i}|home`]);
                const away = sideFor(entry.match.away_team, slot.away, knownTeams, bracketChanges[`${roundKey}|${i}|away`]);
                return (
                  <BracketNode key={i} home={home} away={away} href={`/matches/${matchSlug(entry.match, entry.index)}`} />
                );
              })}
            </BracketRound>
          );
        })}

        <div className="flex flex-col gap-10">
          <BracketRound title="Final">
            {(() => {
              const entry = roundEntries(allMatches, "Final")[0];
              const home = sideFor(entry.match.home_team, bracket.final.home, knownTeams, bracketChanges["final|0|home"]);
              const away = sideFor(entry.match.away_team, bracket.final.away, knownTeams, bracketChanges["final|0|away"]);
              return <BracketNode home={home} away={away} href={`/matches/${matchSlug(entry.match, entry.index)}`} />;
            })()}
          </BracketRound>
          <BracketRound title="Third place play-off">
            {(() => {
              const entry = roundEntries(allMatches, "Third place play-off")[0];
              const home = sideFor(entry.match.home_team, bracket.third_place.home, knownTeams, bracketChanges["third_place|0|home"]);
              const away = sideFor(entry.match.away_team, bracket.third_place.away, knownTeams, bracketChanges["third_place|0|away"]);
              return <BracketNode home={home} away={away} href={`/matches/${matchSlug(entry.match, entry.index)}`} />;
            })()}
          </BracketRound>
        </div>
      </div>
    </div>
  );
}
