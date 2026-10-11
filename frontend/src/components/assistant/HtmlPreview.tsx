import { useEffect, useState } from "react";
import { ErrorState, LoadingState } from "./States";

/**
 * Untrusted HTML is rendered only inside a fully sandboxed iframe:
 * sandbox="" disables scripts, forms, popups and same-origin access.
 */
export function HtmlPreview({ html, title }: { html: string; title: string }) {
  const [loaded, setLoaded] = useState(false);
  useEffect(() => setLoaded(false), [html]);
  if (!html.trim()) return <ErrorState message="This artifact has no HTML to render." />;
  return (
    <div className="relative h-full min-h-[320px] overflow-hidden rounded-lg border border-border bg-card">
      {!loaded && (
        <div className="absolute inset-0 flex items-center justify-center">
          <LoadingState label="Rendering preview…" />
        </div>
      )}
      <iframe
        title={`Preview: ${title}`}
        sandbox=""
        referrerPolicy="no-referrer"
        srcDoc={html}
        onLoad={() => setLoaded(true)}
        className="h-full w-full"
      />
    </div>
  );
}
