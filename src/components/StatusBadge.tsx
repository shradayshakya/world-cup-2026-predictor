const LABELS: Record<string, string> = { out: "OUT", doubt: "DOUBT", suspended: "SUSP" };
const COLORS: Record<string, string> = {
  out: "bg-red-100 text-red-700",
  doubt: "bg-amber-100 text-amber-700",
  suspended: "bg-red-100 text-red-700",
};

export default function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`rounded-sm px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${COLORS[status] ?? "bg-neutral-100 text-neutral-600"}`}>
      {LABELS[status] ?? status}
    </span>
  );
}
