import { useState } from 'react';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import type { Citation } from '@/lib/types';

interface CitationPillProps {
  index: number;
  citation: Citation;
}

function CitationPill({ index, citation }: CitationPillProps) {
  const [open, setOpen] = useState(false);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          className={[
            'inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ml-0.5',
            'bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300',
            'hover:bg-blue-100 dark:hover:bg-blue-900/40 cursor-pointer transition-colors',
          ].join(' ')}
          aria-label={`Citation ${index}: ${citation.document_name}`}
        >
          [{index}]
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-80 p-4" side="top" align="start">
        <div className="space-y-2">
          <p className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
            {citation.document_name}
          </p>
          {citation.page !== null && (
            <p className="text-xs text-neutral-500">Page {citation.page}</p>
          )}
          <p className="text-xs font-mono bg-neutral-50 dark:bg-neutral-900 rounded p-2 whitespace-pre-wrap break-words text-neutral-700 dark:text-neutral-300">
            {citation.chunk_text}
          </p>
        </div>
      </PopoverContent>
    </Popover>
  );
}

function ImplicitCitationPill({ index, citation }: CitationPillProps) {
  const [open, setOpen] = useState(false);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          className={[
            'inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium',
            'bg-neutral-100 dark:bg-neutral-800 text-neutral-500 dark:text-neutral-400',
            'hover:bg-neutral-200 dark:hover:bg-neutral-700 cursor-pointer transition-colors',
          ].join(' ')}
          aria-label={`Source ${index}: ${citation.document_name}`}
        >
          [{index}]
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-80 p-4" side="top" align="start">
        <div className="space-y-2">
          <p className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
            {citation.document_name}
          </p>
          {citation.page !== null && (
            <p className="text-xs text-neutral-500">Page {citation.page}</p>
          )}
          <p className="text-xs font-mono bg-neutral-50 dark:bg-neutral-900 rounded p-2 whitespace-pre-wrap break-words text-neutral-700 dark:text-neutral-300">
            {citation.chunk_text}
          </p>
        </div>
      </PopoverContent>
    </Popover>
  );
}

interface ImplicitCitationsProps {
  citations: Citation[];
}

export function ImplicitCitations({ citations }: ImplicitCitationsProps) {
  if (citations.length === 0) return null;
  return (
    <div className="mt-2 flex flex-wrap items-center gap-1.5">
      <span className="text-xs text-neutral-500 dark:text-neutral-400">Sources consulted:</span>
      {citations.map((citation, i) => (
        <ImplicitCitationPill key={i} index={i + 1} citation={citation} />
      ))}
    </div>
  );
}

interface ContentWithCitationsProps {
  content: string;
  citations: Citation[];
}

export function ContentWithCitations({ content, citations }: ContentWithCitationsProps) {
  const parts = content.split(/(\[\d+\])/g);
  return (
    <>
      {parts.map((part, i) => {
        const match = part.match(/^\[(\d+)\]$/);
        if (match) {
          const idx = parseInt(match[1], 10);
          const citation = citations[idx - 1];
          if (citation) {
            return <CitationPill key={i} index={idx} citation={citation} />;
          }
        }
        return <span key={i}>{part}</span>;
      })}
    </>
  );
}
