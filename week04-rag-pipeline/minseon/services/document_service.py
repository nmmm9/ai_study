"""
문서 서비스 - 파일 형식별 텍스트 추출

[관심사 분리 역할]
  이 파일: PDF / Markdown / TXT 파일을 텍스트로 변환
  chunking_service.py: 텍스트를 청크로 분할
  embedding_service.py: 텍스트를 벡터로 변환
  vector_store.py: 벡터 저장 및 검색
  llm_service.py: LLM 스트리밍 호출
"""

import os


def load_document(file_path: str) -> str:
    """파일 확장자에 따라 텍스트 추출 (md / txt / pdf)"""
    ext = os.path.splitext(file_path)[1].lower()

    if ext in (".md", ".markdown", ".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    elif ext == ".pdf":
        import fitz
        doc = fitz.open(file_path)
        return "\n\n".join(page.get_text() for page in doc)

    raise ValueError(f"지원하지 않는 파일 형식: {ext}")
