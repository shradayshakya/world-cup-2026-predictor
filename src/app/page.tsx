import TournamentWinnerBar from "@/components/TournamentWinnerBar";
import TodaysMatches from "@/components/TodaysMatches";
import AiSummaryBadge from "@/components/AiSummaryBadge";
import TeamLink from "@/components/TeamLink";
import { getLastUpdated, getMovers, getResults } from "@/lib/data";
import { getPredictionFor } from "@/lib/predictions";

function shiftDate(date: string, days: number): string {
  const d = new Date(`${date}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

export default function Home() {
  const serverToday = getLastUpdated().slice(0, 10);
  const windowStart = shiftDate(serverToday, -1);
  const windowEnd = shiftDate(serverToday, 1);
  const results = getResults();
  const windowed = results.matches
    .map((match, index) => ({ match, index, prediction: getPredictionFor(match) }))
    .filter(({ match }) => match.date !== null && match.date >= windowStart && match.date <= windowEnd);
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
        <TodaysMatches serverToday={serverToday} windowed={windowed} />
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
