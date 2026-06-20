"use client";

import { useEffect, useState } from "react";
import MatchCard from "./MatchCard";
import type { PredictedMatch, ResultMatch } from "@/lib/types";

interface Entry {
  match: ResultMatch;
  index: number;
  prediction: PredictedMatch | null;
}

// "Today" is only knowable in the viewer's own browser at view time -- this site is a
// static export with no per-visitor server render, and the pipeline's own "today" is
// whatever UTC date it happened to run at, which can already disagree with a visitor's
// local calendar date. The page passes in everything within +/-1 day of the server's
// "today" (matches have no time-of-day in the source data, so a 1-day window covers any
// realistic timezone offset); this component picks out whichever of those is *actually*
// "today" for the person looking at the screen.
function localToday(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export default function TodaysMatches({ serverToday, windowed }: { serverToday: string; windowed: Entry[] }) {
  // Before mount, render the server's best guess (matches the static HTML exactly, so
  // hydration doesn't warn about a mismatch); swap to the visitor's real local date
  // immediately after.
  const [today, setToday] = useState(serverToday);

  useEffect(() => {
    setToday(localToday());
  }, []);

  const todaysMatches = windowed.filter((e) => e.match.date === today);

  if (todaysMatches.length === 0) {
    return <p className="mt-2 text-sm text-neutral-500">No matches scheduled today.</p>;
  }

  return (
    <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
      {todaysMatches.map(({ match, index, prediction }) => (
        <MatchCard key={index} match={match} index={index} prediction={prediction} />
      ))}
    </div>
  );
}
