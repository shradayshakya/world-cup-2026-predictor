import Link from "next/link";
import { getCalibrationLog, getResults } from "@/lib/data";
import { formatPercent } from "@/lib/format";
import { matchSlug } from "@/lib/slug";
import type { CalibrationEntry } from "@/lib/types";

function outcomeLabel(outcome: "home" | "draw" | "away", e: CalibrationEntry): string {
  if (outcome === "draw") return "Draw";
  return outcome === "home" ? e.home_team : e.away_team;
}

export default function AboutPage() {
  const { entries, summary } = getCalibrationLog();
  const results = getResults().matches;

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">About &amp; calibration</h1>
        <p className="mt-2 max-w-2xl text-sm text-neutral-600">
          This site predicts the 2026 FIFA World Cup using a Poisson-Elo match model and a 50,000-run Monte Carlo
          tournament simulation, refreshed daily. After each match, we compare our prediction to the actual result and
          log it here, so the model&apos;s track record is auditable rather than just asserted.
        </p>
      </div>

      <section>
        <h2 className="text-lg font-semibold">Track record</h2>
        {summary.n === 0 ? (
          <p className="mt-2 text-sm text-neutral-500">No matches scored yet — check back once some have been played.</p>
        ) : (
          <dl className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-5">
            <div className="rounded-md border border-neutral-200 p-2">
              <dt className="text-xs text-neutral-500">Matches scored</dt>
              <dd className="text-lg font-semibold">{summary.n}</dd>
            </div>
            <div className="rounded-md border border-neutral-200 p-2">
              <dt className="text-xs text-neutral-500">Avg Brier score</dt>
              <dd className="text-lg font-semibold">{summary.avg_brier_score?.toFixed(3)}</dd>
            </div>
            <div className="rounded-md border border-neutral-200 p-2">
              <dt className="text-xs text-neutral-500">Avg log-loss</dt>
              <dd className="text-lg font-semibold">{summary.avg_log_loss?.toFixed(3)}</dd>
            </div>
            <div className="rounded-md border border-neutral-200 p-2">
              <dt className="text-xs text-neutral-500">Win/draw/loss accuracy</dt>
              <dd className="text-lg font-semibold">{formatPercent(summary.outcome_accuracy ?? undefined, 0)}</dd>
            </div>
            <div className="rounded-md border border-neutral-200 p-2">
              <dt className="text-xs text-neutral-500">Exact scoreline accuracy</dt>
              <dd className="text-lg font-semibold">{formatPercent(summary.scoreline_accuracy ?? undefined, 0)}</dd>
            </div>
          </dl>
        )}
        <p className="mt-2 text-xs text-neutral-500">
          Brier score (0 = perfect, 2 = worst possible for a 3-way outcome) and log-loss are both scored on the
          home/draw/away win probabilities, not the exact scoreline. &quot;Win/draw/loss accuracy&quot; is a coarser,
          easier bar than the exact scoreline — did we call the winner (or draw) right, regardless of the final score.
        </p>
      </section>

      {entries.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold">Match-by-match</h2>
          <div className="mt-2 overflow-x-auto">
            <table className="w-full min-w-[360px] text-sm sm:min-w-[720px]">
              <thead>
                <tr className="border-b border-neutral-200 text-left text-neutral-500">
                  <th className="py-1 pr-2">Date</th>
                  <th className="py-1 pr-2">Match</th>
                  <th className="px-1 text-center">Predicted</th>
                  <th className="px-1 text-center">Actual</th>
                  <th className="hidden px-1 text-center sm:table-cell">Brier</th>
                  <th className="hidden px-1 text-center sm:table-cell">Log-loss</th>
                  <th className="px-1 text-center">Winner</th>
                  <th className="px-1 text-center">Score</th>
                </tr>
              </thead>
              <tbody>
                {entries
                  .slice()
                  .reverse()
                  .map((e) => {
                    const index = results.findIndex(
                      (m) => m.home_team === e.home_team && m.away_team === e.away_team && m.date === e.date,
                    );
                    const href = index === -1 ? null : `/matches/${matchSlug(results[index], index)}`;
                    return (
                      <tr key={`${e.date}-${e.home_team}-${e.away_team}`} className="border-b border-neutral-100">
                        <td className="py-1.5 pr-2 text-neutral-500">{e.date}</td>
                        <td className="py-1.5 pr-2">
                          {href ? (
                            <Link href={href} className="hover:underline">
                              {e.home_team} vs {e.away_team}
                            </Link>
                          ) : (
                            <>
                              {e.home_team} vs {e.away_team}
                            </>
                          )}
                        </td>
                        <td className="px-1 text-center font-mono">
                          {e.predicted_home_score}-{e.predicted_away_score}
                        </td>
                        <td className="px-1 text-center font-mono">
                          {e.actual_home_score}-{e.actual_away_score}
                        </td>
                        <td className="hidden px-1 text-center sm:table-cell">{e.brier_score.toFixed(3)}</td>
                        <td className="hidden px-1 text-center sm:table-cell">{e.log_loss.toFixed(3)}</td>
                        <td
                          className="px-1 text-center"
                          title={`Predicted: ${outcomeLabel(e.predicted_outcome, e)} · Actual: ${outcomeLabel(e.actual_outcome, e)}`}
                        >
                          {e.outcome_correct ? "✓" : ""}
                        </td>
                        <td className="px-1 text-center">{e.scoreline_correct ? "✓" : ""}</td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
