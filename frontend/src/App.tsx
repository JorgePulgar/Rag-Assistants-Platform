import { useState, useEffect, useCallback } from 'react';
import { Layout } from '@/components/Layout';
import { AssistantList } from '@/components/AssistantList';
import { AssistantsPage } from '@/pages/AssistantsPage';
import { AssistantDetailPage } from '@/pages/AssistantDetailPage';
import { ChatPage } from '@/pages/ChatPage';
import { assistantsApi } from '@/api/client';
import type { Assistant } from '@/lib/types';
import { toast } from 'sonner';

type AppView =
  | { type: 'none' }
  | { type: 'detail'; assistantId: string }
  | { type: 'chat'; assistantId: string; conversationId: string; conversationTitle: string };

export default function App() {
  const [assistants, setAssistants] = useState<Assistant[]>([]);
  const [isLoadingAssistants, setIsLoadingAssistants] = useState(true);
  const [view, setView] = useState<AppView>({ type: 'none' });
  const [documentCounts, setDocumentCounts] = useState<Record<string, number>>({});

  const loadAssistants = useCallback(async () => {
    setIsLoadingAssistants(true);
    try {
      const list = await assistantsApi.list();
      setAssistants(list);
    } catch {
      toast.error('Failed to load assistants');
    } finally {
      setIsLoadingAssistants(false);
    }
  }, []);

  useEffect(() => {
    void loadAssistants();
  }, [loadAssistants]);

  const selectedAssistantId =
    view.type === 'none' ? null : view.assistantId;

  const selectedAssistant = assistants.find(a => a.id === selectedAssistantId) ?? null;

  const handleDocumentCountChange = useCallback((assistantId: string, count: number) => {
    setDocumentCounts(prev => ({ ...prev, [assistantId]: count }));
  }, []);

  function handleCreated(assistant: Assistant) {
    setAssistants(prev => [...prev, assistant]);
    setView({ type: 'detail', assistantId: assistant.id });
  }

  function handleUpdated(assistant: Assistant) {
    setAssistants(prev => prev.map(a => (a.id === assistant.id ? assistant : a)));
  }

  function handleDeleted(id: string) {
    setAssistants(prev => prev.filter(a => a.id !== id));
    setView({ type: 'none' });
  }

  function handleOpenChat(conversationId: string, conversationTitle: string) {
    if (!selectedAssistantId) return;
    setView({ type: 'chat', assistantId: selectedAssistantId, conversationId, conversationTitle });
  }

  return (
    <Layout
      sidebar={
        <AssistantList
          assistants={assistants}
          isLoading={isLoadingAssistants}
          selectedId={selectedAssistantId}
          documentCounts={documentCounts}
          onSelect={id => setView({ type: 'detail', assistantId: id })}
          onCreated={handleCreated}
        />
      }
    >
      {view.type === 'none' && <AssistantsPage />}

      {view.type === 'detail' && selectedAssistant && (
        <AssistantDetailPage
          key={selectedAssistant.id}
          assistant={selectedAssistant}
          onUpdated={handleUpdated}
          onDeleted={handleDeleted}
          onOpenChat={handleOpenChat}
          onDocumentCountChange={count =>
            handleDocumentCountChange(selectedAssistant.id, count)
          }
        />
      )}

      {view.type === 'chat' && (
        <ChatPage
          key={view.conversationId}
          conversationId={view.conversationId}
          conversationTitle={view.conversationTitle}
          onBack={() =>
            setView({ type: 'detail', assistantId: view.assistantId })
          }
        />
      )}
    </Layout>
  );
}
