import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { api } from "@/services/api";
import type { Artifact, Conversation, Message, ModelSelection, Source } from "@/types/assistant";
import { toast } from "sonner";

interface RawCitation {
  episode_title?: string;
  title?: string;
  speaker?: string;
  guest?: string;
  episode?: string;
  timestamp?: string;
  url?: string;
  content?: string;
}

function mapRawCitations(rawList?: RawCitation[]): Source[] {
  if (!rawList) return [];
  return rawList.map((c, i) => ({
    id: `citation-${i}-${c.timestamp || ""}`,
    title: c.episode_title || c.title || "Lenny's Podcast",
    guest: c.speaker || c.guest || "Lenny Rachitsky",
    speaker: c.speaker,
    episode: c.episode_title || c.episode || "Lenny's Podcast",
    episode_title: c.episode_title,
    timestamp: c.timestamp,
    url: c.url,
    content: c.content,
  }));
}

type Phase = "idle" | "loading" | "generating";

interface Store {
  hydrated: boolean;
  conversations: Conversation[];
  activeId: string | null;
  active: Conversation | null;
  model: ModelSelection;
  phase: Phase;
  error: string | null;
  artifact: Artifact | null;
  artifacts: Artifact[];
  artifactOpen: boolean;
  newChat(): void;
  select(id: string): void;
  rename(id: string, title: string): void;
  remove(id: string): void;
  send(text: string): void;
  retry(): void;
  stop(): void;
  setModel(m: ModelSelection): void;
  openArtifact(a: Artifact): void;
  setArtifactOpen(v: boolean): void;
}

const Ctx = createContext<Store | null>(null);

export function AssistantProvider({ children }: { children: ReactNode }) {
  const [hydrated, setHydrated] = useState(false);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [model, setModelState] = useState<ModelSelection>({
    provider: "ollama",
    model: "llama3:latest",
    cloudProviderName: "OpenRouter",
  });
  const [phase, setPhase] = useState<Phase>("idle");
  const [error, setError] = useState<string | null>(null);
  const [artifact, setArtifact] = useState<Artifact | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [artifactOpen, setArtifactOpen] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const lastPrompt = useRef<string>("");

  useEffect(() => {
    let mounted = true;
    const init = async () => {
      try {
        const list = await api.listConversations();
        if (mounted) {
          setConversations(list);
          // When opening the web page newly, open directly on a clean new chat page:
          setActiveId(null);
          setArtifact(null);
          setArtifacts([]);
          setArtifactOpen(false);
        }
      } catch (err) {
        if (mounted) {
          toast.error("Failed to connect to backend.");
        }
      } finally {
        if (mounted) setHydrated(true);
      }
    };
    init();
    return () => {
      mounted = false;
    };
  }, []);

  // Fetch messages and artifacts whenever activeId changes
  useEffect(() => {
    if (!activeId) {
      setArtifact(null);
      setArtifacts([]);
      return;
    }

    let mounted = true;

    // Fetch conversation artifacts
    api
      .getArtifacts(activeId)
      .then((arts) => {
        if (mounted) {
          setArtifacts(arts);
          if (arts.length > 0) {
            // Keep the newest artifact ready
            setArtifact(arts[0]);
          } else {
            setArtifact(null);
          }
        }
      })
      .catch(() => {
        // Safe fallback if conversation has no artifacts or error
        if (mounted) {
          setArtifacts([]);
        }
      });

    // Fetch messages if not yet loaded
    const activeConv = conversations.find((c) => c.id === activeId);
    if (activeConv && activeConv.messages.length === 0) {
      api
        .getMessages(activeId)
        .then((msgs) => {
          if (mounted) {
            setConversations((list) =>
              list.map((c) => (c.id === activeId ? { ...c, messages: msgs } : c)),
            );
            // If messages have artifacts, ensure store has the latest
            const msgWithArt = msgs
              .slice()
              .reverse()
              .find((m) => m.artifact);
            if (msgWithArt?.artifact) {
              setArtifact((current) => current || msgWithArt.artifact!);
            }
          }
        })
        .catch(() => {
          if (mounted) toast.error("Failed to load messages.");
        });
    }

    return () => {
      mounted = false;
    };
  }, [activeId, conversations]);

  const active = conversations.find((c) => c.id === activeId) ?? null;

  const patch = useCallback((id: string, fn: (c: Conversation) => Conversation) => {
    setConversations((list) => list.map((c) => (c.id === id ? fn(c) : c)));
  }, []);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setPhase("idle");
  }, []);

  const run = useCallback(
    async (convId: string | null, text: string, history: Message[]) => {
      setError(null);
      setPhase("loading");
      const ctrl = new AbortController();
      abortRef.current = ctrl;

      // optimistic user msg
      const userMsgId = Math.random().toString();
      const optimisticMsg: Message = {
        id: userMsgId,
        role: "user",
        content: text,
        createdAt: Date.now(),
      };

      let currentConvId = convId;

      if (currentConvId && conversations.some((c) => c.id === currentConvId)) {
        patch(currentConvId, (c) => ({
          ...c,
          messages: [...c.messages, optimisticMsg],
        }));
      } else {
        // Create an optimistic local conversation if none exists
        const tempId = `conv-${Date.now()}`;
        currentConvId = tempId;
        const newConv: Conversation = {
          id: tempId,
          title: text.slice(0, 30),
          updatedAt: Date.now(),
          messages: [optimisticMsg],
        };
        setConversations((l) => [newConv, ...l]);
        setActiveId(tempId);
      }

      try {
        const res = await api.sendMessage({
          sessionId: currentConvId,
          content: text,
          history,
          model,
          signal: ctrl.signal,
        });

        // If backend returned a new conversationId, sync it
        const finalConvId = res.conversationId || currentConvId;
        if (finalConvId !== currentConvId) {
          setConversations((l) =>
            l.map((c) => (c.id === currentConvId ? { ...c, id: finalConvId } : c)),
          );
          setActiveId(finalConvId);
          currentConvId = finalConvId;
        }

        setPhase("generating");

        const msgId = res.id || Math.random().toString();
        patch(currentConvId, (c) => ({
          ...c,
          messages: [
            ...c.messages,
            {
              id: msgId,
              role: "assistant",
              content: "",
              statusMsg: "Preparing your question...",
              createdAt: Date.now(),
              sources: res.sources,
              artifact: res.artifact,
            },
          ],
        }));

        for await (const chunk of res.stream) {
          if (typeof chunk === "string") {
            // Fallback for non-streaming strings
            patch(currentConvId, (c) => ({
              ...c,
              updatedAt: Date.now(),
              messages: c.messages.map((m) =>
                m.id === msgId ? { ...m, content: m.content + chunk } : m,
              ),
            }));
          } else if (chunk.type === "init") {
            const mappedSources = mapRawCitations(chunk.citations);
            patch(currentConvId, (c) => ({
              ...c,
              id: chunk.conversationId || c.id,
              messages: c.messages.map((m) =>
                m.id === msgId ? { ...m, sources: mappedSources } : m,
              ),
            }));
            if (chunk.conversationId && chunk.conversationId !== currentConvId) {
              setConversations((l) =>
                l.map((conv) =>
                  conv.id === currentConvId ? { ...conv, id: chunk.conversationId } : conv,
                ),
              );
              setActiveId(chunk.conversationId);
              currentConvId = chunk.conversationId;
            }
          } else if (chunk.type === "status") {
            patch(currentConvId, (c) => ({
              ...c,
              messages: c.messages.map((m) =>
                m.id === msgId ? { ...m, statusMsg: chunk.message } : m,
              ),
            }));
          } else if (chunk.type === "text_delta") {
            patch(currentConvId, (c) => ({
              ...c,
              updatedAt: Date.now(),
              messages: c.messages.map((m) =>
                m.id === msgId ? { ...m, content: m.content + chunk.text } : m,
              ),
            }));
          } else if (chunk.type === "done") {
            const mappedSources = mapRawCitations(chunk.data.citations);
            const rawArt = chunk.data.artifacts?.[0];
            const art: Artifact | undefined = rawArt
              ? {
                  id: rawArt.id,
                  title: rawArt.title,
                  type: rawArt.type || rawArt.artifact_type || "markdown",
                  content: rawArt.content,
                }
              : undefined;

            patch(currentConvId, (c) => ({
              ...c,
              messages: c.messages.map((m) =>
                m.id === msgId
                  ? {
                      ...m,
                      id: chunk.data.id || msgId,
                      content: chunk.data.content || m.content,
                      statusMsg: undefined,
                      status: "done",
                      artifact: art,
                      sources: mappedSources.length > 0 ? mappedSources : m.sources,
                    }
                  : m,
              ),
            }));
            if (art) {
              setArtifact(art);
              setArtifacts((prev) => [art, ...prev.filter((a) => a.id !== art.id)]);
              setArtifactOpen(true);
            }
          }
        }

        // Final fallback done marking
        patch(currentConvId, (c) => ({
          ...c,
          messages: c.messages.map((m) =>
            m.id === msgId ? { ...m, status: "done", statusMsg: undefined } : m,
          ),
        }));

        // The artifact is now updated through the "done" event in the stream
      } catch (e) {
        if ((e as Error).name !== "AbortError") {
          setError((e as Error).message || "Something went wrong.");
          toast.error((e as Error).message || "Something went wrong.");
        }
      } finally {
        setPhase("idle");
        abortRef.current = null;
      }
    },
    [conversations, model, patch],
  );

  const newChat = useCallback(() => {
    stop();
    setActiveId(null);
    setError(null);
    setArtifact(null);
    setArtifacts([]);
    setArtifactOpen(false);
  }, [stop]);

  const send = useCallback(
    (raw: string) => {
      const text = raw.trim();
      if (!text || phase !== "idle") return;
      lastPrompt.current = text;
      const id = activeId;
      let history: Message[] = [];

      if (id) {
        const cur = conversations.find((c) => c.id === id);
        history = cur?.messages ?? [];
      }
      void run(id, text, history);
    },
    [activeId, conversations, phase, run],
  );

  const retry = useCallback(() => {
    if (activeId && lastPrompt.current)
      void run(activeId, lastPrompt.current, active?.messages ?? []);
  }, [active, activeId, run]);

  const value = useMemo<Store>(
    () => ({
      hydrated,
      conversations,
      activeId,
      active,
      model,
      phase,
      error,
      artifact,
      artifacts,
      artifactOpen,
      newChat,
      select: (id) => {
        stop();
        setActiveId(id);
        setError(null);
        setArtifact(null);
        setArtifacts([]);
        setArtifactOpen(false);
      },
      rename: (id, title) => {
        // The backend does not currently support rename, just stub it with error message.
        toast.error("Rename not supported by backend yet.");
      },
      remove: async (id) => {
        try {
          await api.deleteConversation(id);
          setConversations((list) => {
            const currentIndex = list.findIndex((c) => c.id === id);
            const nextList = list.filter((c) => c.id !== id);
            if (activeId === id) {
              if (nextList.length === 0) {
                setActiveId(null);
                setArtifact(null);
                setArtifacts([]);
                setArtifactOpen(false);
              } else {
                // Determine target conversation:
                // If there is an adjacent item at currentIndex (now the next item), switch to it.
                // If the deleted item was the last item, switch to the previous item (currentIndex - 1).
                const targetIndex = currentIndex < nextList.length ? currentIndex : nextList.length - 1;
                const nextTarget = nextList[Math.max(0, targetIndex)];
                if (nextTarget) {
                  setActiveId(nextTarget.id);
                } else {
                  setActiveId(null);
                }
                setArtifact(null);
                setArtifacts([]);
                setArtifactOpen(false);
              }
            }
            return nextList;
          });
          toast.success("Conversation deleted");
        } catch (e) {
          toast.error("Failed to delete chat");
        }
      },
      send,
      retry,
      stop,
      setModel: (m) => {
        setModelState(m);
      },
      openArtifact: async (a) => {
        // ensure we have content
        if (!a.content) {
          try {
            const fullArtifact = await api.getArtifact(a.id);
            setArtifact(fullArtifact);
          } catch (e) {
            toast.error("Failed to fetch artifact details");
            return;
          }
        } else {
          setArtifact(a);
        }
        setArtifactOpen(true);
      },
      setArtifactOpen,
    }),
    [
      hydrated,
      conversations,
      activeId,
      active,
      model,
      phase,
      error,
      artifact,
      artifacts,
      artifactOpen,
      newChat,
      stop,
      send,
      retry,
    ],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAssistantStore() {
  const s = useContext(Ctx);
  if (!s) throw new Error("useAssistantStore must be used within AssistantProvider");
  return s;
}
