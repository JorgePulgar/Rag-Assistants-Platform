import logging

from app.services.parsers import ParsedChunk

logger = logging.getLogger(__name__)


def parse(file_path: str) -> list[ParsedChunk]:
    """Read plain text / Markdown as a single chunk. UTF-8 with latin-1 fallback."""
    try:
        text = open(file_path, encoding="utf-8").read()
    except UnicodeDecodeError:
        logger.warning("UTF-8 decode failed for %s, falling back to latin-1", file_path)
        text = open(file_path, encoding="latin-1").read()

    text = text.strip()
    if not text:
        return []
    return [ParsedChunk(text=text, page=None, section=None)]
