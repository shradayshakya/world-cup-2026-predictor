export function formatPercent(value: number | undefined, digits: number = 1): string {
  if (value === undefined) return "—";
  return `${(value * 100).toFixed(digits)}%`;
}

export function formatDate(date: string | null): string {
  if (!date) return "Date TBD";
  return new Date(`${date}T00:00:00Z`).toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  });
}

export function formatTimestamp(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  });
}
