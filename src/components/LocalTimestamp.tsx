"use client";

import { useEffect, useState } from "react";
import { formatTimestamp } from "@/lib/format";

// Static export means this is rendered once at build time with no idea who's
// viewing it -- "the viewer's local time" can only be known in the browser.
// Render the UTC version first (matches what the server actually emitted, so
// hydration doesn't warn about a mismatch), then swap to the visitor's own
// timezone right after mount.
export default function LocalTimestamp({ iso }: { iso: string }) {
  const [text, setText] = useState(`${formatTimestamp(iso)} UTC`);

  useEffect(() => {
    // Intl rejects mixing dateStyle/timeStyle with explicit component options like
    // timeZoneName -- spell out the equivalent of "medium date + short time" by hand
    // so the zone abbreviation can be included.
    setText(
      new Date(iso).toLocaleString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
        timeZoneName: "short",
      }),
    );
  }, [iso]);

  return <>{text}</>;
}
