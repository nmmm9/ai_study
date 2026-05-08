"""
청킹 서비스 - 텍스트를 의미 단위로 분할

[관심사 분리 역할]
  이 파일: Recursive Character Splitting, Markdown 헤더 기반 분할 로직
  document_loader.py: 파일 형식별 텍스트 추출
  chunker.py (CLI):   결과 출력 및 커맨드라인 인터페이스
"""

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)


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
    return splitter.split_text(text)


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
