import logging

from app.clients import azure_openai
from app.models.message import Message

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You rewrite follow-up questions into standalone search queries.

Given a conversation history and the user's current message, produce a \
single sentence that captures what the user is asking about, including \
enough topical context from prior turns to be meaningful on its own.

Rules:
- Output ONLY the rewritten query. No explanation, no quotes, no prefix.
- If the user's message is already self-contained (introduces a new topic), \
return it unchanged.
- Keep the user's language (Spanish queries stay in Spanish).
- Preserve specific proper nouns, numbers, and technical terms from the history.
- Target length: 10–30 words."""


def rewrite_query(history: list[Message], user_message: str) -> str:
    """Rewrite a follow-up user message into a standalone search query.

    Sends the last N history messages and the current user message to the LLM.
    Returns the rewritten query, or the original message if the LLM returns empty.
    """
    history_text = "\n".join(f"{msg.role}: {msg.content}" for msg in history)
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Conversation history:\n{history_text}\n\n"
                f"User's current message: {user_message}"
            ),
        },
    ]
    rewritten = azure_openai.call_llm(messages).strip()
    if not rewritten:
        logger.warning("Query rewriter returned empty string; using original query")
        return user_message
    logger.info("Query rewriting: original=%r rewritten=%r", user_message, rewritten)
    return rewritten
