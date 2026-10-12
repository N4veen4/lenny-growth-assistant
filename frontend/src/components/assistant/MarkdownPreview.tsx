import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Check, Copy } from "lucide-react";

function CodeBlock({ children, className, ...props }: any) {
  const [copied, setCopied] = useState(false);
  const codeString = String(children).replace(/\n$/, "");
  const isInline = !className && !codeString.includes("\n");

  if (isInline) {
    return (
      <code
        className="rounded-md bg-[#212121] px-1.5 py-0.5 font-mono text-[0.875em] text-[#ECECEC] border border-[#333333]/60"
        {...props}
      >
        {children}
      </code>
    );
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(codeString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative my-3 group rounded-2xl border border-[#333333]/70 bg-[#212121] p-4 text-[#ECECEC] font-mono text-[14px] leading-relaxed shadow-sm">
      <button
        onClick={handleCopy}
        aria-label="Copy code"
        title="Copy code"
        className="absolute top-3 right-3 flex size-7 items-center justify-center rounded-lg bg-[#2f2f2f]/80 text-[#B4B4B4] transition-all hover:bg-[#3f3f3f] hover:text-[#FFFFFF]"
      >
        {copied ? <Check className="size-3.5 text-emerald-400" /> : <Copy className="size-3.5" />}
      </button>
      <pre className="overflow-x-auto pr-8">
        <code className={className} {...props}>
          {children}
        </code>
      </pre>
    </div>
  );
}

/** Renders markdown safely: raw HTML is not rendered (react-markdown default). */
export function MarkdownPreview({ content }: { content: string }) {
  return (
    <div className="prose-lenny">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code: CodeBlock,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
