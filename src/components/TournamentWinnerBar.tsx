import { getProbabilities } from "@/lib/data";
import { formatPercent } from "@/lib/format";
import { slugify } from "@/lib/slug";
import Link from "next/link";

function colorForIndex(index: number): string {
  const hue = (index * 37) % 360;
  return `hsl(${hue}, 60%, 55%)`;
}

export default function TournamentWinnerBar() {
  const teams = getProbabilities().teams;
  const ranked = Object.entries(teams)
    .map(([name, stats]) => ({ name, probability: stats.won_tournament ?? 0 }))
    .filter((t) => t.probability > 0)
    .sort((a, b) => b.probability - a.probability);

  if (ranked.length === 0) {
    return <p className="text-sm text-neutral-500">No live contenders yet.</p>;
  }

  return (
    <div>
      <div className="flex h-10 w-full overflow-hidden rounded-md border border-neutral-200">
        {ranked.map((team, i) => (
          <Link
            key={team.name}
            href={`/teams/${slugify(team.name)}`}
            title={`${team.name}: ${formatPercent(team.probability)}`}
            style={{ width: `${team.probability * 100}%`, backgroundColor: colorForIndex(i) }}
            className="h-full transition-opacity hover:opacity-80"
          />
        ))}
      </div>
      <ol className="mt-3 grid grid-cols-2 gap-1 text-sm sm:grid-cols-4">
        {ranked.slice(0, 12).map((team, i) => (
          <li key={team.name} className="flex items-center gap-1.5">
            <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: colorForIndex(i) }} />
            <Link href={`/teams/${slugify(team.name)}`} className="hover:underline">
              {team.name}
            </Link>
            <span className="text-neutral-500">{formatPercent(team.probability)}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}
