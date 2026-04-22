class AssistantNotFoundError(Exception):
    def __init__(self, assistant_id: str) -> None:
        self.assistant_id = assistant_id
        super().__init__(f"Assistant '{assistant_id}' not found")


class IngestionError(Exception):
    pass


class RetrievalError(Exception):
    pass
