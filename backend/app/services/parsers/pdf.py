import logging

from pypdf import PdfReader

from app.services.parsers import ParsedChunk

logger = logging.getLogger(__name__)

_MIN_PAGE_CHARS = 20


def parse(file_path: str) -> list[ParsedChunk]:
    """Extract text page by page. Each ParsedChunk = one PDF page.

    Pages with fewer than 20 non-whitespace characters are skipped
    (typically blank pages or cover images with no extractable text).
    """
    reader = PdfReader(file_path)
    chunks: list[ParsedChunk] = []
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if len(text.strip()) < _MIN_PAGE_CHARS:
            logger.debug("PDF page %d has too little text, skipping", page_num)
            continue
        chunks.append(ParsedChunk(text=text, page=page_num, section=None))
    return chunks
