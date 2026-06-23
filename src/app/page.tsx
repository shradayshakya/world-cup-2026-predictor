import TournamentWinnerBar from "@/components/TournamentWinnerBar";
import MatchCard from "@/components/MatchCard";
import AiSummaryBadge from "@/components/AiSummaryBadge";
import TeamLink from "@/components/TeamLink";
import { getMovers, getResults } from "@/lib/data";
import { getPredictionFor } from "@/lib/predictions";

const NEXT_MATCHES_COUNT = 4;

export default function Home() {
  const results = getResults();
  // "Next N unplayed matches" rather than "today's matches" -- a literal date-string
  // match broke down across the date line between where this runs (Nepal) and where
  // the tournament is played (North America): a match could be genuinely upcoming yet
  // dated for what's already "tomorrow" or "yesterday" relative to either side, so
  // some real upcoming matches just never matched "today" and silently never showed.
  // Sorting by date and taking the next unplayed ones sidesteps that entirely -- no
  // notion of "today" involved, so no timezone to get wrong.
  const upcoming = results.matches
    .map((match, index) => ({ match, index, prediction: getPredictionFor(match) }))
    .filter(({ match }) => !match.played)
    .sort((a, b) => (a.match.date ?? "").localeCompare(b.match.date ?? ""))
    .slice(0, NEXT_MATCHES_COUNT);
  const movers = getMovers().movers;

  return (
    <div className="flex flex-col gap-10">
      <section>
        <h1 className="text-2xl font-bold tracking-tight">Tournament winner probability</h1>
        <p className="mt-1 text-sm text-neutral-500">
          Live contenders only — eliminated teams are excluded. Hover or tap a segment for the exact number.
        </p>
        <div className="mt-4">
          <TournamentWinnerBar />
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold">Next matches</h2>
        {upcoming.length === 0 ? (
          <p className="mt-2 text-sm text-neutral-500">No upcoming matches on file.</p>
        ) : (
          <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {upcoming.map(({ match, index, prediction }) => (
              <MatchCard key={index} match={match} index={index} prediction={prediction} />
            ))}
          </div>
        )}
      </section>

      {movers.length > 0 && (
        <section>
          <h2 className="text-xl font-semibold">Biggest movers</h2>
          <div className="mt-3 flex flex-col gap-3">
            {movers.map((m) => (
              <div key={m.team} className="rounded-md border border-neutral-200 p-3">
                <div className="flex items-baseline gap-2">
                  <span className={m.direction === "gainer" ? "text-emerald-600" : "text-red-600"}>
                    {m.direction === "gainer" ? "▲" : "▼"}
                  </span>
                  <TeamLink name={m.team} className="font-semibold hover:underline" />
                  <span className="text-sm text-neutral-500">
                    {m.previous_pct.toFixed(1)}% → {m.current_pct.toFixed(1)}% ({m.delta_pp > 0 ? "+" : ""}
                    {m.delta_pp.toFixed(1)}pp)
                  </span>
                </div>
                <p className="mt-1 text-sm text-neutral-600">{m.blurb}</p>
                <AiSummaryBadge sources={m.sources} />
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
