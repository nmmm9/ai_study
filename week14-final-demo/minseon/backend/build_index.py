"""
build_index.py — 정책 문서 임베딩 후 ChromaDB에 저장 (1회 실행)

실행 방법:
  cd week14-final-demo/minseon
  python -m backend.build_index

database/chroma_db/ 폴더가 생성됩니다.
이미 인덱스가 있으면 스킵합니다. 재빌드하려면 chroma_db 폴더를 삭제하세요.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import settings  # noqa: F401  (.env를 여기서 한 번 로드)
from backend.logging_config import get_logger
from backend.tools.policy_loader import _load_all_docs
from backend.modules.embedder import embed_texts
from backend.modules.vector_store import add_documents, count, is_built

logger = get_logger(__name__)

BATCH_SIZE = 50


def build_index():
    if is_built():
        logger.info(f"이미 인덱스 존재 ({count()}개). 재빌드하려면 database/chroma_db 폴더를 삭제하세요.")
        return

    logger.info("문서 로드 중...")
    docs = _load_all_docs()
    logger.info(f"총 {len(docs)}개 문서 로드 완료\n")

    total = len(docs)
    for i in range(0, total, BATCH_SIZE):
        batch = docs[i:i + BATCH_SIZE]

        texts = [f"{d['title']}\n{d['content'][:800]}" for d in batch]
        embeddings = embed_texts(texts)

        add_documents(
            ids=[f"doc_{i + j}" for j in range(len(batch))],
            embeddings=embeddings,
            documents=[d["content"][:1500] for d in batch],
            metadatas=[{"title": d["title"], "category": d["category"]} for d in batch],
        )

        done = min(i + BATCH_SIZE, total)
        logger.info(f"  {done}/{total} 완료")
        time.sleep(0.3)

    logger.info(f"\n인덱스 빌드 완료! 총 {count()}개 저장됨")
    logger.info("저장 위치: database/chroma_db/")


if __name__ == "__main__":
    build_index()
