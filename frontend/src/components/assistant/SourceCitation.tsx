import { ExternalLink, Headphones } from "lucide-react";
import type { Source } from "@/types/assistant";

export function SourceCitation({ sources }: { sources: Source[] }) {
  if (!sources || !sources.length) return null;
  return (
    <div className="mt-6 border-t border-border/60 pt-4 animate-in fade-in-50 duration-200">
      <div className="mb-3 flex items-center gap-2">
        <Headphones className="size-3.5 text-primary" />
        <span className="text-[11px] font-semibold tracking-wider text-muted-foreground uppercase">
          Sources ({sources.length})
        </span>
      </div>
      <ol className="grid gap-2.5">
        {sources.map((s, i) => {
          const displayTitle = s.title || s.episode_title || s.episode || "Lenny's Podcast";
          const speakerName = s.speaker || s.guest;

          return (
            <li
              key={s.id || `source-${i}`}
              className="group grid min-w-0 grid-cols-[auto_minmax(0,1fr)] items-start gap-3 rounded-xl border border-border/70 bg-card/50 p-3.5 text-xs transition-all duration-200 hover:border-primary/40 hover:bg-card/90 hover:shadow-xs"
            >
              <span className="flex size-6 shrink-0 items-center justify-center rounded-lg bg-brand-subtle font-mono text-[11px] font-medium text-primary">
                {i + 1}
              </span>
              <div className="min-w-0">
                <p className="break-words font-medium leading-relaxed text-foreground">
                  {s.url ? (
                    <a
                      href={s.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 font-medium text-foreground underline-offset-4 transition-colors hover:text-primary hover:underline"
                    >
                      <span>{displayTitle}</span>
                      <ExternalLink className="size-3 shrink-0 text-muted-foreground transition-colors group-hover:text-primary" />
                    </a>
                  ) : (
                    <span>{displayTitle}</span>
                  )}
                </p>
                <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                  {speakerName && (
                    <span className="inline-flex items-center rounded-md bg-muted/80 px-2 py-0.5 text-[10px] font-medium text-foreground/80">
                      {speakerName}
                    </span>
                  )}
                  {s.timestamp && (
                    <span className="inline-flex items-center rounded-md bg-muted/60 px-2 py-0.5 font-mono text-[10px] text-muted-foreground">
                      {s.timestamp}
                    </span>
                  )}
                </div>
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
