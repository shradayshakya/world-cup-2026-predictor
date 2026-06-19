import Link from "next/link";
import ChangeArrow from "./ChangeArrow";
import { formatPercent } from "@/lib/format";

export interface BracketSide {
  name: string;
  probability?: number;
  deltaPp?: number;
  confirmed: boolean;
}

// Plain text, not a link: the node is already an <a> to the match page, and
// nesting an <a> inside an <a> is invalid HTML (breaks hydration).
function SideRow({ side }: { side: BracketSide }) {
  return (
    <div className="flex items-center justify-between gap-2 px-2 py-1">
      <span className={side.confirmed ? "truncate" : "truncate text-neutral-500"}>{side.name}</span>
      {!side.confirmed && side.probability !== undefined && (
        <span className="shrink-0 whitespace-nowrap text-xs text-neutral-400">
          {formatPercent(side.probability, 0)}
          <ChangeArrow deltaPp={side.deltaPp} />
        </span>
      )}
    </div>
  );
}

export default function BracketNode({ home, away, href }: { home: BracketSide; away: BracketSide; href?: string }) {
  const content = (
    <div className="w-44 divide-y divide-neutral-200 rounded-md border border-neutral-200 bg-white text-sm">
      <SideRow side={home} />
      <SideRow side={away} />
    </div>
  );
  return href ? (
    <Link href={href} className="block hover:border-neutral-400">
      {content}
    </Link>
  ) : (
    content
  );
}
