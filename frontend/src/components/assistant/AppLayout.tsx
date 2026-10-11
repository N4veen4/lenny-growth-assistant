import { ArrowUpRight, ChartNoAxesCombined, Layers3, Sprout, Target } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useEffect, useRef, useState } from "react";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
import { STARTER_QUESTIONS } from "@/mocks/data";
import { ArtifactViewer } from "./ArtifactViewer";
import { ChatHeader } from "./ChatHeader";
import { ChatMessage } from "./ChatMessage";
import { ConversationSidebar } from "./ConversationSidebar";
import { LogoMark } from "./Logo";
import { MessageComposer } from "./MessageComposer";
import { ErrorState, LoadingState } from "./States";
import { useAssistantStore } from "./store";

function Welcome() {
  const { send } = useAssistantStore();
  const [greeting, setGreeting] = useState("Welcome back");
  useEffect(() => {
    const hour = new Date().getHours();
    setGreeting(hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening");
  }, []);
  const icons = [Target, ChartNoAxesCombined, Sprout, Layers3];
  const topics = ["Product-market fit", "Retention", "Onboarding", "Pricing"];
  return (
    <div className="mx-auto flex w-full max-w-[680px] flex-col px-5 pt-12 pb-8 sm:px-8 sm:pt-20">
      <LogoMark className="size-12" />
      <p className="mt-7 text-sm text-muted-foreground">{greeting}</p>
      <h2 className="mt-2 max-w-lg font-display text-[30px] leading-tight font-medium sm:text-4xl">
        What growth challenge are we working on?
      </h2>
      <p className="mt-4 max-w-md text-sm leading-relaxed text-muted-foreground">
        A little clarity for your next big decision.
      </p>
      <div className="mt-8 grid w-full gap-3 sm:grid-cols-2">
        {STARTER_QUESTIONS.slice(0, 4).map((q, i) => {
          const Icon = icons[i] ?? Target;
          return (
            <Button
              key={q}
              variant="outline"
              onClick={() => send(q)}
              className="group h-auto min-h-28 flex-col items-start gap-3 whitespace-normal rounded-xl border-border/70 bg-card/60 p-4 text-left shadow-xs transition-all duration-200 hover:border-primary/45 hover:bg-card hover:shadow-sm"
            >
              <span className="flex w-full items-center gap-2 text-xs text-muted-foreground">
                <Icon className="size-4 text-primary/80 transition-colors group-hover:text-primary" />
                {topics[i]}
                <ArrowUpRight className="ml-auto size-3.5 opacity-0 transition-opacity group-hover:opacity-100" />
              </span>
              <span className="text-sm font-normal leading-relaxed">{q}</span>
            </Button>
          );
        })}
      </div>
    </div>
  );
}

function ChatWorkspace() {
  const { active, phase, error, retry, hydrated } = useAssistantStore();
  const end = useRef<HTMLDivElement>(null);
  const msgs = active?.messages ?? [];
  useEffect(() => {
    end.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [msgs.length, msgs[msgs.length - 1]?.content, phase, error]);

  if (!hydrated)
    return (
      <div className="flex flex-1 items-center justify-center">
        <LoadingState label="Loading workspace…" />
      </div>
    );

  return (
    <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain scroll-smooth">
      {msgs.length === 0 ? (
        <Welcome />
      ) : (
        <div className="mx-auto max-w-3xl space-y-8 px-5 py-8 sm:px-8">
          {msgs.map((m) => (
            <ChatMessage key={m.id} message={m} />
          ))}
          {phase === "loading" && (
            <div className="pl-10">
              <LoadingState />
            </div>
          )}
          {error && <ErrorState message={error} onRetry={retry} />}
          <div ref={end} />
        </div>
      )}
    </div>
  );
}

export function AppLayout() {
  const { artifactOpen, setArtifactOpen, newChat } = useAssistantStore();
  const [narrow, setNarrow] = useState(false);
  useEffect(() => {
    const media = window.matchMedia("(max-width: 1099px)");
    const update = () => setNarrow(media.matches);
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        newChat();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [newChat]);

  return (
    <div className="flex h-dvh w-full overflow-hidden bg-background">
      <div className="hidden md:block">
        <ConversationSidebar collapsed={collapsed} />
      </div>
      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetContent side="left" className="w-72 p-0 [&>button]:hidden">
          <SheetTitle className="sr-only">Conversations</SheetTitle>
          <ConversationSidebar collapsed={false} onNavigate={() => setMobileOpen(false)} />
        </SheetContent>
      </Sheet>
      <main className="flex min-w-0 flex-1 flex-col">
        <ChatHeader
          onToggleSidebar={() => setCollapsed((c) => !c)}
          onOpenMobileSidebar={() => setMobileOpen(true)}
        />
        <ChatWorkspace />
        <MessageComposer />
      </main>
      {artifactOpen && !narrow && (
        <ArtifactViewer className="w-[43%] min-w-[380px] max-w-[720px] shrink-0 border-l border-border" />
      )}
      {narrow && (
        <Sheet open={artifactOpen} onOpenChange={setArtifactOpen}>
          <SheetContent side="bottom" className="h-[94dvh] p-0 [&>button]:hidden">
            <SheetTitle className="sr-only">Artifact</SheetTitle>
            <ArtifactViewer className="h-full" />
          </SheetContent>
        </Sheet>
      )}
    </div>
  );
}
