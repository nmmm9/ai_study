"""Document ingestion — turn raw files into chunks ready for embedding.

Supported inputs:
- .txt / .md (plain text)
- .pdf (via pypdf)

Chunking strategy: paragraph-aware sliding window.
- Target ~600 tokens (~2400 chars) per chunk
- 100-char overlap between chunks (preserves context across boundaries)
- Splits on double newlines first, then merges to target size
"""

from __future__ import annotations

import os
import re
from typing import Optional

from services.document_store import Chunk, new_doc_id, new_chunk_id, add_chunks


CHUNK_SIZE = 2400   # ~600 tokens
CHUNK_OVERLAP = 100


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _read_pdf(path: str) -> list[tuple[int, str]]:
    """Return list of (page_number, text) starting from page 1."""
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise RuntimeError("pypdf 가 설치되지 않았습니다. pip install pypdf") from e

    reader = PdfReader(path)
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        if text.strip():
            pages.append((i, text))
    return pages


def _normalize(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _split_into_chunks(text: str, max_chars: int = CHUNK_SIZE,
                       overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Paragraph-aware chunking. Falls back to character window for long blocks."""
    text = _normalize(text)
    if not text:
        return []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buf = ""

    def flush():
        nonlocal buf
        if buf.strip():
            chunks.append(buf.strip())
        buf = ""

    for p in paragraphs:
        # If a single paragraph is longer than max_chars, hard-split it
        if len(p) > max_chars:
            flush()
            i = 0
            while i < len(p):
                end = min(i + max_chars, len(p))
                chunks.append(p[i:end])
                i = end - overlap if end < len(p) else end
            continue

        if len(buf) + 2 + len(p) <= max_chars:
            buf = (buf + "\n\n" + p) if buf else p
        else:
            flush()
            buf = p
    flush()

    # Add small overlap from previous chunk's tail
    if overlap > 0 and len(chunks) > 1:
        overlapped: list[str] = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_tail = chunks[i - 1][-overlap:]
            overlapped.append(prev_tail + "\n" + chunks[i])
        chunks = overlapped

    return chunks


async def ingest_text(text: str, doc_name: str) -> dict:
    """Ingest plain text. Returns {doc_id, doc_name, chunks_added}."""
    doc_id = new_doc_id()
    pieces = _split_into_chunks(text)
    chunks = [
        Chunk(
            id=new_chunk_id(doc_id, i),
            text=piece,
            doc_id=doc_id,
            doc_name=doc_name,
            chunk_index=i,
            page=None,
        )
        for i, piece in enumerate(pieces)
    ]
    added = await add_chunks(chunks)
    return {"doc_id": doc_id, "doc_name": doc_name, "chunks_added": added}


async def ingest_pdf(path: str, doc_name: Optional[str] = None) -> dict:
    """Ingest a PDF. Each page is chunked separately so `page` metadata is correct."""
    doc_name = doc_name or os.path.basename(path)
    doc_id = new_doc_id()
    pages = _read_pdf(path)

    all_chunks: list[Chunk] = []
    chunk_idx = 0
    for page_no, page_text in pages:
        for piece in _split_into_chunks(page_text):
            all_chunks.append(Chunk(
                id=new_chunk_id(doc_id, chunk_idx),
                text=piece,
                doc_id=doc_id,
                doc_name=doc_name,
                chunk_index=chunk_idx,
                page=page_no,
            ))
            chunk_idx += 1

    added = await add_chunks(all_chunks)
    return {"doc_id": doc_id, "doc_name": doc_name, "chunks_added": added}


async def ingest_file(path: str, doc_name: Optional[str] = None) -> dict:
    """Auto-dispatch by extension."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return await ingest_pdf(path, doc_name)
    if ext in (".txt", ".md", ".markdown"):
        text = _read_text(path)
        return await ingest_text(text, doc_name or os.path.basename(path))
    raise ValueError(f"지원하지 않는 파일 형식: {ext}")
