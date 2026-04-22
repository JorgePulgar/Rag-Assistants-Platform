import logging

from docx import Document as DocxDocument

from app.services.parsers import ParsedChunk

logger = logging.getLogger(__name__)


def parse(file_path: str) -> list[ParsedChunk]:
    """Extract text grouped by section (heading boundary).

    Paragraphs are accumulated under the most recent heading.
    Each section becomes one ParsedChunk with page=None.
    If there are no headings, all paragraphs form a single chunk.
    """
    doc = DocxDocument(file_path)
    sections: list[tuple[str | None, list[str]]] = []  # (section_title, [paragraph_texts])
    current_section: str | None = None
    current_paragraphs: list[str] = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        if para.style and para.style.name.startswith("Heading"):
            if current_paragraphs:
                sections.append((current_section, current_paragraphs))
            current_section = text
            current_paragraphs = []
        else:
            current_paragraphs.append(text)

    if current_paragraphs:
        sections.append((current_section, current_paragraphs))

    chunks: list[ParsedChunk] = []
    for section_title, paragraphs in sections:
        combined = "\n\n".join(paragraphs)
        if combined.strip():
            chunks.append(ParsedChunk(text=combined, page=None, section=section_title))

    return chunks
