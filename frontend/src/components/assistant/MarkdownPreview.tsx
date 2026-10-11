import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/** Renders markdown safely: raw HTML is not rendered (react-markdown default). */
export function MarkdownPreview({ content }: { content: string }) {
  return (
    <div className="prose-lenny">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  );
}
