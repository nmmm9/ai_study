"""
3주차 과제: Embedding & Vector DB - 문서 임베딩 및 유사도 검색
OpenAI 임베딩 + ChromaDB로 구성하는 RAG 파이프라인
"""

import argparse
import os

from dotenv import load_dotenv
from openai import OpenAI
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

client = OpenAI()

# ── 설정 ──────────────────────────────────────────────
EMBEDDING_MODEL = "text-embedding-3-small"
CHUNK_SIZE = 900
CHUNK_OVERLAP = 90
COLLECTION_NAME = "minseon_docs"


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


# ── Vector DB (ChromaDB) ───────────────────────────────

def get_collection(db_path: str = "./chroma_db") -> chromadb.Collection:
    """ChromaDB 클라이언트 및 컬렉션 반환 (없으면 생성)"""
    chroma_client = chromadb.PersistentClient(path=db_path)
    collection = chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},  # 코사인 유사도 사용
    )
    return collection


def store_embeddings(
    collection: chromadb.Collection,
    chunks: list[str],
    vectors: list[list[float]],
    source: str,
) -> None:
    """청크와 벡터를 ChromaDB에 저장"""
    ids = [f"{source}_{i}" for i in range(len(chunks))]

    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=vectors,
        metadatas=[{"source": source, "chunk_index": i} for i in range(len(chunks))],
    )
    print(f"  벡터DB 저장 완료: {len(chunks)}개 → '{COLLECTION_NAME}' 컬렉션")


def search(
    collection: chromadb.Collection,
    query: str,
    top_k: int = 3,
) -> list[dict]:
    """
    사용자 질문을 임베딩 후 코사인 유사도로 가장 유사한 청크 검색

    1. 질문 텍스트 → 임베딩 벡터
    2. ChromaDB에서 유사도 높은 top_k개 청크 반환
    """
    query_vector = embed_texts([query])[0]

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "distances", "metadatas"],
    )

    hits = []
    for i in range(len(results["documents"][0])):
        hits.append({
            "content": results["documents"][0][i],
            "distance": results["distances"][0][i],
            "metadata": results["metadatas"][0][i],
        })
    return hits


# ── 결과 출력 ─────────────────────────────────────────

def print_results(hits: list[dict], preview_length: int = 150) -> None:
    """검색 결과 출력"""
    print(f"\n{'='*60}")
    print(f"  검색 결과: {len(hits)}개")
    print(f"{'='*60}\n")

    for i, hit in enumerate(hits):
        similarity = 1 - hit["distance"]  # 코사인 거리 → 유사도
        preview = hit["content"][:preview_length].replace("\n", " ")
        if len(hit["content"]) > preview_length:
            preview += "..."

        print(f"  [{i+1}] 유사도: {similarity:.4f} | 출처: {hit['metadata']['source']} (청크 #{hit['metadata']['chunk_index']})")
        print(f"       {preview}")
        print()


# ── CLI ───────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="문서를 임베딩해서 ChromaDB에 저장하고 유사도 검색 수행"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # index 명령: 문서 → 임베딩 → 저장
    index_parser = subparsers.add_parser("index", help="문서를 임베딩해서 DB에 저장")
    index_parser.add_argument("file", help="임베딩할 파일 경로 (MD, TXT, PDF)")

    # search 명령: 질문 → 검색
    search_parser = subparsers.add_parser("search", help="질문으로 유사한 청크 검색")
    search_parser.add_argument("query", help="검색할 질문")
    search_parser.add_argument("--top-k", type=int, default=3, help="반환할 결과 수 (기본값: 3)")

    args = parser.parse_args()
    collection = get_collection()

    if args.command == "index":
        if not os.path.exists(args.file):
            print(f"파일을 찾을 수 없습니다: {args.file}")
            return

        print(f"\n── 1. 문서 로딩 ──")
        text = load_document(args.file)

        print(f"\n── 2. 청킹 ──")
        chunks = split_text(text)

        print(f"\n── 3. 임베딩 ──")
        vectors = embed_texts(chunks)

        print(f"\n── 4. 벡터DB 저장 ──")
        source = os.path.basename(args.file)
        store_embeddings(collection, chunks, vectors, source)

        print(f"\n완료! 이제 'python embedder.py search \"질문\"' 으로 검색하세요.\n")

    elif args.command == "search":
        print(f"\n── 질문 임베딩 및 검색 ──")
        print(f"  질문: {args.query}\n")
        hits = search(collection, args.query, top_k=args.top_k)
        print_results(hits)


if __name__ == "__main__":
    main()
