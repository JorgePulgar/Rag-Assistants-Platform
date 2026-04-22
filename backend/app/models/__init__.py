# Import every model here so Base.metadata knows about all tables before create_all() is called.
from app.models.assistant import Assistant as Assistant
from app.models.conversation import Conversation as Conversation
from app.models.document import Document as Document
from app.models.message import Message as Message
