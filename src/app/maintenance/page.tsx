import { getMaintenance } from "@/lib/data";
import { formatTimestamp } from "@/lib/format";

const SOURCE_LABELS: Record<string, string> = {
  wikipedia_groups: "Wikipedia (group standings)",
  wikipedia_matches: "Wikipedia (matches)",
  squads: "Wikipedia (squads)",
};

export default function MaintenancePage() {
  const { generated_at, issues } = getMaintenance();

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Maintenance</h1>
        <p className="mt-2 max-w-2xl text-sm text-neutral-600">
          Internal page (not linked in navigation): sanity-check failures from the daily scrapers, and whether the
          Ollama extraction fallback recovered usable data (PRD.md §7/§11 Phase 5c). An empty list means every
          structured parser&apos;s output looked self-consistent on the last run.
        </p>
        {generated_at && <p className="mt-1 text-xs text-neutral-400">Last run: {formatTimestamp(generated_at)} UTC</p>}
      </div>

      {issues.length === 0 ? (
        <p className="text-sm text-neutral-500">No issues on the last run.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[480px] text-sm">
            <thead>
              <tr className="border-b border-neutral-200 text-left text-neutral-500">
                <th className="py-1 pr-2">Source</th>
                <th className="py-1 pr-2">Detail</th>
                <th className="px-1 text-center">Fallback</th>
              </tr>
            </thead>
            <tbody>
              {issues.map((issue, i) => (
                <tr key={i} className="border-b border-neutral-100 align-top">
                  <td className="py-1.5 pr-2 whitespace-nowrap text-neutral-500">{SOURCE_LABELS[issue.source] ?? issue.source}</td>
                  <td className="py-1.5 pr-2">{issue.detail}</td>
                  <td className="px-1 text-center">
                    {!issue.fallback_attempted
                      ? "not attempted"
                      : issue.fallback_succeeded
                        ? "recovered"
                        : "failed — manual fix needed"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
