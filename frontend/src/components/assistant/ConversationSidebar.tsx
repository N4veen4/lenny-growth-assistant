import { Button } from "@/components/ui/button";
import {
  MessageSquarePlus,
  MessagesSquare,
  Search,
  SearchX,
  X,
  Sparkles,
  BookOpen,
  PenTool,
  TrendingUp,
  Database,
  Trash2,
} from "lucide-react";
import { useMemo, useState } from "react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { filterConversations, groupConversations } from "@/lib/conversations";
import { cn } from "@/lib/utils";
import { ConversationItem } from "./ConversationItem";
import { LogoMark } from "./Logo";
import { EmptyState } from "./States";
import { ThemeSegmentedControl, ThemeToggle } from "./ThemeToggle";
import { useAssistantStore } from "./store";

export function ConversationSidebar({
  collapsed,
  onNavigate,
}: {
  collapsed: boolean;
  onNavigate?: () => void;
}) {
  const { conversations, activeId, newChat, select, rename, remove, send, hydrated } =
    useAssistantStore();
  const [q, setQ] = useState("");
  const [pendingDelete, setPendingDelete] = useState<string | null>(null);
  const [pendingClearAll, setPendingClearAll] = useState(false);

  const groups = useMemo(
    () => groupConversations(filterConversations(conversations, q)),
    [conversations, q],
  );

  const handleQuickPrompt = (prompt: string) => {
    newChat();
    setTimeout(() => {
      send(prompt);
      onNavigate?.();
    }, 100);
  };

  const handleClearAll = async () => {
    for (const c of conversations) {
      await remove(c.id);
    }
    setPendingClearAll(false);
  };

  if (collapsed) {
    return (
      <aside className="flex h-full w-16 flex-col items-center justify-between border-r border-sidebar-border bg-sidebar py-5">
        <div className="flex flex-col items-center gap-4">
          <LogoMark className="size-9" />
          <Button
            variant="ghost"
            size="icon"
            onClick={newChat}
            title="New chat (Ctrl+K)"
            aria-label="New chat"
            className="rounded-xl p-2 text-sidebar-foreground hover:bg-sidebar-accent transition-all duration-200 hover:scale-105"
          >
            <MessageSquarePlus className="size-5 text-primary" />
          </Button>
        </div>
        <div className="flex flex-col items-center gap-2">
          <ThemeToggle />
        </div>
      </aside>
    );
  }

  const toDelete = conversations.find((c) => c.id === pendingDelete);

  return (
    <aside className="flex h-full w-[275px] max-w-full flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground transition-all duration-200">
      {/* 1. Header & Project Name with Brand Typography */}
      <div className="flex items-center gap-3 px-4 pt-5 pb-4">
        <LogoMark className="size-9 shrink-0 shadow-sm transition-transform duration-300 hover:scale-105" />
        <div className="min-w-0 leading-tight">
          <div className="flex items-center gap-1.5">
            <span className="font-brand text-[17px] font-black tracking-tight text-foreground bg-gradient-to-r from-foreground via-foreground to-primary/90 bg-clip-text">
              The Lenny
            </span>
            <span className="rounded-md bg-primary/15 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider text-primary border border-primary/20">
              AI
            </span>
          </div>
          <p className="font-sans text-[11px] font-medium text-muted-foreground tracking-tight">
            Growth & Product Assistant
          </p>
        </div>
      </div>

      {/* 2. ChatGPT-Style New Chat & Search */}
      <div className="space-y-2.5 px-3">
        <Button
          variant="outline"
          onClick={() => {
            newChat();
            onNavigate?.();
          }}
          className="group h-10 w-full justify-between rounded-xl border-border/80 bg-card/80 px-3 text-foreground shadow-xs transition-all duration-200 hover:border-primary/40 hover:bg-accent hover:shadow-sm"
        >
          <div className="flex items-center gap-2">
            <MessageSquarePlus className="size-4 text-primary transition-transform duration-200 group-hover:scale-110" />
            <span className="font-medium text-sm">New chat</span>
          </div>
          <span className="rounded border border-border/60 bg-muted/60 px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground">
            ⌘K
          </span>
        </Button>

        <div className="relative">
          <Search className="pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-muted-foreground" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search conversations..."
            aria-label="Search conversations"
            className="w-full rounded-xl border border-sidebar-border/80 bg-background/50 py-2 pr-7 pl-8 text-xs placeholder:text-muted-foreground/80 focus:border-primary/50 focus:bg-background focus:outline-none focus:ring-1 focus:ring-primary/40 transition-all duration-150"
          />
          {q && (
            <button
              onClick={() => setQ("")}
              className="absolute top-1/2 right-2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              title="Clear search"
            >
              <X className="size-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* 3. Quick Growth Assistant Templates (ChatGPT-style shortcuts) */}
      <div className="px-3 pt-3 pb-1">
        <div className="flex items-center gap-1.5 px-1 pb-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/80">
          <Sparkles className="size-3 text-primary" />
          <span>Quick Prompts</span>
        </div>
        <div className="grid grid-cols-2 gap-1.5">
          <button
            onClick={() =>
              handleQuickPrompt(
                "What did top product leaders say about achieving Product-Market Fit in Lenny's podcast?",
              )
            }
            className="flex items-center gap-1.5 rounded-lg border border-border/60 bg-card/40 px-2 py-1.5 text-left text-[11px] font-medium text-muted-foreground hover:border-primary/30 hover:bg-accent hover:text-foreground transition-colors"
          >
            <BookOpen className="size-3 text-amber-500 shrink-0" />
            <span className="truncate">PMF Secrets</span>
          </button>
          <button
            onClick={() =>
              handleQuickPrompt(
                "Write a Ship 30 for 30 essay on Product-Led Growth metrics with an artifact.",
              )
            }
            className="flex items-center gap-1.5 rounded-lg border border-border/60 bg-card/40 px-2 py-1.5 text-left text-[11px] font-medium text-muted-foreground hover:border-primary/30 hover:bg-accent hover:text-foreground transition-colors"
          >
            <PenTool className="size-3 text-primary shrink-0" />
            <span className="truncate">Ship 30 Essay</span>
          </button>
        </div>
      </div>

      {/* 4. Grouped Conversations List */}
      <nav
        className="mt-3 min-h-0 flex-1 overflow-y-auto overscroll-contain px-2.5 pb-2"
        aria-label="Conversations"
      >
        {hydrated && conversations.length === 0 && (
          <EmptyState icon={<MessagesSquare className="size-5" />} title="No chats yet">
            Ask your first growth question above.
          </EmptyState>
        )}
        {conversations.length > 0 && groups.length === 0 && (
          <EmptyState icon={<SearchX className="size-5" />} title="No matches found">
            Try a different search keyword.
          </EmptyState>
        )}
        {groups.map((g) => (
          <div key={g.label} className="mb-4">
            <p className="px-2.5 pb-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/70">
              {g.label}
            </p>
            <ul className={cn("space-y-0.5")}>
              {g.items.map((c) => (
                <li key={c.id}>
                  <ConversationItem
                    conv={c}
                    active={c.id === activeId}
                    onSelect={() => {
                      select(c.id);
                      onNavigate?.();
                    }}
                    onRename={(t) => rename(c.id, t)}
                    onDelete={() => setPendingDelete(c.id)}
                  />
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>

      {/* 5. ChatGPT-Style Bottom Options Panel */}
      <div className="border-t border-sidebar-border bg-card/20 px-3 py-3 space-y-2.5">
        {/* Theme Segmented Switcher */}
        <div>
          <p className="px-1 pb-1.5 text-[10px] font-medium text-muted-foreground/80">
            Appearance
          </p>
          <ThemeSegmentedControl />
        </div>

        {/* Knowledge Base Status Chip */}
        <div className="flex items-center justify-between rounded-lg border border-border/50 bg-background/40 px-2.5 py-1.5 text-[11px] text-muted-foreground">
          <div className="flex items-center gap-2">
            <span className="relative flex size-2">
              <span className="absolute inline-flex size-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex size-2 rounded-full bg-emerald-500" />
            </span>
            <span className="font-medium text-foreground/80">305 Episodes</span>
          </div>
          <span className="text-[10px] text-muted-foreground font-mono">609 Chunks</span>
        </div>

        {/* Workspace Account / Clear Chats Row */}
        <div className="flex items-center justify-between pt-0.5 text-[11px]">
          <div className="flex items-center gap-2 min-w-0">
            <div className="size-6 rounded-full bg-primary/20 text-primary font-bold flex items-center justify-center text-[10px] shrink-0 border border-primary/30">
              L
            </div>
            <span className="truncate font-medium text-foreground/90">Lenny Workspace</span>
          </div>

          {conversations.length > 0 && (
            <button
              onClick={() => setPendingClearAll(true)}
              className="text-[10px] text-muted-foreground hover:text-destructive transition-colors p-1 rounded hover:bg-destructive/10"
              title="Clear all conversations"
            >
              <Trash2 className="size-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Delete Single Chat Dialog */}
      <AlertDialog open={!!pendingDelete} onOpenChange={(o) => !o && setPendingDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete conversation?</AlertDialogTitle>
            <AlertDialogDescription>
              “{toDelete?.title}” will be removed from this workspace.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (pendingDelete) remove(pendingDelete);
                setPendingDelete(null);
              }}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Clear All Chats Dialog */}
      <AlertDialog open={pendingClearAll} onOpenChange={setPendingClearAll}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Clear all conversations?</AlertDialogTitle>
            <AlertDialogDescription>
              This will remove all {conversations.length} conversation sessions from your workspace. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleClearAll}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Clear All
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </aside>
  );
}
