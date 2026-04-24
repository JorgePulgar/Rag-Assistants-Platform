import { AlertCircle } from 'lucide-react';
import { ContentWithCitations } from '@/components/CitationBlock';
import type { Message } from '@/lib/types';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  if (message.role === 'user') {
    return (
      <div className="flex justify-end mt-6">
        <div className="max-w-[70%] px-4 py-2 rounded-2xl rounded-br-md bg-blue-600 text-white text-sm whitespace-pre-wrap">
          {message.content}
        </div>
      </div>
    );
  }

  const citations = message.citations ?? [];

  // Warning style applies only to the two known "I don't know" response prefixes:
  // the hardcoded empty-retrieval message and the LLM's Rule-2 fallback.
  const IDK_PREFIXES = [
    "I did not find relevant information in this assistant's documents to answer your question.",
    "I don't have enough information in my documents to answer this question.",
  ];
  const isIdk = IDK_PREFIXES.some((p) => message.content.startsWith(p));

  return (
    <div className="flex items-start gap-3 mt-6">
      <div className="h-7 w-7 rounded-full bg-blue-600 flex items-center justify-center shrink-0 mt-0.5">
        <span className="text-xs font-medium text-white">A</span>
      </div>

      <div
        className={[
          'max-w-[85%] text-sm leading-relaxed',
          isIdk
            ? 'flex items-start gap-2 text-neutral-600 dark:text-neutral-400'
            : 'text-neutral-900 dark:text-neutral-100',
        ].join(' ')}
      >
        {isIdk && (
          <AlertCircle className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" aria-hidden="true" />
        )}
        <span className="whitespace-pre-wrap">
          <ContentWithCitations content={message.content} citations={citations} />
        </span>
      </div>
    </div>
  );
}

export function ThinkingBubble() {
  return (
    <div className="flex items-start gap-3 mt-6">
      <div className="h-7 w-7 rounded-full bg-blue-600 flex items-center justify-center shrink-0">
        <span className="text-xs font-medium text-white">A</span>
      </div>
      <div className="flex items-center gap-1.5 text-neutral-500 text-sm">
        <span className="h-1.5 w-1.5 rounded-full bg-neutral-400 animate-pulse [animation-delay:0ms]" />
        <span className="h-1.5 w-1.5 rounded-full bg-neutral-400 animate-pulse [animation-delay:150ms]" />
        <span className="h-1.5 w-1.5 rounded-full bg-neutral-400 animate-pulse [animation-delay:300ms]" />
        <span className="ml-1">Thinking…</span>
      </div>
    </div>
  );
}
