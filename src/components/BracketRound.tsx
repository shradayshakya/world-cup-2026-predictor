import type { ReactNode } from "react";

export default function BracketRound({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-4">
      <h3 className="text-sm font-semibold text-neutral-500">{title}</h3>
      <div className="flex flex-col gap-6">{children}</div>
    </div>
  );
}
