import TournamentWinnerBar from "@/components/TournamentWinnerBar";
import MatchCard from "@/components/MatchCard";
import AiSummaryBadge from "@/components/AiSummaryBadge";
import TeamLink from "@/components/TeamLink";
import { getLastUpdated, getMovers, getResults } from "@/lib/data";
import { getPredictionFor } from "@/lib/predictions";

export default function Home() {
  const today = getLastUpdated().slice(0, 10);
  const results = getResults();
  const todaysMatches = results.matches
    .map((match, index) => ({ match, index }))
    .filter(({ match }) => match.date === today);
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
        <h2 className="text-xl font-semibold">Today&apos;s matches</h2>
        {todaysMatches.length === 0 ? (
          <p className="mt-2 text-sm text-neutral-500">No matches scheduled today.</p>
        ) : (
          <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {todaysMatches.map(({ match, index }) => (
              <MatchCard key={index} match={match} index={index} prediction={getPredictionFor(match)} />
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
