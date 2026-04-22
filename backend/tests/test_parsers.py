"""Parser tests — one fixture file per supported format (T017)."""
from pathlib import Path

import pytest

from app.services.parsers import ParsedChunk
from app.services.parsers.docx import parse as parse_docx
from app.services.parsers.pdf import parse as parse_pdf
from app.services.parsers.pptx import parse as parse_pptx
from app.services.parsers.text import parse as parse_text

FIXTURES = Path(__file__).parent / "fixtures"


def _path(name: str) -> str:
    return str(FIXTURES / name)


# ── PDF ──────────────────────────────────────────────────────────────────────


def test_pdf_parser_returns_chunks() -> None:
    chunks = parse_pdf(_path("sample.pdf"))
    assert len(chunks) >= 1, "PDF parser returned no chunks"


def test_pdf_parser_chunk_has_text() -> None:
    chunks = parse_pdf(_path("sample.pdf"))
    assert all(c.text.strip() for c in chunks), "Some PDF chunks have empty text"


def test_pdf_parser_sets_page_numbers() -> None:
    chunks = parse_pdf(_path("sample.pdf"))
    for chunk in chunks:
        assert isinstance(chunk.page, int), "PDF chunk should have an integer page"
        assert chunk.page >= 1, "PDF page numbers are 1-indexed"


def test_pdf_parser_page_is_none_in_text_parser() -> None:
    """Sanity check: text parser should NOT set page (contrast with PDF)."""
    chunks = parse_text(_path("sample.txt"))
    assert all(c.page is None for c in chunks)


# ── DOCX ─────────────────────────────────────────────────────────────────────


def test_docx_parser_returns_chunks() -> None:
    chunks = parse_docx(_path("sample.docx"))
    assert len(chunks) >= 1


def test_docx_parser_chunk_has_text() -> None:
    chunks = parse_docx(_path("sample.docx"))
    assert all(c.text.strip() for c in chunks)


def test_docx_parser_page_is_none() -> None:
    chunks = parse_docx(_path("sample.docx"))
    assert all(c.page is None for c in chunks), "DOCX has no page concept"


def test_docx_parser_propagates_section_from_heading() -> None:
    chunks = parse_docx(_path("sample.docx"))
    sections = [c.section for c in chunks if c.section]
    assert sections, "Expected at least one section from DOCX headings"


# ── PPTX ─────────────────────────────────────────────────────────────────────


def test_pptx_parser_returns_chunks() -> None:
    chunks = parse_pptx(_path("sample.pptx"))
    assert len(chunks) >= 1


def test_pptx_parser_chunk_has_text() -> None:
    chunks = parse_pptx(_path("sample.pptx"))
    assert all(c.text.strip() for c in chunks)


def test_pptx_parser_sets_slide_number() -> None:
    chunks = parse_pptx(_path("sample.pptx"))
    assert chunks[0].page == 1, "First slide should be page 1"


# ── TXT / MD ─────────────────────────────────────────────────────────────────


def test_text_parser_txt() -> None:
    chunks = parse_text(_path("sample.txt"))
    assert len(chunks) == 1
    assert "plain-text" in chunks[0].text


def test_text_parser_md() -> None:
    chunks = parse_text(_path("sample.md"))
    assert len(chunks) == 1
    assert chunks[0].page is None


def test_text_parser_empty_file(tmp_path: Path) -> None:
    empty = tmp_path / "empty.txt"
    empty.write_text("")
    assert parse_text(str(empty)) == []


# ── resolve_parser ────────────────────────────────────────────────────────────


def test_resolve_parser_pdf() -> None:
    from app.services.parsers import resolve_parser

    fn = resolve_parser("report.pdf")
    assert fn is parse_pdf


def test_resolve_parser_unsupported_raises() -> None:
    from app.exceptions import IngestionError
    from app.services.parsers import resolve_parser

    with pytest.raises(IngestionError, match="Unsupported"):
        resolve_parser("archive.zip")
