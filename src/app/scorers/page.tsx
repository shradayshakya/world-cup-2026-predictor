import TeamLink from "@/components/TeamLink";
import { getTopScorers } from "@/lib/data";

export default function ScorersPage() {
  const { scorers } = getTopScorers();

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Predicted top scorers</h1>
        <p className="mt-2 max-w-2xl text-sm text-neutral-600">
          Each team&apos;s Monte Carlo-simulated total tournament goals, distributed to players by their share of the
          squad&apos;s historical (pre-tournament career) goals, adjusted for current injury/suspension status. This is a
          forward-looking estimate, not a running tally of goals actually scored at this World Cup — we don&apos;t track
          individual match goal-scorers, only who&apos;s historically been a team&apos;s most prolific finisher.
        </p>
      </div>

      {scorers.length === 0 ? (
        <p className="text-sm text-neutral-500">No predictions on file yet.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[280px] text-sm sm:min-w-[420px]">
            <thead>
              <tr className="border-b border-neutral-200 text-left text-neutral-500">
                <th className="py-1 pr-2">#</th>
                <th className="py-1 pr-2">Player</th>
                <th className="py-1 pr-2">Team</th>
                <th className="hidden px-1 text-center sm:table-cell">Pos</th>
                <th className="px-1 text-center">Predicted</th>
                <th className="hidden px-1 text-center sm:table-cell">Career goals</th>
              </tr>
            </thead>
            <tbody>
              {scorers.map((s, i) => (
                <tr key={`${s.team}-${s.player}`} className="border-b border-neutral-100">
                  <td className="py-1.5 pr-2 text-neutral-500">{i + 1}</td>
                  <td className="py-1.5 pr-2 font-medium">{s.player}</td>
                  <td className="py-1.5 pr-2">
                    <TeamLink name={s.team} />
                  </td>
                  <td className="hidden px-1 text-center text-neutral-500 sm:table-cell">{s.position}</td>
                  <td className="px-1 text-center font-semibold">{s.predicted_goals}</td>
                  <td className="hidden px-1 text-center text-neutral-500 sm:table-cell">{s.historical_goals}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
