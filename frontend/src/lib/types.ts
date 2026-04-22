export interface Assistant {
  id: string;
  name: string;
  instructions: string;
  description: string | null;
  search_index: string;
  created_at: string;
  updated_at: string;
}

export interface Document {
  id: string;
  assistant_id: string;
  filename: string;
  mime_type: string | null;
  size_bytes: number | null;
  chunk_count: number | null;
  status: 'pending' | 'indexed' | 'failed';
  error_message: string | null;
  uploaded_at: string;
}

export interface Conversation {
  id: string;
  assistant_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface Citation {
  document_id: string;
  document_name: string;
  page: number | null;
  chunk_text: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant';
  content: string;
  citations: Citation[] | null;
  created_at: string;
}
