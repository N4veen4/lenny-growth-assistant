import { Button } from "@/components/ui/button";
import { Code2, FileText, PanelRightOpen, Loader2 } from "lucide-react";
import type { Message } from "@/types/assistant";
import { MarkdownPreview } from "./MarkdownPreview";
import { SourceCitation } from "./SourceCitation";
import { useAssistantStore } from "./store";
import { LogoMark } from "./Logo";

export function ChatMessage({ message }: { message: Message }) {
  const { openArtifact } = useAssistantStore();
  if (message.role === "user") {
    return (
      <div className="flex justify-end animate-in fade-in-50 duration-200">
        <div className="max-w-[85%] whitespace-pre-wrap break-words rounded-3xl rounded-br-md border border-border/50 bg-user-surface px-5 py-3 text-[15px] leading-relaxed text-foreground shadow-xs">
          {message.content}
        </div>
      </div>
    );
  }
  const done = message.status === "done" || message.status === undefined;
  const artifact = message.artifact;
  return (
    <div className="flex gap-4 animate-in fade-in-50 duration-200">
      <LogoMark className="mt-0.5 size-7 shrink-0" />
      <div className="min-w-0 flex-1 text-[15px] leading-relaxed">
        {!done && message.statusMsg && (
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-primary/25 bg-primary/10 px-3 py-1 text-xs font-medium text-primary shadow-xs">
            <Loader2 className="size-3.5 animate-spin text-primary" />
            <span>{message.statusMsg}</span>
          </div>
        )}
        {message.content && <MarkdownPreview content={message.content} />}
        {artifact && (
          <Button
            variant="outline"
            onClick={() => openArtifact(artifact)}
            className="mt-5 flex h-auto w-full max-w-md items-center gap-3 whitespace-normal rounded-xl border-border/80 bg-card/80 p-4 text-left shadow-sm transition-all hover:border-primary/50 hover:bg-card"
          >
            <span className="flex size-9 items-center justify-center rounded-lg bg-brand-subtle text-primary">
              {artifact.type === "html" ? (
                <Code2 className="size-4" />
              ) : (
                <FileText className="size-4" />
              )}
            </span>
            <span className="min-w-0 flex-1">
              <span className="block font-medium text-foreground">{artifact.title}</span>
              <span className="text-xs text-muted-foreground">
                {artifact.type === "html" ? "HTML page" : "Markdown document"}
              </span>
            </span>
            <PanelRightOpen className="size-4 text-muted-foreground" />
          </Button>
        )}
        {done && message.sources && <SourceCitation sources={message.sources} />}
      </div>
    </div>
  );
}
