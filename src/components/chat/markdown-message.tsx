"use client";

import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type MarkdownMessageProps = {
  content: string;
  onCitationClick?: (citation: { is_number: string; clause: string }) => void;
};

function formatCitationText(
  text: string,
  onCitationClick?: (citation: { is_number: string; clause: string }) => void,
): React.ReactNode {
  // Regex to match [IS 13252 -> Clause 4.1], [IS 13252 : Clause 4.1], etc.
  const regex = /\[(IS\s*[^\]\-:>]+?)\s*(?:->|:)\s*(?:Clause\s*)?([^\]]+?)\]/gi;
  if (!regex.test(text)) {
    return text;
  }
  regex.lastIndex = 0;

  const elements: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      elements.push(text.slice(lastIndex, match.index));
    }
    const isNum = match[1].trim();
    const clause = match[2].trim();
    elements.push(
      <button
        key={`${isNum}-${clause}-${match.index}`}
        type="button"
        onClick={() => onCitationClick?.({ is_number: isNum, clause })}
        title={`Verified BIS Standard: ${isNum} Clause ${clause}`}
        className="mx-1 inline-flex items-center gap-1 rounded-md border border-emerald-500/30 bg-emerald-500/10 px-1.5 py-0.5 text-[0.85em] font-semibold text-emerald-800 transition hover:bg-emerald-500/25 dark:border-emerald-500/40 dark:text-emerald-300"
      >
        <span className="inline-block size-1.5 rounded-full bg-emerald-500" />
        {isNum} → Clause {clause}
      </button>,
    );
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < text.length) {
    elements.push(text.slice(lastIndex));
  }

  return elements;
}

export function MarkdownMessage({ content, onCitationClick }: MarkdownMessageProps) {
  return (
    <div className="prose-maanak text-sm leading-6">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          p: ({ children }) => {
            if (typeof children === "string") {
              return (
                <p className="my-2 leading-relaxed">
                  {formatCitationText(children, onCitationClick)}
                </p>
              );
            }
            return <p className="my-2 leading-relaxed">{children}</p>;
          },
          a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noreferrer" className="underline">
              {children}
            </a>
          ),
          table: ({ children }) => (
            <div className="my-2 overflow-x-auto rounded-lg border">
              <table className="w-full text-left text-xs">{children}</table>
            </div>
          ),
          th: ({ children }) => (
            <th className="border-b bg-muted/60 px-2 py-1.5 font-medium">{children}</th>
          ),
          td: ({ children }) => <td className="border-b px-2 py-1.5 align-top">{children}</td>,
          ul: ({ children }) => <ul className="my-2 list-disc space-y-1 pl-4">{children}</ul>,
          ol: ({ children }) => <ol className="my-2 list-decimal space-y-1 pl-4">{children}</ol>,
          code: ({ className, children }) => {
            const isBlock = Boolean(className);
            if (isBlock) {
              return (
                <code className="block overflow-x-auto rounded-md bg-muted p-2 text-xs">
                  {children}
                </code>
              );
            }
            return (
              <code className="rounded bg-muted px-1 py-0.5 text-[0.85em]">{children}</code>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
