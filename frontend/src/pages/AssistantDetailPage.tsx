import { useState, useEffect, useCallback } from 'react';
import { Pencil, Trash2, FileText, Loader2, MessageSquare, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { AssistantForm } from '@/components/AssistantForm';
import { DocumentUploader } from '@/components/DocumentUploader';
import { assistantsApi, documentsApi, conversationsApi } from '@/api/client';
import type { Assistant, Document, Conversation } from '@/lib/types';
import { toast } from 'sonner';

interface AssistantDetailPageProps {
  assistant: Assistant;
  onUpdated: (assistant: Assistant) => void;
  onDeleted: (id: string) => void;
  onOpenChat: (conversationId: string, conversationTitle: string) => void;
  onDocumentCountChange: (count: number) => void;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function StatusBadge({ status }: { status: string }) {
  if (status === 'indexed') {
    return (
      <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-400">
        Indexed
      </span>
    );
  }
  if (status === 'pending') {
    return (
      <span className="inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full bg-amber-50 dark:bg-amber-950/30 text-amber-700 dark:text-amber-400">
        <Loader2 className="h-3 w-3 animate-spin" aria-hidden="true" />
        Pending
      </span>
    );
  }
  return (
    <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-red-50 dark:bg-red-950/30 text-red-700 dark:text-red-400">
      Failed
    </span>
  );
}

export function AssistantDetailPage({
  assistant,
  onUpdated,
  onDeleted,
  onOpenChat,
  onDocumentCountChange,
}: AssistantDetailPageProps) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoadingDocs, setIsLoadingDocs] = useState(true);
  const [isLoadingConvos, setIsLoadingConvos] = useState(true);
  const [showEdit, setShowEdit] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deletingDocId, setDeletingDocId] = useState<string | null>(null);
  const [isCreatingConvo, setIsCreatingConvo] = useState(false);

  const loadDocuments = useCallback(async () => {
    setIsLoadingDocs(true);
    try {
      const docs = await documentsApi.list(assistant.id);
      setDocuments(docs);
      onDocumentCountChange(docs.length);
    } catch {
      toast.error('Failed to load documents');
    } finally {
      setIsLoadingDocs(false);
    }
  // onDocumentCountChange is stable (memoized in parent) — safe to omit here
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [assistant.id]);

  const loadConversations = useCallback(async () => {
    setIsLoadingConvos(true);
    try {
      const convos = await conversationsApi.list(assistant.id);
      setConversations(convos);
    } catch {
      toast.error('Failed to load conversations');
    } finally {
      setIsLoadingConvos(false);
    }
  }, [assistant.id]);

  useEffect(() => {
    void loadDocuments();
    void loadConversations();
  }, [loadDocuments, loadConversations]);

  async function handleDeleteAssistant() {
    setIsDeleting(true);
    try {
      await assistantsApi.delete(assistant.id);
      onDeleted(assistant.id);
      toast.success('Assistant deleted');
    } catch {
      toast.error('Failed to delete assistant');
    } finally {
      setIsDeleting(false);
      setShowDeleteConfirm(false);
    }
  }

  async function handleDeleteDocument(docId: string) {
    setDeletingDocId(docId);
    try {
      await documentsApi.delete(assistant.id, docId);
      setDocuments(prev => {
        const next = prev.filter(d => d.id !== docId);
        onDocumentCountChange(next.length);
        return next;
      });
      toast.success('Document deleted');
    } catch {
      toast.error('Failed to delete document');
    } finally {
      setDeletingDocId(null);
    }
  }

  async function handleStartNewConversation() {
    setIsCreatingConvo(true);
    try {
      const convo = await conversationsApi.create(assistant.id);
      setConversations(prev => [convo, ...prev]);
      onOpenChat(convo.id, convo.title);
    } catch {
      toast.error('Failed to create conversation');
    } finally {
      setIsCreatingConvo(false);
    }
  }

  const docCountLabel = documents.length === 1 ? '1 document' : `${documents.length} documents`;

  return (
    <div className="max-w-[1024px] mx-auto px-8 py-6 space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h1 className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100 leading-tight">
            {assistant.name}
          </h1>
          {assistant.description && (
            <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
              {assistant.description}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Button variant="outline" size="sm" onClick={() => setShowEdit(true)}>
            <Pencil className="h-3.5 w-3.5 mr-1.5" aria-hidden="true" />
            Edit
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950/20"
            onClick={() => setShowDeleteConfirm(true)}
          >
            <Trash2 className="h-3.5 w-3.5 mr-1.5" aria-hidden="true" />
            Delete
          </Button>
        </div>
      </div>

      {/* Instructions */}
      <div>
        <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-3">
          Instructions
        </h2>
        <div className="bg-neutral-50 dark:bg-neutral-900 rounded-lg p-4 font-mono text-xs text-neutral-700 dark:text-neutral-300 whitespace-pre-wrap">
          {assistant.instructions}
        </div>
      </div>

      {/* Documents */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
            Documents
          </h2>
          <span className="text-xs font-medium text-neutral-500 bg-neutral-100 dark:bg-neutral-800 px-2 py-0.5 rounded-full">
            {docCountLabel}
          </span>
        </div>

        <DocumentUploader assistantId={assistant.id} onUploaded={() => void loadDocuments()} />

        {isLoadingDocs ? (
          <div className="mt-4 space-y-2">
            {[1, 2].map(i => (
              <div key={i} className="h-10 rounded bg-neutral-100 dark:bg-neutral-800 animate-pulse" />
            ))}
          </div>
        ) : documents.length === 0 ? (
          <p className="mt-4 text-sm text-neutral-500">No documents uploaded</p>
        ) : (
          <ul className="mt-4 space-y-2">
            {documents.map(doc => (
              <li
                key={doc.id}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-950"
              >
                <FileText className="h-4 w-4 text-neutral-400 shrink-0" aria-hidden="true" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100 truncate">
                    {doc.filename}
                  </p>
                  <p className="text-xs text-neutral-500">{formatDate(doc.uploaded_at)}</p>
                </div>
                <StatusBadge status={doc.status} />
                <button
                  onClick={() => void handleDeleteDocument(doc.id)}
                  disabled={deletingDocId === doc.id}
                  className="p-1.5 rounded text-neutral-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/20 transition-colors disabled:opacity-50"
                  aria-label={`Delete ${doc.filename}`}
                >
                  {deletingDocId === doc.id ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
                  ) : (
                    <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                  )}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Conversations */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
            Conversations
          </h2>
          <Button
            size="sm"
            onClick={() => void handleStartNewConversation()}
            disabled={isCreatingConvo}
          >
            {isCreatingConvo ? (
              <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" aria-hidden="true" />
            ) : (
              <Plus className="h-3.5 w-3.5 mr-1.5" aria-hidden="true" />
            )}
            {isCreatingConvo ? 'Creating…' : 'Start new conversation'}
          </Button>
        </div>

        {isLoadingConvos ? (
          <div className="space-y-2">
            {[1, 2].map(i => (
              <div key={i} className="h-10 rounded bg-neutral-100 dark:bg-neutral-800 animate-pulse" />
            ))}
          </div>
        ) : conversations.length === 0 ? (
          <p className="text-sm text-neutral-500">No conversations yet</p>
        ) : (
          <ul className="space-y-1">
            {conversations.map(convo => (
              <li key={convo.id}>
                <button
                  onClick={() => onOpenChat(convo.id, convo.title)}
                  className="w-full text-left px-3 py-2.5 rounded-lg hover:bg-neutral-50 dark:hover:bg-neutral-900 transition-colors flex items-center gap-3"
                >
                  <MessageSquare className="h-4 w-4 text-neutral-400 shrink-0" aria-hidden="true" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100 truncate">
                      {convo.title}
                    </p>
                    <p className="text-xs text-neutral-500">{formatDate(convo.updated_at)}</p>
                  </div>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <AssistantForm
        open={showEdit}
        onOpenChange={setShowEdit}
        initialValues={assistant}
        onSuccess={updated => {
          onUpdated(updated);
          setShowEdit(false);
        }}
      />

      <Dialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete assistant?</DialogTitle>
            <DialogDescription>
              This will delete {docCountLabel} and all conversations. This cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="ghost"
              onClick={() => setShowDeleteConfirm(false)}
              disabled={isDeleting}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => void handleDeleteAssistant()}
              disabled={isDeleting}
            >
              {isDeleting && <Loader2 className="h-4 w-4 animate-spin mr-2" aria-hidden="true" />}
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
