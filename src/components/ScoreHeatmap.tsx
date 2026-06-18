import { formatPercent } from "@/lib/format";

export default function ScoreHeatmap({
  grid,
  homeTeam,
  awayTeam,
}: {
  grid: number[][];
  homeTeam: string;
  awayTeam: string;
}) {
  const max = Math.max(...grid.flat());

  return (
    <div className="overflow-x-auto">
      <p className="mb-1 text-xs text-neutral-500">
        Rows: {homeTeam} goals · Columns: {awayTeam} goals
      </p>
      <table className="border-collapse text-xs">
        <tbody>
          {grid.map((row, h) => (
            <tr key={h}>
              {row.map((p, a) => (
                <td
                  key={a}
                  title={`${h}-${a}: ${formatPercent(p, 2)}`}
                  className="h-9 w-9 text-center font-mono"
                  style={{ backgroundColor: `rgba(37, 99, 235, ${max > 0 ? p / max : 0})` }}
                >
                  {p >= 0.01 ? Math.round(p * 100) : ""}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
