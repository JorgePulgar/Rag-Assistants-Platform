class AssistantNotFoundError(Exception):
    def __init__(self, assistant_id: str) -> None:
        self.assistant_id = assistant_id
        super().__init__(f"Assistant '{assistant_id}' not found")


class DocumentNotFoundError(Exception):
    def __init__(self, document_id: str) -> None:
        self.document_id = document_id
        super().__init__(f"Document '{document_id}' not found")


class ConversationNotFoundError(Exception):
    def __init__(self, conversation_id: str) -> None:
        self.conversation_id = conversation_id
        super().__init__(f"Conversation '{conversation_id}' not found")


class IngestionError(Exception):
    pass


class RetrievalError(Exception):
    pass
