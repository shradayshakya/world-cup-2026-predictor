import type { GroupStanding, PredictedMatch, ProbabilitiesData, ResultMatch } from "@/lib/types";
import { formatPercent } from "@/lib/format";
import TeamLink from "./TeamLink";
import EliminatedBadge from "./EliminatedBadge";
import MatchCard from "./MatchCard";

export default function GroupTable({
  letter,
  standings,
  probabilities,
  fixtures,
}: {
  letter: string;
  standings: GroupStanding[];
  probabilities: ProbabilitiesData["teams"];
  fixtures: Array<{ match: ResultMatch; index: number; prediction: PredictedMatch | null }>;
}) {
  const remaining = fixtures.filter((f) => !f.match.played);

  return (
    <section id={`group-${letter}`} className="scroll-mt-20">
      <h2 className="text-xl font-semibold">Group {letter}</h2>
      <div className="mt-2 overflow-x-auto">
        <table className="w-full min-w-[640px] text-sm">
          <thead>
            <tr className="border-b border-neutral-200 text-left text-neutral-500">
              <th className="py-1 pr-2">#</th>
              <th className="py-1 pr-2">Team</th>
              <th className="px-1 text-center">P</th>
              <th className="px-1 text-center">W</th>
              <th className="px-1 text-center">D</th>
              <th className="px-1 text-center">L</th>
              <th className="px-1 text-center">GD</th>
              <th className="px-1 text-center">Pts</th>
              <th className="px-1 text-center">1st</th>
              <th className="px-1 text-center">2nd</th>
              <th className="px-1 text-center">Adv.</th>
              <th className="py-1 pl-2"></th>
            </tr>
          </thead>
          <tbody>
            {standings.map((s) => {
              const stats = probabilities[s.team];
              const eliminated = (stats?.advanced_to_r32 ?? 0) === 0;
              return (
                <tr key={s.team} className="border-b border-neutral-100">
                  <td className="py-1.5 pr-2 text-neutral-500">{s.position}</td>
                  <td className="py-1.5 pr-2">
                    <TeamLink name={s.team} />
                    {s.host && <span className="ml-1 text-xs text-neutral-400">(H)</span>}
                  </td>
                  <td className="px-1 text-center">{s.played}</td>
                  <td className="px-1 text-center">{s.won}</td>
                  <td className="px-1 text-center">{s.drawn}</td>
                  <td className="px-1 text-center">{s.lost}</td>
                  <td className="px-1 text-center">{s.goal_difference}</td>
                  <td className="px-1 text-center font-semibold">{s.points}</td>
                  <td className="px-1 text-center text-neutral-500">{formatPercent(stats?.group_winner, 0)}</td>
                  <td className="px-1 text-center text-neutral-500">{formatPercent(stats?.group_runner_up, 0)}</td>
                  <td className="px-1 text-center text-neutral-500">{formatPercent(stats?.advanced_to_r32, 0)}</td>
                  <td className="py-1.5 pl-2">{eliminated && <EliminatedBadge />}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {remaining.length > 0 && (
        <div className="mt-3 grid gap-2 sm:grid-cols-2">
          {remaining.map((f) => (
            <MatchCard key={f.index} match={f.match} index={f.index} prediction={f.prediction} />
          ))}
        </div>
      )}
    </section>
  );
}
