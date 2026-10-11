import { createFileRoute } from "@tanstack/react-router";
import { AppLayout } from "@/components/assistant/AppLayout";
import { AssistantProvider } from "@/components/assistant/store";
import { Toaster } from "@/components/ui/sonner";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "The Lenny Growth Assistant" },
      {
        name: "description",
        content:
          "A growth workspace prototype for product teams to explore retention, pricing and PLG with sample answers and artifacts.",
      },
      { property: "og:title", content: "The Lenny Growth Assistant" },
      {
        property: "og:description",
        content:
          "Explore growth questions with sample answers, clearly labeled mock sources, and document and page previews.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});

function Index() {
  return (
    <AssistantProvider>
      <AppLayout />
      <Toaster />
    </AssistantProvider>
  );
}
