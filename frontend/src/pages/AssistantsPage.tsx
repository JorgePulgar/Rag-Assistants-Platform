import { MessageSquare } from 'lucide-react';

export function AssistantsPage() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-4">
      <MessageSquare
        className="h-12 w-12 text-neutral-300 dark:text-neutral-700 mb-4"
        aria-hidden="true"
      />
      <h2 className="text-lg text-neutral-600 dark:text-neutral-400">
        Select an assistant to start
      </h2>
      <p className="text-sm text-neutral-500 mt-1">Or create a new one from the sidebar.</p>
    </div>
  );
}
