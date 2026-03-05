"""
청킹 서비스 - 텍스트를 의미 단위로 분할

[관심사 분리 역할]
  이 파일: Recursive Character Splitting (2주차와 동일한 방식)
  document_service.py: 파일 로딩
  embedding_service.py: 벡터 변환
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter

CHUNK_SIZE = 800
CHUNK_OVERLAP = 80


def split_text(text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> list[str]:
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
