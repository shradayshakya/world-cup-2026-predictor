import Link from "next/link";
import type { PredictedMatch, ResultMatch } from "@/lib/types";
import { formatDate } from "@/lib/format";
import { matchSlug } from "@/lib/slug";

// Plain text, not a link: this whole card is already an <a> to the match page,
// and nesting an <a> inside an <a> is invalid HTML (breaks hydration).
function TeamLabel({ name }: { name: string }) {
  const isPlaceholder = name.startsWith("Winner") || name.startsWith("Runner-up") || /^\d/.test(name);
  return <span className={isPlaceholder ? "text-neutral-500" : undefined}>{name}</span>;
}

export default function MatchCard({
  match,
  index,
  prediction,
}: {
  match: ResultMatch;
  index: number;
  prediction?: PredictedMatch | null;
}) {
  return (
    <Link
      href={`/matches/${matchSlug(match, index)}`}
      className="block rounded-md border border-neutral-200 p-3 hover:border-neutral-400"
    >
      <div className="text-xs text-neutral-500">
        {formatDate(match.date)} · {match.group ? `Group ${match.group}` : match.round}
      </div>
      <div className="mt-1 flex items-center justify-between gap-2">
        <span className="truncate">
          <TeamLabel name={match.home_team} />
        </span>
        <span className="shrink-0 font-mono text-sm">
          {match.played
            ? `${match.home_score} – ${match.away_score}`
            : prediction
              ? `${prediction.prediction.predicted_home_score} – ${prediction.prediction.predicted_away_score}`
              : "vs"}
        </span>
        <span className="truncate text-right">
          <TeamLabel name={match.away_team} />
        </span>
      </div>
      {!match.played && prediction && <div className="mt-1 text-xs text-neutral-400">predicted</div>}
    </Link>
  );
}
