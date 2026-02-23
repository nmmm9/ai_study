"""
2주차 과제: Chunking - PDF/Markdown 로드 및 Recursive Character Splitting
도메인 데이터를 의미 단위로 분할하는 파이프라인
"""

import argparse
import os

import fitz  # pymupdf
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
)


# ── 문서 로딩 ─────────────────────────────────────────

def load_pdf(file_path: str) -> str:
    """PDF 파일을 텍스트로 변환 (pymupdf - 한국어 인코딩에 강함)"""
    doc = fitz.open(file_path)
    pages_text = [page.get_text() for page in doc]
    text = "\n\n".join(pages_text)
    print(f"  PDF 로드 완료: {len(doc)}페이지, {len(text)}자")
    return text


def load_markdown(file_path: str) -> str:
    """Markdown 파일을 텍스트로 읽기"""
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    print(f"  Markdown 로드 완료: {len(text)}자")
    return text


def load_document(file_path: str) -> str:
    """파일 확장자에 따라 적절한 로더 선택"""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return load_pdf(file_path)
    elif ext in (".md", ".markdown"):
        return load_markdown(file_path)
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        print(f"  텍스트 로드 완료: {len(text)}자")
        return text
    else:
        raise ValueError(f"지원하지 않는 파일 형식: {ext}")


# ── Recursive Character Splitting ─────────────────────

def chunk_text(
    text: str,
    chunk_size: int = 900,
    chunk_overlap: int = 90,
) -> list[str]:
    """
    Recursive Character Splitting으로 텍스트를 의미 단위로 분할

    구분자 우선순위:
      1. 빈 줄 (문단 구분)
      2. 줄바꿈
      3. 마침표/물음표/느낌표 (문장 구분)
      4. 공백 (단어 구분)
      5. 빈 문자열 (글자 단위 - 최후 수단)
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""],
        length_function=len,
    )

    chunks = splitter.split_text(text)
    return chunks


# ── Markdown 구조 기반 분할 (보너스) ──────────────────

def chunk_markdown_by_headers(text: str) -> list[dict]:
    """Markdown 헤더 구조를 활용한 분할 (메타데이터 포함)"""
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#", "제목"),
            ("##", "소제목"),
            ("###", "절"),
        ]
    )
    docs = splitter.split_text(text)
    return [
        {
            "content": doc.page_content,
            "metadata": doc.metadata,
        }
        for doc in docs
    ]


# ── 결과 출력 ─────────────────────────────────────────

def print_chunks(chunks: list[str], preview_length: int = 80):
    """청크 분할 결과를 보기 좋게 출력"""
    lengths = [len(c) for c in chunks]

    print(f"\n{'='*60}")
    print(f"  총 청크 수: {len(chunks)}개")
    print(f"  평균 길이:  {sum(lengths) / len(lengths):.0f}자")
    print(f"  최소 길이:  {min(lengths)}자")
    print(f"  최대 길이:  {max(lengths)}자")
    print(f"{'='*60}\n")

    for i, chunk in enumerate(chunks):
        preview = chunk[:preview_length].replace("\n", " ")
        if len(chunk) > preview_length:
            preview += "..."
        print(f"  [{i+1:3d}] ({len(chunk):4d}자) {preview}")

    print()


def print_markdown_chunks(chunks: list[dict], preview_length: int = 80):
    """Markdown 헤더 기반 분할 결과 출력"""
    print(f"\n{'='*60}")
    print(f"  Markdown 구조 기반 분할: {len(chunks)}개 섹션")
    print(f"{'='*60}\n")

    for i, chunk in enumerate(chunks):
        metadata = " > ".join(f"{k}: {v}" for k, v in chunk["metadata"].items())
        preview = chunk["content"][:preview_length].replace("\n", " ")
        if len(chunk["content"]) > preview_length:
            preview += "..."
        print(f"  [{i+1:3d}] [{metadata}]")
        print(f"        ({len(chunk['content']):4d}자) {preview}")
        print()


# ── CLI ───────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="PDF/Markdown 문서를 Recursive Character Splitting으로 분할"
    )
    parser.add_argument("file", help="분할할 파일 경로 (PDF, Markdown, TXT)")
    parser.add_argument(
        "--chunk-size", type=int, default=900,
        help="청크 최대 글자 수 (기본값: 900)"
    )
    parser.add_argument(
        "--chunk-overlap", type=int, default=90,
        help="청크 간 겹침 글자 수 (기본값: 90)"
    )
    parser.add_argument(
        "--md-headers", action="store_true",
        help="Markdown 파일일 때 헤더 기반 분할도 함께 실행"
    )

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"파일을 찾을 수 없습니다: {args.file}")
        return

    # 1) 문서 로딩
    print(f"\n── 문서 로딩 ──")
    text = load_document(args.file)

    # 2) Recursive Character Splitting
    print(f"\n── Recursive Character Splitting ──")
    print(f"  chunk_size={args.chunk_size}, chunk_overlap={args.chunk_overlap}")

    chunks = chunk_text(text, args.chunk_size, args.chunk_overlap)
    print_chunks(chunks)

    # 3) Markdown 헤더 기반 분할 (옵션)
    ext = os.path.splitext(args.file)[1].lower()
    if args.md_headers and ext in (".md", ".markdown"):
        print(f"── Markdown 헤더 기반 분할 ──")
        md_chunks = chunk_markdown_by_headers(text)
        print_markdown_chunks(md_chunks)


if __name__ == "__main__":
    main()
