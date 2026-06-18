import { notFound } from "next/navigation";
import MatchCard from "@/components/MatchCard";
import { getElo, getForm, getGroups, getProbabilities, getResults } from "@/lib/data";
import { getPredictionFor } from "@/lib/predictions";
import { allTeamNames, slugify, teamNameBySlug } from "@/lib/slug";
import { resolveEloName } from "@/lib/teamAliases";
import { formatPercent } from "@/lib/format";

export function generateStaticParams() {
  return allTeamNames().map((name) => ({ slug: slugify(name) }));
}

const STAGE_LABELS: Array<[string, string]> = [
  ["group_winner", "Win group"],
  ["group_runner_up", "Finish 2nd"],
  ["group_third_advanced", "Advance as 3rd"],
  ["advanced_to_r32", "Reach Round of 32"],
  ["reached_r16", "Reach Round of 16"],
  ["reached_qf", "Reach quarter-finals"],
  ["reached_sf", "Reach semi-finals"],
  ["reached_final", "Reach final"],
  ["won_tournament", "Win the tournament"],
];

export default async function TeamPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const name = teamNameBySlug(slug);
  if (!name) notFound();

  const groups = getGroups().groups;
  const groupLetter = Object.keys(groups).find((letter) => groups[letter].some((e) => e.team === name));
  const standing = groupLetter ? groups[groupLetter].find((e) => e.team === name) : undefined;

  const eloTeam = getElo().teams.find((t) => t.name === resolveEloName(name));
  const stats = getProbabilities().teams[name] ?? {};
  const form = getForm().teams[name] ?? [];

  const remainingFixtures = getResults()
    .matches.map((match, index) => ({ match, index }))
    .filter(({ match }) => !match.played && (match.home_team === name || match.away_team === name));

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{name}</h1>
        <p className="mt-1 text-sm text-neutral-500">
          {groupLetter && `Group ${groupLetter}, position ${standing?.position}`}
          {eloTeam && ` · Elo rating ${eloTeam.rating} (world rank #${eloTeam.rank})`}
        </p>
      </div>

      <section>
        <h2 className="text-lg font-semibold">Tournament probabilities</h2>
        <dl className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-3">
          {STAGE_LABELS.map(([key, label]) => (
            <div key={key} className="rounded-md border border-neutral-200 p-2">
              <dt className="text-xs text-neutral-500">{label}</dt>
              <dd className="text-lg font-semibold">{formatPercent(stats[key as keyof typeof stats])}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section>
        <h2 className="text-lg font-semibold">Recent form</h2>
        {form.length === 0 ? (
          <p className="mt-2 text-sm text-neutral-500">No recent results on file.</p>
        ) : (
          <div className="mt-2 flex flex-col gap-1">
            <div className="flex gap-1">
              {form.map((m, i) => (
                <span
                  key={i}
                  title={`${m.result} vs ${m.opponent} (${m.goals_for}-${m.goals_against}, ${m.date})`}
                  className={`flex h-6 w-6 items-center justify-center rounded-sm text-xs font-semibold text-white ${
                    m.result === "W" ? "bg-emerald-500" : m.result === "L" ? "bg-red-500" : "bg-neutral-400"
                  }`}
                >
                  {m.result}
                </span>
              ))}
            </div>
            <ul className="mt-2 text-sm text-neutral-600">
              {form.map((m, i) => (
                <li key={i}>
                  {m.date} — {m.result} {m.goals_for}-{m.goals_against} vs {m.opponent} ({m.tournament})
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>

      <section>
        <h2 className="text-lg font-semibold">Remaining fixtures</h2>
        {remainingFixtures.length === 0 ? (
          <p className="mt-2 text-sm text-neutral-500">No remaining fixtures on file.</p>
        ) : (
          <div className="mt-2 grid gap-2 sm:grid-cols-2">
            {remainingFixtures.map(({ match, index }) => (
              <MatchCard key={index} match={match} index={index} prediction={getPredictionFor(match)} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
