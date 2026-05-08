"""
문서 로더 서비스 - 파일 형식별 텍스트 추출

[관심사 분리 역할]
  이 파일: PDF / Markdown / TXT 파일을 텍스트로 변환
  chunker.py (서비스): 텍스트를 청크로 분할
  chunker.py (CLI):    결과 출력 및 커맨드라인 인터페이스
"""

import os

import fitz  # pymupdf


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
