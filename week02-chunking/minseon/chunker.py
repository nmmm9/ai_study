"""
2주차 과제: Chunking - CLI 및 결과 출력

[관심사 분리]
  이 파일: 결과 출력 함수 + 커맨드라인 인터페이스 (CLI)
  services/document_loader.py: 파일 형식별 텍스트 추출
  services/chunker.py:         청킹 로직 (Recursive / Markdown 헤더)
"""

import argparse
import os

from services.document_loader import load_document
from services.chunker import chunk_text, chunk_markdown_by_headers


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
