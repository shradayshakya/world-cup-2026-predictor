import TournamentWinnerBar from "@/components/TournamentWinnerBar";
import MatchCard from "@/components/MatchCard";
import { getLastUpdated, getResults } from "@/lib/data";
import { getPredictionFor } from "@/lib/predictions";

export default function Home() {
  const today = getLastUpdated().slice(0, 10);
  const results = getResults();
  const todaysMatches = results.matches
    .map((match, index) => ({ match, index }))
    .filter(({ match }) => match.date === today);

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
    </div>
  );
}
