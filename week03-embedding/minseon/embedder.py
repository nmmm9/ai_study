"""
3주차 과제: Embedding & Vector DB - 문서 임베딩 및 유사도 검색
OpenAI 임베딩 + numpy 코사인 유사도로 구성하는 RAG 파이프라인
"""

import argparse
import json
import os

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

client = OpenAI()

# ── 설정 ──────────────────────────────────────────────
EMBEDDING_MODEL = "text-embedding-3-small"
CHUNK_SIZE = 900
CHUNK_OVERLAP = 90
DB_PATH = "./vector_db.json"


# ── 문서 로딩 ──────────────────────────────────────────

def load_document(file_path: str) -> str:
    """파일 확장자에 따라 텍스트 추출"""
    ext = os.path.splitext(file_path)[1].lower()

    if ext in (".md", ".markdown", ".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    elif ext == ".pdf":
        import fitz
        doc = fitz.open(file_path)
        text = "\n\n".join(page.get_text() for page in doc)
    else:
        raise ValueError(f"지원하지 않는 파일 형식: {ext}")

    print(f"  문서 로드 완료: {len(text)}자")
    return text


# ── 청킹 ──────────────────────────────────────────────

def split_text(text: str) -> list[str]:
    """2주차와 동일한 Recursive Character Splitting"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""],
        length_function=len,
    )
    chunks = splitter.split_text(text)
    print(f"  청킹 완료: {len(chunks)}개 청크")
    return chunks


# ── 임베딩 ────────────────────────────────────────────

def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    OpenAI text-embedding-3-small으로 텍스트 리스트를 벡터로 변환

    - 한 번의 API 호출로 여러 텍스트를 배치 처리
    - 반환값: 각 텍스트에 대응하는 1536차원 벡터 리스트
    """
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )
    vectors = [item.embedding for item in response.data]
    print(f"  임베딩 완료: {len(vectors)}개 벡터 (차원: {len(vectors[0])})")
    return vectors


# ── Vector DB (JSON + numpy) ───────────────────────────

def load_db(db_path: str = DB_PATH) -> dict:
    """저장된 벡터 DB 로드 (없으면 빈 구조 반환)"""
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"chunks": [], "vectors": [], "metadatas": []}


def save_db(db: dict, db_path: str = DB_PATH) -> None:
    """벡터 DB를 JSON 파일로 저장"""
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False)


def store_embeddings(
    chunks: list[str],
    vectors: list[list[float]],
    source: str,
    db_path: str = DB_PATH,
) -> None:
    """청크와 벡터를 JSON DB에 저장 (기존 데이터에 추가)"""
    db = load_db(db_path)

    # 같은 소스 파일은 덮어쓰기
    existing = [(c, v, m) for c, v, m in zip(db["chunks"], db["vectors"], db["metadatas"])
                if m.get("source") != source]
    db["chunks"] = [x[0] for x in existing]
    db["vectors"] = [x[1] for x in existing]
    db["metadatas"] = [x[2] for x in existing]

    for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
        db["chunks"].append(chunk)
        db["vectors"].append(vector)
        db["metadatas"].append({"source": source, "chunk_index": i})

    save_db(db, db_path)
    print(f"  벡터DB 저장 완료: {len(chunks)}개 청크 → '{db_path}'")


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """두 벡터의 코사인 유사도 계산"""
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def search(
    query: str,
    top_k: int = 3,
    db_path: str = DB_PATH,
) -> list[dict]:
    """
    사용자 질문을 임베딩 후 코사인 유사도로 가장 유사한 청크 검색

    1. 질문 텍스트 → 임베딩 벡터
    2. 저장된 모든 벡터와 코사인 유사도 계산
    3. 유사도 높은 top_k개 청크 반환
    """
    db = load_db(db_path)
    if not db["chunks"]:
        return []

    query_vector = embed_texts([query])[0]

    similarities = [
        cosine_similarity(query_vector, vec)
        for vec in db["vectors"]
    ]

    top_indices = np.argsort(similarities)[::-1][:top_k]

    hits = []
    for idx in top_indices:
        hits.append({
            "content": db["chunks"][idx],
            "similarity": similarities[idx],
            "metadata": db["metadatas"][idx],
        })
    return hits


# ── 결과 출력 ─────────────────────────────────────────

def print_results(hits: list[dict], preview_length: int = 150) -> None:
    """검색 결과 출력"""
    print(f"\n{'='*60}")
    print(f"  검색 결과: {len(hits)}개  |  임베딩 모델: {EMBEDDING_MODEL}")
    print(f"{'='*60}\n")

    for i, hit in enumerate(hits):
        sim = hit["similarity"]
        preview = hit["content"][:preview_length].replace("\n", " ")
        if len(hit["content"]) > preview_length:
            preview += "..."

        print(f"  [{i+1}] 유사도: {sim:.4f} ({sim*100:.1f}%) | 출처: {hit['metadata']['source']} (청크 #{hit['metadata']['chunk_index']})")
        print(f"       {preview}")
        print()


# ── CLI ───────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="문서를 임베딩해서 JSON DB에 저장하고 유사도 검색 수행"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser("index", help="문서를 임베딩해서 DB에 저장")
    index_parser.add_argument("file", help="임베딩할 파일 경로 (MD, TXT, PDF)")

    search_parser = subparsers.add_parser("search", help="질문으로 유사한 청크 검색")
    search_parser.add_argument("query", help="검색할 질문")
    search_parser.add_argument("--top-k", type=int, default=3, help="반환할 결과 수 (기본값: 3)")

    args = parser.parse_args()

    if args.command == "index":
        if not os.path.exists(args.file):
            print(f"파일을 찾을 수 없습니다: {args.file}")
            return

        print(f"\n── 1. 문서 로딩 ──")
        text = load_document(args.file)

        print(f"\n── 2. 청킹 ──")
        chunks = split_text(text)

        print(f"\n── 3. 임베딩 ({EMBEDDING_MODEL}) ──")
        vectors = embed_texts(chunks)

        print(f"\n── 4. 벡터DB 저장 ──")
        source = os.path.basename(args.file)
        store_embeddings(chunks, vectors, source)

        print(f"\n완료! 이제 'python embedder.py search \"질문\"' 으로 검색하세요.\n")

    elif args.command == "search":
        print(f"\n── 질문 임베딩 및 검색 ({EMBEDDING_MODEL}) ──")
        print(f"  질문: {args.query}\n")
        hits = search(args.query, top_k=args.top_k)
        print_results(hits)


if __name__ == "__main__":
    main()
