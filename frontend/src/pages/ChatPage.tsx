import { useState, useEffect, useRef, useCallback } from 'react';
import { Send, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { MessageBubble, ThinkingBubble } from '@/components/MessageBubble';
import { conversationsApi } from '@/api/client';
import type { Message } from '@/lib/types';
import { toast } from 'sonner';

interface ChatPageProps {
  conversationId: string;
  conversationTitle: string;
  onBack: () => void;
}

export function ChatPage({ conversationId, conversationTitle, onBack }: ChatPageProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setIsLoading(true);
      try {
        const msgs = await conversationsApi.messages(conversationId);
        if (!cancelled) setMessages(msgs);
      } catch {
        if (!cancelled) toast.error('Failed to load messages');
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }
    void load();
    return () => { cancelled = true; };
  }, [conversationId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking]);

  const sendMessage = useCallback(async () => {
    const content = input.trim();
    if (!content || isThinking) return;

    const optimistic: Message = {
      id: `tmp-${Date.now()}`,
      conversation_id: conversationId,
      role: 'user',
      content,
      citations: null,
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, optimistic]);
    setInput('');
    setIsThinking(true);

    try {
      const { message } = await conversationsApi.sendMessage(conversationId, content);
      setMessages(prev => [...prev, message]);
    } catch {
      toast.error('Failed to send message');
      setMessages(prev => prev.filter(m => m.id !== optimistic.id));
      setInput(content);
    } finally {
      setIsThinking(false);
    }
  }, [input, isThinking, conversationId]);

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      void sendMessage();
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 px-6 py-3 border-b border-neutral-200 dark:border-neutral-800 shrink-0">
        <Button variant="ghost" size="icon" onClick={onBack} aria-label="Back to assistant">
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <h2 className="text-sm font-medium text-neutral-900 dark:text-neutral-100 truncate">
          {conversationTitle}
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-4">
        <div className="max-w-[1024px] mx-auto">
          {isLoading ? (
            <div className="space-y-6 mt-6">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-8 rounded bg-neutral-100 dark:bg-neutral-800 animate-pulse" />
              ))}
            </div>
          ) : messages.length === 0 ? (
            <p className="text-center text-sm text-neutral-500 mt-12">
              Ask anything about the documents…
            </p>
          ) : (
            messages.map(msg => <MessageBubble key={msg.id} message={msg} />)
          )}
          {isThinking && <ThinkingBubble />}
          <div ref={bottomRef} />
        </div>
      </div>

      <div className="border-t border-neutral-200 dark:border-neutral-800 p-4 shrink-0">
        <div className="max-w-[1024px] mx-auto flex items-end gap-3">
          <Textarea
            className="flex-1 resize-none min-h-[40px] max-h-[144px]"
            rows={1}
            placeholder="Ask anything about the documents…"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isThinking}
          />
          <Button
            size="icon"
            onClick={() => void sendMessage()}
            disabled={!input.trim() || isThinking}
            aria-label="Send message"
            className="shrink-0"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
