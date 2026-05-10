from pathlib import Path
import json
import re


CHUNKS_PATH = Path("output/chunks.json")


def load_chunks() -> list[dict]:
    if not CHUNKS_PATH.exists():
        raise FileNotFoundError(
            "output/chunks.json 파일이 없습니다. 먼저 main.py를 실행해서 chunk를 생성하세요."
        )

    return json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))


def tokenize(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r"[^가-힣a-zA-Z0-9\s]", " ", text)
    words = text.split()

    return [word for word in words if len(word) >= 2]


def score_chunk(query: str, chunk_text: str) -> int:
    query_words = tokenize(query)
    chunk_text_lower = chunk_text.lower()

    score = 0

    for word in query_words:
        if word in chunk_text_lower:
            score += 1

    return score


def retrieve_relevant_chunks(query: str, top_k: int = 3) -> list[dict]:
    chunks = load_chunks()

    scored_chunks = []

    for chunk in chunks:
        score = score_chunk(query, chunk["text"])

        if score > 0:
            scored_chunks.append({
                "score": score,
                "text": chunk["text"],
                "metadata": chunk["metadata"],
            })

    scored_chunks.sort(key=lambda x: x["score"], reverse=True)

    return scored_chunks[:top_k]


if __name__ == "__main__":
    query = input("질문을 입력하세요: ")

    results = retrieve_relevant_chunks(query, top_k=3)

    print(f"\n검색 결과: {len(results)}개")
    print("=" * 50)

    for result in results:
        metadata = result["metadata"]

        print(f"score: {result['score']}")
        print(f"source: {metadata.get('source')}")
        print(f"type: {metadata.get('document_type')}")

        if "page" in metadata:
            print(f"page: {metadata.get('page')}")

        if "section" in metadata:
            print(f"section: {metadata.get('section')}")

        print()
        print(result["text"])
        print("-" * 50)