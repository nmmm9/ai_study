"""Hybrid Chunking — Structure-aware primary, fixed-size secondary.

Pass 1: Detect document format (markdown/numbered/csv/plain) → split by structure
Pass 2: Enforce size limits (oversized → sub-split, undersized → merge)

Why hybrid?
- Fixed-size: cuts mid-sentence, loses heading context
- Structure-only: fails on PDFs with no structure
- Semantic: too slow (embed every sentence at upload time)
- Hybrid: best of structure + fixed, works on all file types
"""

import re
from dataclasses import dataclass, field

from langchain_text_splitters import RecursiveCharacterTextSplitter

TARGET_CHARS = 2800  # ~800 tokens
MAX_CHARS = 4200     # ~1200 tokens
OVERLAP_CHARS = 350  # ~100 tokens
MIN_CHARS = 280      # ~80 tokens


@dataclass
class Chunk:
    index: int
    text: str
    start: int
    end: int


# ── Pass 1: Structure-Aware Split ──


def _detect_format(text: str) -> str:
    if text.count("#") > 3 and re.search(r"^#{1,3}\s", text, re.MULTILINE):
        return "markdown"
    if re.search(r"^\d+\.\s+\S", text, re.MULTILINE):
        return "numbered"
    if text.count(",") > text.count("\n") * 2:
        return "csv"
    return "plain"


def _split_by_structure(text: str) -> list[str]:
    fmt = _detect_format(text)

    if fmt == "csv":
        lines = text.split("\n")
        if not lines:
            return [text]
        header = lines[0]
        sections: list[str] = []
        current = header + "\n"
        for line in lines[1:]:
            if len(current) + len(line) > TARGET_CHARS and len(current) > len(header) + 10:
                sections.append(current.strip())
                current = header + "\n"
            current += line + "\n"
        if current.strip() and current.strip() != header.strip():
            sections.append(current.strip())
        return sections if sections else [text]

    if fmt == "markdown":
        parts = re.split(r"(?=\n#{1,3}\s)", text)
        return [p.strip() for p in parts if p.strip()]

    if fmt == "numbered":
        parts = re.split(r"(?=\n\d+\.\s+\S)", text)
        return [p.strip() for p in parts if p.strip()]

    # Plain text: split on double newlines, merge small paragraphs
    parts = text.split("\n\n")
    merged: list[str] = []
    current = ""
    for part in parts:
        if len(current) + len(part) < TARGET_CHARS:
            current += ("\n\n" + part if current else part)
        else:
            if current:
                merged.append(current.strip())
            current = part
    if current.strip():
        merged.append(current.strip())
    return merged if merged else [text]


# ── Pass 2: Size Enforcement ──


def _enforce_size_limits(sections: list[str]) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=TARGET_CHARS,
        chunk_overlap=OVERLAP_CHARS,
        separators=["\n\n", "\n", ". ", " "],
    )

    result: list[str] = []
    for section in sections:
        if len(section) <= MAX_CHARS:
            if result and len(section) < MIN_CHARS:
                result[-1] = result[-1] + "\n\n" + section
            else:
                result.append(section)
        else:
            result.extend(splitter.split_text(section))

    # Re-check merged chunks
    final: list[str] = []
    for chunk in result:
        if len(chunk) > MAX_CHARS:
            final.extend(splitter.split_text(chunk))
        else:
            final.append(chunk)

    return final


# ── Public API ──


def chunk_text(
    text: str,
    chunk_size: int = TARGET_CHARS,
    chunk_overlap: int = OVERLAP_CHARS,
) -> list[Chunk]:
    """Hybrid chunking: structure-aware + size enforcement."""
    sections = _split_by_structure(text)
    texts = _enforce_size_limits(sections)

    chunks = []
    pos = 0
    for i, chunk_content in enumerate(texts):
        start = text.find(chunk_content[:80], pos)
        if start == -1:
            start = text.find(chunk_content[:40])
            if start == -1:
                start = pos
        end = start + len(chunk_content)
        chunks.append(Chunk(index=i, text=chunk_content, start=start, end=end))
        pos = max(pos, start + 1)

    return chunks
