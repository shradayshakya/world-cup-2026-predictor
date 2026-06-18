import { formatPercent } from "@/lib/format";

const TOP_N = 6;

function outcomeLabel(homeGoals: number, awayGoals: number, homeTeam: string, awayTeam: string): string {
  if (homeGoals > awayGoals) return `${homeTeam} win`;
  if (homeGoals < awayGoals) return `${awayTeam} win`;
  return "Draw";
}

export default function TopScorelines({
  grid,
  homeTeam,
  awayTeam,
}: {
  grid: number[][];
  homeTeam: string;
  awayTeam: string;
}) {
  const cells = grid.flatMap((row, homeGoals) => row.map((probability, awayGoals) => ({ homeGoals, awayGoals, probability })));
  const top = cells.sort((a, b) => b.probability - a.probability).slice(0, TOP_N);

  return (
    <div>
      <p className="text-sm text-neutral-500">
        The modal scoreline above is just the single highest cell in this list — a favored team&apos;s win probability is usually
        split across many scorelines, while draws concentrate into fewer, so a draw can edge out any one individual win scoreline even
        when wins are more likely overall.
      </p>
      <table className="mt-2 w-full max-w-xs text-sm">
        <thead>
          <tr className="border-b border-neutral-200 text-left text-neutral-500">
            <th className="py-1">Score</th>
            <th className="py-1 text-right">Probability</th>
            <th className="py-1 pl-4">Outcome</th>
          </tr>
        </thead>
        <tbody>
          {top.map(({ homeGoals, awayGoals, probability }) => (
            <tr key={`${homeGoals}-${awayGoals}`} className="border-b border-neutral-100">
              <td className="py-1 font-mono">
                {homeGoals}-{awayGoals}
              </td>
              <td className="py-1 text-right">{formatPercent(probability, 1)}</td>
              <td className="py-1 pl-4 text-neutral-500">{outcomeLabel(homeGoals, awayGoals, homeTeam, awayTeam)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
