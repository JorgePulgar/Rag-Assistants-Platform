from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from app.exceptions import IngestionError


@dataclass
class ParsedChunk:
    """Raw text unit produced by a parser before the splitter is applied."""

    text: str
    page: int | None
    section: str | None


def resolve_parser(filename: str) -> Callable[[str], list[ParsedChunk]]:
    """Return the parser function for the given filename's extension."""
    from app.services.parsers.docx import parse as parse_docx
    from app.services.parsers.pdf import parse as parse_pdf
    from app.services.parsers.pptx import parse as parse_pptx
    from app.services.parsers.text import parse as parse_text

    ext = Path(filename).suffix.lower()
    mapping: dict[str, Callable[[str], list[ParsedChunk]]] = {
        ".pdf": parse_pdf,
        ".docx": parse_docx,
        ".pptx": parse_pptx,
        ".txt": parse_text,
        ".md": parse_text,
    }
    if ext not in mapping:
        raise IngestionError(f"Unsupported file format: '{ext}'")
    return mapping[ext]
