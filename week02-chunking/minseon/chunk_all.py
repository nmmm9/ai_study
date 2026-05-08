"""
전체 도메인 데이터 일괄 Chunking 스크립트
data/ 하위 모든 .md 파일을 로드하여 Recursive Character Splitting 후 JSON 저장
"""

import json
import os

from chunker import load_markdown, chunk_text, chunk_markdown_by_headers

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "chunks.json")


def find_markdown_files(base_dir: str) -> list[str]:
    """data/ 하위 모든 .md 파일 경로 수집"""
    md_files = []
    for root, _, files in os.walk(base_dir):
        for f in sorted(files):
            if f.endswith(".md"):
                md_files.append(os.path.join(root, f))
    return md_files


def chunk_all(chunk_size: int = 500, chunk_overlap: int = 50):
    """전체 데이터 일괄 chunking"""
    md_files = find_markdown_files(DATA_DIR)

    if not md_files:
        print("data/ 폴더에 .md 파일이 없습니다.")
        return

    print(f"── 전체 데이터 Chunking ──")
    print(f"  대상 파일: {len(md_files)}개")
    print(f"  chunk_size={chunk_size}, chunk_overlap={chunk_overlap}\n")

    all_chunks = []
    total_chars = 0

    for file_path in md_files:
        rel_path = os.path.relpath(file_path, DATA_DIR)
        category = os.path.dirname(rel_path)
        filename = os.path.basename(rel_path)

        print(f"  [{category}/{filename}]", end=" ")

        text = load_markdown(file_path)
        total_chars += len(text)

        # Recursive Character Splitting
        chunks = chunk_text(text, chunk_size, chunk_overlap)

        # Markdown 헤더 기반 메타데이터 추출
        header_chunks = chunk_markdown_by_headers(text)
        # 첫 번째 헤더에서 제목 추출
        title = header_chunks[0]["metadata"].get("제목", filename) if header_chunks else filename

        for i, chunk_text_content in enumerate(chunks):
            all_chunks.append({
                "id": f"{category}/{filename}#{i}",
                "source": rel_path,
                "category": category,
                "title": title,
                "chunk_index": i,
                "content": chunk_text_content,
                "char_count": len(chunk_text_content),
            })

        print(f"→ {len(chunks)}개 청크")

    # JSON 저장
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    # 통계 출력
    lengths = [c["char_count"] for c in all_chunks]
    print(f"\n{'='*50}")
    print(f"  총 파일 수:    {len(md_files)}개")
    print(f"  총 원본 글자:  {total_chars:,}자")
    print(f"  총 청크 수:    {len(all_chunks)}개")
    print(f"  평균 청크 길이: {sum(lengths) / len(lengths):.0f}자")
    print(f"  최소 / 최대:   {min(lengths)}자 / {max(lengths)}자")
    print(f"{'='*50}")
    print(f"\n  저장 완료: {OUTPUT_FILE}")


if __name__ == "__main__":
    chunk_all()
