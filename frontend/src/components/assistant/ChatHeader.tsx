import { Menu, PanelLeft, PanelRightOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ModelSelector } from "./ModelSelector";
import { ThemeToggle } from "./ThemeToggle";
import { useAssistantStore } from "./store";

export function ChatHeader({
  onToggleSidebar,
  onOpenMobileSidebar,
}: {
  onToggleSidebar: () => void;
  onOpenMobileSidebar: () => void;
}) {
  const { artifact, artifactOpen, setArtifactOpen } = useAssistantStore();
  return (
    <header className="flex h-[64px] shrink-0 items-center justify-between border-b border-border/60 bg-background px-3 sm:px-5">
      <div className="flex items-center gap-2 sm:gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={onOpenMobileSidebar}
          aria-label="Open conversations"
          title="Open conversations"
          className="shrink-0 text-muted-foreground md:hidden hover:text-foreground"
        >
          <Menu />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleSidebar}
          aria-label="Toggle sidebar"
          title="Toggle sidebar"
          className="hidden shrink-0 text-muted-foreground md:inline-flex hover:text-foreground hover:bg-accent/70"
        >
          <PanelLeft />
        </Button>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <ThemeToggle />
        {artifact && !artifactOpen && (
          <Button
            variant="outline"
            size="icon"
            onClick={() => setArtifactOpen(true)}
            aria-label="Open artifact viewer"
            title="Open artifact viewer"
            className="size-8 text-muted-foreground hover:text-primary hover:border-primary/40 transition-colors"
          >
            <PanelRightOpen />
          </Button>
        )}
        <ModelSelector />
      </div>
    </header>
  );
}
