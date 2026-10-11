import type { Conversation } from "@/types/assistant";

const DAY = 86_400_000;
const LABELS = ["Today", "Yesterday", "Previous 7 days", "Older"] as const;

export type GroupLabel = (typeof LABELS)[number];

export interface ConversationGroup {
  label: GroupLabel;
  items: Conversation[];
}

export function groupLabel(timestamp: number, currentNow: number = Date.now()): GroupLabel {
  const diff = currentNow - timestamp;
  if (diff < DAY) return "Today";
  if (diff < 2 * DAY) return "Yesterday";
  if (diff < 7 * DAY) return "Previous 7 days";
  return "Older";
}

export function groupConversations(
  items: Conversation[],
  currentNow: number = Date.now(),
): ConversationGroup[] {
  const sorted = [...items].sort((a, b) => b.updatedAt - a.updatedAt);
  const buckets: Record<GroupLabel, Conversation[]> = {
    Today: [],
    Yesterday: [],
    "Previous 7 days": [],
    Older: [],
  };

  for (const item of sorted) {
    const label = groupLabel(item.updatedAt, currentNow);
    buckets[label].push(item);
  }

  const result: ConversationGroup[] = [];
  for (const label of LABELS) {
    if (buckets[label].length > 0) {
      result.push({ label, items: buckets[label] });
    }
  }

  return result;
}

export function filterConversations(items: Conversation[], query: string): Conversation[] {
  const q = query.trim().toLowerCase();
  if (!q) return items;

  return items.filter((conv) => {
    if (conv.title.toLowerCase().includes(q)) return true;
    if (conv.messages?.some((m) => m.content.toLowerCase().includes(q))) return true;
    return false;
  });
}
