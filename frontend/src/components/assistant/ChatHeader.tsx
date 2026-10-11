import { Menu, PanelLeft, PanelRightOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ModelSelector } from "./ModelSelector";
import { useAssistantStore } from "./store";

export function ChatHeader({
  onToggleSidebar,
  onOpenMobileSidebar,
}: {
  onToggleSidebar: () => void;
  onOpenMobileSidebar: () => void;
}) {
  const { active, artifact, artifactOpen, setArtifactOpen } = useAssistantStore();
  return (
    <header className="grid h-[72px] shrink-0 grid-cols-[minmax(0,1fr)_auto] items-center gap-2 border-b border-border/60 px-3 sm:px-5">
      <div className="flex min-w-0 items-center gap-2 sm:gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={onOpenMobileSidebar}
          aria-label="Open conversations"
          title="Open conversations"
          className="shrink-0 text-muted-foreground md:hidden"
        >
          <Menu />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleSidebar}
          aria-label="Toggle sidebar"
          title="Toggle sidebar"
          className="hidden shrink-0 text-muted-foreground md:inline-flex"
        >
          <PanelLeft />
        </Button>
        <div className="min-w-0">
          <h1 className="truncate text-sm font-medium">{active?.title ?? "New chat"}</h1>
          <p className="mt-1 truncate text-[11px] text-muted-foreground">
            The Lenny · Growth Assistant
          </p>
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {artifact && !artifactOpen && (
          <Button
            variant="outline"
            size="icon"
            onClick={() => setArtifactOpen(true)}
            aria-label="Open artifact viewer"
            title="Open artifact viewer"
            className="size-8 text-muted-foreground"
          >
            <PanelRightOpen />
          </Button>
        )}
        <ModelSelector />
      </div>
    </header>
  );
}
