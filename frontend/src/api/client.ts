import axios from 'axios';
import type { Assistant, Document, Conversation, Message } from '@/lib/types';

const api = axios.create({ baseURL: 'http://localhost:8000' });

export const assistantsApi = {
  list: (): Promise<Assistant[]> =>
    api.get<Assistant[]>('/api/assistants').then(r => r.data),
  get: (id: string): Promise<Assistant> =>
    api.get<Assistant>(`/api/assistants/${id}`).then(r => r.data),
  create: (data: { name: string; instructions: string; description?: string }): Promise<Assistant> =>
    api.post<Assistant>('/api/assistants', data).then(r => r.data),
  update: (id: string, data: { name?: string; instructions?: string; description?: string }): Promise<Assistant> =>
    api.patch<Assistant>(`/api/assistants/${id}`, data).then(r => r.data),
  delete: (id: string): Promise<void> =>
    api.delete(`/api/assistants/${id}`).then(() => undefined),
};

export const documentsApi = {
  list: (assistantId: string): Promise<Document[]> =>
    api.get<Document[]>(`/api/assistants/${assistantId}/documents`).then(r => r.data),
  upload: (assistantId: string, file: File): Promise<Document> => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<Document>(`/api/assistants/${assistantId}/documents`, formData).then(r => r.data);
  },
  delete: (assistantId: string, docId: string): Promise<void> =>
    api.delete(`/api/assistants/${assistantId}/documents/${docId}`).then(() => undefined),
};

export const conversationsApi = {
  create: (assistantId: string): Promise<Conversation> =>
    api.post<Conversation>('/api/conversations', { assistant_id: assistantId }).then(r => r.data),
  list: (assistantId: string): Promise<Conversation[]> =>
    api.get<Conversation[]>(`/api/assistants/${assistantId}/conversations`).then(r => r.data),
  messages: (conversationId: string): Promise<Message[]> =>
    api.get<Message[]>(`/api/conversations/${conversationId}/messages`).then(r => r.data),
  sendMessage: (conversationId: string, content: string): Promise<{ message: Message }> =>
    api
      .post<{ message: Message }>(`/api/conversations/${conversationId}/messages`, { content })
      .then(r => r.data),
  delete: (conversationId: string): Promise<void> =>
    api.delete(`/api/conversations/${conversationId}`).then(() => undefined),
};
