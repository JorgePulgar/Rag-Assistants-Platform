import { useState } from 'react';
import { Plus, MessageSquare } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { AssistantForm } from '@/components/AssistantForm';
import type { Assistant } from '@/lib/types';

interface AssistantListProps {
  assistants: Assistant[];
  isLoading: boolean;
  selectedId: string | null;
  documentCounts: Record<string, number>;
  onSelect: (id: string) => void;
  onCreated: (assistant: Assistant) => void;
}

export function AssistantList({
  assistants,
  isLoading,
  selectedId,
  documentCounts,
  onSelect,
  onCreated,
}: AssistantListProps) {
  const [showCreate, setShowCreate] = useState(false);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-3 pt-4 pb-2">
        <span className="text-xs font-medium uppercase tracking-wide text-neutral-500">
          Assistants
        </span>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 px-2 text-xs gap-1"
          onClick={() => setShowCreate(true)}
        >
          <Plus className="h-3 w-3" aria-hidden="true" />
          New
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-4">
        {isLoading ? (
          <div className="space-y-1 mt-1">
            {[1, 2, 3].map(i => (
              <div
                key={i}
                className="h-12 rounded-md bg-neutral-200 dark:bg-neutral-800 animate-pulse"
              />
            ))}
          </div>
        ) : assistants.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
            <MessageSquare
              className="h-8 w-8 text-neutral-300 dark:text-neutral-700 mb-3"
              aria-hidden="true"
            />
            <p className="text-sm text-neutral-500">No assistants yet</p>
            <Button
              variant="ghost"
              size="sm"
              className="mt-2 text-xs"
              onClick={() => setShowCreate(true)}
            >
              Create your first assistant
            </Button>
          </div>
        ) : (
          <ul className="space-y-0.5 mt-1">
            {assistants.map(assistant => {
              const isSelected = assistant.id === selectedId;
              const count = documentCounts[assistant.id];
              return (
                <li key={assistant.id}>
                  <button
                    onClick={() => onSelect(assistant.id)}
                    className={[
                      'w-full text-left px-3 py-2.5 rounded-md transition-colors border-l-2',
                      isSelected
                        ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-600'
                        : 'border-transparent hover:bg-neutral-100 dark:hover:bg-neutral-800',
                    ].join(' ')}
                  >
                    <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100 truncate">
                      {assistant.name}
                    </p>
                    {count !== undefined && (
                      <p className="text-xs text-neutral-500 mt-0.5">
                        {count === 1 ? '1 document' : `${count} documents`}
                      </p>
                    )}
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      <AssistantForm
        open={showCreate}
        onOpenChange={setShowCreate}
        onSuccess={a => {
          onCreated(a);
          setShowCreate(false);
        }}
      />
    </div>
  );
}
