import type { AiSource } from "@/lib/types";

export default function AiSummaryBadge({ sources }: { sources: AiSource[] }) {
  return (
    <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-neutral-400">
      <span className="rounded-sm bg-violet-100 px-1.5 py-0.5 font-semibold uppercase tracking-wide text-violet-700">
        AI summary
      </span>
      {sources.length > 0 && (
        <span>
          Sources:{" "}
          {sources.map((s, i) => (
            <span key={i}>
              {i > 0 && ", "}
              <a href={s.href} className="hover:underline">
                {s.label}
              </a>
            </span>
          ))}
        </span>
      )}
    </div>
  );
}
