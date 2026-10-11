import { Button } from "@/components/ui/button";
import { Check, ChevronDown, Cloud, Cpu } from "lucide-react";
import { useState } from "react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import { useAssistantStore } from "./store";

export function ModelSelector() {
  const { model, setModel } = useAssistantStore();
  const [open, setOpen] = useState(false);

  const label = model.provider === "ollama" ? `Local (Ollama)` : `Cloud (OpenRouter)`;

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className="flex h-8 items-center gap-2 rounded-md border border-border/70 bg-card/60 px-2 sm:px-3 text-xs font-medium text-foreground transition-colors hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          aria-label={`Selected provider: ${label}`}
        >
          {model.provider === "ollama" ? (
            <Cpu className="size-3.5" />
          ) : (
            <Cloud className="size-3.5" />
          )}
          <span className="max-w-[100px] truncate sm:max-w-[180px]">{label}</span>
          <ChevronDown className="size-3.5 text-muted-foreground" />
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-64 p-0">
        <div className="border-b border-border p-3">
          <p className="text-sm font-medium">Provider Selection</p>
          <p className="text-xs text-muted-foreground">Select the backend AI provider.</p>
        </div>
        <div className="p-2 space-y-1">
          <Button
            variant="ghost"
            onClick={() => {
              setModel({ provider: "ollama", model: "qwen3:4b", cloudProviderName: "" });
              setOpen(false);
            }}
            className={cn(
              "flex w-full items-center justify-between h-9 rounded-md px-2 py-1.5 text-xs hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              model.provider === "ollama" && model.model === "qwen3:4b" && "bg-accent",
            )}
          >
            <span className="flex items-center gap-2">
              <Cpu className="size-3.5" /> Local (Qwen3)
            </span>
            {model.provider === "ollama" && model.model === "qwen3:4b" && (
              <Check className="size-3.5 text-primary" />
            )}
          </Button>
          <Button
            variant="ghost"
            onClick={() => {
              setModel({ provider: "ollama", model: "llama3:latest", cloudProviderName: "" });
              setOpen(false);
            }}
            className={cn(
              "flex w-full items-center justify-between h-9 rounded-md px-2 py-1.5 text-xs hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              model.provider === "ollama" && model.model === "llama3:latest" && "bg-accent",
            )}
          >
            <span className="flex items-center gap-2">
              <Cpu className="size-3.5" /> Local (Llama 3)
            </span>
            {model.provider === "ollama" && model.model === "llama3:latest" && (
              <Check className="size-3.5 text-primary" />
            )}
          </Button>
          <Button
            variant="ghost"
            onClick={() => {
              setModel({
                provider: "cloud",
                model: "openai/gpt-4o-mini",
                cloudProviderName: "OpenRouter",
              });
              setOpen(false);
            }}
            className={cn(
              "flex w-full items-center justify-between h-9 rounded-md px-2 py-1.5 text-xs hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              model.provider === "cloud" && "bg-accent",
            )}
          >
            <span className="flex items-center gap-2">
              <Cloud className="size-3.5" /> Cloud (OpenRouter)
            </span>
            {model.provider === "cloud" && <Check className="size-3.5 text-primary" />}
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  );
}
