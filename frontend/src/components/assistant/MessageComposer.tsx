import { Button } from "@/components/ui/button";
import { ArrowUp, Square } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useAssistantStore } from "./store";

export function MessageComposer() {
  const { send, phase, stop, activeId, model, error } = useAssistantStore();
  const [value, setValue] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);
  const busy = phase !== "idle";

  useEffect(() => {
    ref.current?.focus();
  }, [activeId, phase]);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  }, [value]);

  const submit = () => {
    if (!value.trim() || busy) return;
    send(value);
    setValue("");
  };

  return (
    <div className="mx-auto w-full max-w-3xl shrink-0 px-4 pt-3 pb-4 sm:px-8">
      <div className="rounded-2xl border border-border/80 bg-card/90 shadow-workspace transition-all duration-200 focus-within:border-primary/60 focus-within:ring-2 focus-within:ring-primary/20">
        <label htmlFor="composer" className="sr-only">
          Message
        </label>
        <textarea
          id="composer"
          ref={ref}
          rows={1}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
              e.preventDefault();
              submit();
            }
          }}
          placeholder="Ask about growth, retention, pricing…"
          className="block w-full resize-none bg-transparent px-4 pt-4 pb-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none"
        />
        <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-2 px-4 pb-3">
          <span className="min-w-0 text-[11px] text-muted-foreground">
            <kbd className="font-mono">Enter</kbd> to send ·{" "}
            <kbd className="font-mono">Shift+Enter</kbd> new line
          </span>
          {busy ? (
            <Button
              size="icon"
              onClick={stop}
              title="Stop generating"
              aria-label="Stop generating"
              className="flex size-8 items-center justify-center rounded-lg bg-foreground text-background transition-transform active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <Square className="size-3 fill-current" />
            </Button>
          ) : (
            <Button
              size="icon"
              onClick={submit}
              title="Send message"
              disabled={!value.trim()}
              aria-label="Send message"
              className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 active:scale-95 disabled:opacity-30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <ArrowUp className="size-4" />
            </Button>
          )}
        </div>
      </div>
      <p className="mt-3 text-center text-[10px] sm:text-[11px] text-muted-foreground">
        {error ? (
          <span className="text-destructive font-medium">{error}</span>
        ) : (
          <span className="inline-flex items-center gap-1.5">
            <span className="size-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span>
              Connected to{" "}
              {model.provider === "ollama"
                ? "Local (Ollama)"
                : `Cloud (${model.cloudProviderName})`}
            </span>
          </span>
        )}
      </p>
    </div>
  );
}
