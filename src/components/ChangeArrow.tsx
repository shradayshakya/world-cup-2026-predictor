// PRD §5.1a: green up / red down, no arrow below the noise threshold (already
// filtered server-side when probability_changes.json is generated, but this stays
// defensive in case it's ever called with raw, unfiltered data).
//
// The delta is "since the last match result," not "since yesterday" -- update.py's
// change_baseline.json only advances when a real match resolves, so it correctly
// survives multiple no-op pipeline runs between results without resetting to zero.
const NOISE_THRESHOLD_PP = 0.1;

export default function ChangeArrow({ deltaPp }: { deltaPp: number | undefined }) {
  if (deltaPp === undefined || Math.abs(deltaPp) < NOISE_THRESHOLD_PP) return null;
  const isGain = deltaPp > 0;
  return (
    <span
      title={`${isGain ? "+" : ""}${deltaPp.toFixed(1)}pp since the last match result`}
      className={`ml-1 text-xs ${isGain ? "text-emerald-600" : "text-red-600"}`}
    >
      {isGain ? "▲" : "▼"}
    </span>
  );
}
