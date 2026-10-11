import { Button } from "@/components/ui/button";
import { MessageSquarePlus, MessagesSquare, Search, SearchX } from "lucide-react";
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
import { useAssistantStore } from "./store";

export function ConversationSidebar({
  collapsed,
  onNavigate,
}: {
  collapsed: boolean;
  onNavigate?: () => void;
}) {
  const { conversations, activeId, newChat, select, rename, remove, hydrated } =
    useAssistantStore();
  const [q, setQ] = useState("");
  const [pendingDelete, setPendingDelete] = useState<string | null>(null);
  const groups = useMemo(
    () => groupConversations(filterConversations(conversations, q)),
    [conversations, q],
  );

  if (collapsed) {
    return (
      <aside className="flex h-full w-16 flex-col items-center gap-5 border-r border-sidebar-border bg-sidebar py-5">
        <LogoMark className="size-8" />
        <Button
          variant="ghost"
          size="icon"
          onClick={newChat}
          title="New chat"
          aria-label="New chat"
          className="rounded-md p-2 text-sidebar-foreground hover:bg-sidebar-accent"
        >
          <MessageSquarePlus className="size-4" />
        </Button>
      </aside>
    );
  }

  const toDelete = conversations.find((c) => c.id === pendingDelete);

  return (
    <aside className="flex h-full w-[264px] max-w-full flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground">
      <div className="flex items-center gap-3 px-5 pt-6 pb-7">
        <LogoMark className="size-8" />
        <div className="min-w-0 leading-tight">
          <p className="font-display text-lg font-semibold">The Lenny</p>
          <p className="text-[11px] text-muted-foreground">Growth Assistant</p>
        </div>
      </div>
      <div className="space-y-3 px-4">
        <Button
          variant="outline"
          onClick={() => {
            newChat();
            onNavigate?.();
          }}
          className="h-10 w-full justify-start border-border bg-card text-foreground shadow-none hover:border-primary/35 hover:bg-accent"
        >
          <MessageSquarePlus className="size-4 text-primary" /> New chat
        </Button>
        <div className="relative">
          <Search className="pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-muted-foreground" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search conversations"
            aria-label="Search conversations"
            className="w-full rounded-lg border border-sidebar-border/70 bg-background/40 py-2 pr-2 pl-8 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
      </div>
      <nav
        className="mt-7 min-h-0 flex-1 overflow-y-auto overscroll-contain px-3 pb-4"
        aria-label="Conversations"
      >
        {hydrated && conversations.length === 0 && (
          <EmptyState icon={<MessagesSquare className="size-6" />} title="No conversations yet">
            Start a new chat to ask your first growth question.
          </EmptyState>
        )}
        {conversations.length > 0 && groups.length === 0 && (
          <EmptyState icon={<SearchX className="size-6" />} title="No matches">
            Try a different search term.
          </EmptyState>
        )}
        {groups.map((g) => (
          <div key={g.label} className="mb-6">
            <p className="px-2.5 pb-2 text-[10px] font-medium text-muted-foreground">{g.label}</p>
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
      <div className="mx-4 mb-4 flex items-center gap-2 border-t border-sidebar-border pt-4 text-[11px] text-muted-foreground">
        <span className="size-1.5 rounded-full bg-primary/70" />
        Sample workspace
        <span className="ml-auto rounded border border-border px-1.5 py-0.5 text-[9px]">
          PROTOTYPE
        </span>
      </div>
      <AlertDialog open={!!pendingDelete} onOpenChange={(o) => !o && setPendingDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete conversation?</AlertDialogTitle>
            <AlertDialogDescription>
              “{toDelete?.title}” will be removed from this browser.
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
    </aside>
  );
}
