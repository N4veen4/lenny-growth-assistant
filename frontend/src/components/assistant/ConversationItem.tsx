import { Button } from "@/components/ui/button";
import { MoreHorizontal, Pencil, Trash2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import type { Conversation } from "@/types/assistant";

export function ConversationItem({
  conv,
  active,
  onSelect,
  onRename,
  onDelete,
}: {
  conv: Conversation;
  active: boolean;
  onSelect: () => void;
  onRename: (t: string) => void;
  onDelete: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(conv.title);
  const input = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (editing) input.current?.select();
  }, [editing]);

  if (editing) {
    return (
      <input
        ref={input}
        aria-label="Rename conversation"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        onBlur={() => {
          onRename(title);
          setEditing(false);
        }}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            onRename(title);
            setEditing(false);
          }
          if (e.key === "Escape") {
            setTitle(conv.title);
            setEditing(false);
          }
        }}
        className="w-full rounded-md border border-primary/50 bg-card px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
      />
    );
  }

  return (
    <div
      className={cn(
        "group grid grid-cols-[minmax(0,1fr)_auto] items-center rounded-lg transition-colors px-1",
        active
          ? "bg-sidebar-accent text-white font-medium shadow-xs"
          : "text-sidebar-foreground hover:bg-sidebar-accent/60 hover:text-foreground",
      )}
    >
      <Button
        variant="ghost"
        onClick={onSelect}
        aria-current={active ? "page" : undefined}
        className="block h-9 min-w-0 flex-1 truncate rounded-lg px-2 text-left text-[13.5px] font-normal hover:bg-transparent focus-visible:outline-none"
      >
        {active && (
          <span className="mr-2 inline-block size-1.5 rounded-full bg-primary align-middle" />
        )}
        {conv.title}
      </Button>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            aria-label={`Actions for ${conv.title}`}
            className="mr-1 size-7 shrink-0 rounded p-1 text-muted-foreground opacity-100 sm:opacity-0 transition-opacity hover:text-foreground focus-visible:opacity-100 group-hover:opacity-100 data-[state=open]:opacity-100"
          >
            <MoreHorizontal className="size-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem
            onSelect={() => {
              setTitle(conv.title);
              setTimeout(() => setEditing(true), 0);
            }}
          >
            <Pencil className="size-3.5" /> Rename
          </DropdownMenuItem>
          <DropdownMenuItem onSelect={onDelete} className="text-destructive focus:text-destructive">
            <Trash2 className="size-3.5" /> Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
