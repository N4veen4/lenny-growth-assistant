import { useState } from "react";
import { cn } from "@/lib/utils";

export function LogoMark({ className }: { className?: string }) {
  const [failed, setFailed] = useState(false);

  return (
    <span
      className={cn(
        "relative flex items-center justify-center overflow-hidden rounded-xl border border-primary/25 bg-gradient-to-br from-brand-subtle via-card to-background p-0.5 shadow-xs transition-all duration-300 hover:scale-105 hover:border-primary/50",
        className,
      )}
      aria-hidden
    >
      {!failed ? (
        <img
          src="/logo.png"
          alt="Lenny Logo"
          onError={() => setFailed(true)}
          className="size-full object-contain filter drop-shadow-xs select-none"
        />
      ) : (
        <svg
          viewBox="0 0 24 24"
          className="size-[65%] text-primary"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M4 18 L10 12 L14 15 L20 6" />
          <path d="M15 6 H20 V11" />
        </svg>
      )}
    </span>
  );
}
