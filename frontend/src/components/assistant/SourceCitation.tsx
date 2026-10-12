import { ExternalLink, Headphones } from "lucide-react";
import type { Source } from "@/types/assistant";

export function SourceCitation({ sources }: { sources: Source[] }) {
  if (!sources || !sources.length) return null;
  return (
    <div className="mt-6 border-t border-border/60 pt-4 animate-in fade-in-50 duration-200">
      <div className="mb-3 flex items-center gap-2">
        <Headphones className="size-3.5 text-primary" />
        <span className="text-[11px] font-semibold tracking-wider text-muted-foreground uppercase">
          Sources
        </span>
      </div>
      <ol className="grid gap-2.5">
        {sources.map((s, i) => {
          const displayTitle = s.title || s.episode_title || s.episode || "Lenny's Podcast";
          const speakerName = s.speaker || s.guest;

          return (
            <li
              key={s.id || `source-${i}`}
              className="group relative isolate overflow-hidden grid min-w-0 grid-cols-[auto_minmax(0,1fr)] items-start gap-3 rounded-xl border border-white/15 p-3.5 text-xs transition-all duration-200 hover:border-white/30 hover:shadow-md"
            >
              {/* Clear background image without blur */}
              <div
                className="pointer-events-none absolute inset-0 -z-10 bg-cover bg-center transition-transform duration-300 group-hover:scale-105"
                style={{ backgroundImage: `url('/lennys-podcast-bg.png')` }}
              />
              {/* Dark tint overlay so text and names are clearly visible */}
              <div className="pointer-events-none absolute inset-0 -z-10 bg-black/60 group-hover:bg-black/50 transition-colors" />

              <span className="relative z-10 font-mono text-[12px] font-bold text-white/90 drop-shadow-xs pt-0.5">
                {i + 1}.
              </span>
              <div className="relative z-10 min-w-0">
                <p className="break-words font-semibold text-[13px] leading-relaxed text-white drop-shadow-sm">
                  {s.url ? (
                    <a
                      href={s.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 font-semibold text-white underline-offset-4 transition-colors hover:text-amber-200 hover:underline"
                    >
                      <span>{displayTitle}</span>
                      <ExternalLink className="size-3.5 shrink-0 text-white/70 transition-colors group-hover:text-amber-200" />
                    </a>
                  ) : (
                    <span>{displayTitle}</span>
                  )}
                </p>
                <div className="mt-1 flex flex-wrap items-center gap-2 text-[11px] text-white/80 drop-shadow-xs">
                  {speakerName && (
                    <span className="font-medium text-white/90">
                      {speakerName}
                    </span>
                  )}
                  {s.timestamp && (
                    <span className="font-mono text-white/75">
                      {speakerName ? `• ${s.timestamp}` : s.timestamp}
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
