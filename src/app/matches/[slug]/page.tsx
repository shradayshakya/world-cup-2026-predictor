import { notFound } from "next/navigation";
import ScoreHeatmap from "@/components/ScoreHeatmap";
import TeamLink from "@/components/TeamLink";
import { getForm, getResults } from "@/lib/data";
import { formatDate, formatPercent } from "@/lib/format";
import { getPredictionFor } from "@/lib/predictions";
import { matchByValidatedSlug, matchSlug } from "@/lib/slug";

export function generateStaticParams() {
  return getResults().matches.map((match, index) => ({ slug: matchSlug(match, index) }));
}

function headToHead(home: string, away: string) {
  const homeForm = getForm().teams[home] ?? [];
  return homeForm.filter((m) => m.opponent === away);
}

export default async function MatchPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const found = matchByValidatedSlug(slug);
  if (!found) notFound();
  const { match } = found;

  const prediction = !match.played ? getPredictionFor(match) : null;
  const isResolved = match.played || prediction !== null;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <p className="text-sm text-neutral-500">
          {formatDate(match.date)} · {match.group ? `Group ${match.group}` : match.round}
          {match.venue && ` · ${match.venue}`}
        </p>
        <h1 className="mt-1 text-2xl font-bold tracking-tight">
          {isResolved ? (
            <>
              <TeamLink name={match.home_team} /> vs <TeamLink name={match.away_team} />
            </>
          ) : (
            <>
              {match.home_team} vs {match.away_team}
            </>
          )}
        </h1>
      </div>

      {match.played ? (
        <section>
          <p className="text-3xl font-mono font-semibold">
            {match.home_score} – {match.away_score}
          </p>
          {match.attendance && <p className="mt-1 text-sm text-neutral-500">Attendance: {match.attendance.toLocaleString()}</p>}
          {match.referee && <p className="text-sm text-neutral-500">Referee: {match.referee}</p>}
        </section>
      ) : prediction ? (
        <>
          <section>
            <h2 className="text-lg font-semibold">Predicted result</h2>
            <p className="mt-1 text-3xl font-mono font-semibold">
              {prediction.prediction.predicted_home_score} – {prediction.prediction.predicted_away_score}
            </p>
            <div className="mt-2 flex gap-4 text-sm text-neutral-600">
              <span>Home win {formatPercent(prediction.prediction.home_win_probability)}</span>
              <span>Draw {formatPercent(prediction.prediction.draw_probability)}</span>
              <span>Away win {formatPercent(prediction.prediction.away_win_probability)}</span>
            </div>
            {(() => {
              const { predicted_home_score, predicted_away_score, home_win_probability, draw_probability, away_win_probability } =
                prediction.prediction;
              const scorelineOutcome =
                predicted_home_score > predicted_away_score ? "home" : predicted_home_score < predicted_away_score ? "away" : "draw";
              const outcomes = { home: home_win_probability, draw: draw_probability, away: away_win_probability } as const;
              const leadingOutcome = (Object.keys(outcomes) as Array<keyof typeof outcomes>).reduce((a, b) =>
                outcomes[b] > outcomes[a] ? b : a,
              );
              if (scorelineOutcome === leadingOutcome) return null;
              const favoredTeam = leadingOutcome === "home" ? match.home_team : leadingOutcome === "away" ? match.away_team : null;
              return (
                <p className="mt-2 text-sm text-neutral-500">
                  Note: {favoredTeam ? `${favoredTeam} is favored (${formatPercent(outcomes[leadingOutcome])})` : "a draw is the favored outcome"} — the predicted scoreline above is just the single
                  most likely <em>exact</em> result, not the favored outcome. A win can happen via many different scorelines (2-0, 2-1,
                  3-1...), while draws concentrate into fewer cells (0-0, 1-1, 2-2), so a draw scoreline can still be the most probable
                  individual result even when it isn&apos;t the most probable outcome overall.
                </p>
              );
            })()}
            {prediction.elo_win_expectancy && (
              <p className="mt-2 text-sm text-neutral-500">
                According to eloratings.net&apos;s win expectancy: {match.home_team} {prediction.elo_win_expectancy.home}% /{" "}
                {match.away_team} {prediction.elo_win_expectancy.away}%. (Their metric is an Elo &ldquo;expected score&rdquo;
                that blends in draws, not a 3-way split like ours.)
              </p>
            )}
          </section>

          <section>
            <h2 className="text-lg font-semibold">Score distribution</h2>
            <div className="mt-2">
              <ScoreHeatmap grid={prediction.prediction.score_grid} homeTeam={match.home_team} awayTeam={match.away_team} />
            </div>
          </section>

          <section>
            <h2 className="text-lg font-semibold">Recent meetings</h2>
            {(() => {
              const meetings = headToHead(match.home_team, match.away_team);
              return meetings.length === 0 ? (
                <p className="mt-2 text-sm text-neutral-500">No recent meetings on file.</p>
              ) : (
                <ul className="mt-2 text-sm text-neutral-600">
                  {meetings.map((m, i) => (
                    <li key={i}>
                      {m.date} — {match.home_team} {m.goals_for}-{m.goals_against} {match.away_team} ({m.tournament})
                    </li>
                  ))}
                </ul>
              );
            })()}
          </section>
        </>
      ) : (
        <p className="text-sm text-neutral-500">Teams not yet determined — check back once earlier rounds conclude.</p>
      )}
    </div>
  );
}
