import { getLastUpdated } from "@/lib/data";
import LocalTimestamp from "./LocalTimestamp";

export default function LastUpdatedBanner() {
  return (
    <div className="bg-neutral-50 px-4 py-1.5 text-center text-xs text-neutral-500 sm:px-8">
      Last updated: <LocalTimestamp iso={getLastUpdated()} />
    </div>
  );
}
