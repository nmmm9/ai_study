"""
attachment_parser.py — 공고문 첨부파일(PDF/HWPX) 구조화 파싱

LH·HUG 등 공공기관 공고는 상세 조건(평형, 임대보증금, 월임대료 등)이
공고 URL 페이지가 아니라 첨부된 PDF/HWP 파일 안에만 있는 경우가 많다.
이 모듈은 그 첨부파일을 다운로드해 텍스트·표를 추출한다.

지원 형식:
  - PDF: pdfplumber로 텍스트 + 표(table)를 마크다운으로 변환
  - HWPX: 최신 한글 문서는 zip+XML 구조라 pyhwp 없이 zipfile로 직접 파싱 가능
  - 구버전 HWP(바이너리): 미지원 — 필요 시 pyhwp 별도 설치 필요(본 프로젝트에서는 다루지 않음)
"""

import io
import re
import zipfile
import xml.etree.ElementTree as ET

import requests

from backend.logging_config import get_logger

logger = get_logger(__name__)

_MAX_ATTACHMENT_BYTES = 15 * 1024 * 1024  # 15MB
_TIMEOUT = 15


def _table_to_markdown(table: list[list[str | None]]) -> str:
    rows = [[(c or "").strip().replace("\n", " ") for c in row] for row in table]
    if not rows:
        return ""
    header = rows[0]
    lines = ["| " + " | ".join(header) + " |",
             "|" + "|".join(["---"] * len(header)) + "|"]
    for row in rows[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def parse_pdf_bytes(pdf_bytes: bytes, max_pages: int = 10) -> str:
    """PDF 바이트에서 텍스트 + 표를 마크다운 텍스트로 추출."""
    import pdfplumber

    parts = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for i, page in enumerate(pdf.pages[:max_pages]):
            text = (page.extract_text() or "").strip()
            if text:
                parts.append(text)
            for table in page.extract_tables():
                md = _table_to_markdown(table)
                if md:
                    parts.append(md)
    return "\n\n".join(parts).strip()


_HWPX_NS = {"hp": "http://www.hancom.co.kr/hwpml/2011/paragraph"}


def parse_hwpx_bytes(hwpx_bytes: bytes) -> str:
    """
    HWPX(최신 한글 문서, zip+XML 구조)에서 본문 텍스트를 추출.
    Contents/section0.xml ... 등 여러 섹션 파일에 <hp:t> 텍스트 노드가 들어있다.
    """
    texts = []
    with zipfile.ZipFile(io.BytesIO(hwpx_bytes)) as z:
        section_files = sorted(
            n for n in z.namelist()
            if re.match(r"Contents/section\d+\.xml$", n)
        )
        for name in section_files:
            try:
                root = ET.fromstring(z.read(name))
            except ET.ParseError:
                continue
            for t in root.iter():
                if t.tag.endswith("}t") and t.text:
                    texts.append(t.text.strip())
    return "\n".join(t for t in texts if t)


def _sniff_kind(url: str, content_type: str, head_bytes: bytes) -> str | None:
    lower = url.lower()
    if lower.endswith(".pdf") or "pdf" in content_type:
        return "pdf"
    if lower.endswith(".hwpx"):
        return "hwpx"
    if lower.endswith(".hwp"):
        return "hwp"
    if head_bytes[:4] == b"%PDF":
        return "pdf"
    if head_bytes[:2] == b"PK":  # zip 기반 = hwpx 가능성
        return "hwpx"
    return None


def fetch_and_parse_attachment(url: str) -> str | None:
    """
    URL에서 첨부파일을 내려받아 텍스트로 변환. 실패하거나 지원하지 않는
    형식이면 None을 반환한다 (호출부는 이를 '본문 링크만 안내'로 폴백해야 함).
    """
    if not url or not url.startswith(("http://", "https://")):
        return None

    try:
        resp = requests.get(url, timeout=_TIMEOUT, stream=True)
        resp.raise_for_status()
        content = resp.raw.read(_MAX_ATTACHMENT_BYTES + 1, decode_content=True)
        if len(content) > _MAX_ATTACHMENT_BYTES:
            logger.warning(f"[attachment_parser] 파일 용량 초과로 건너뜀: {url}")
            return None
    except Exception as e:
        logger.error(f"[attachment_parser] 다운로드 실패: {url} ({e})")
        return None

    kind = _sniff_kind(url, resp.headers.get("Content-Type", ""), content[:8])
    if kind is None:
        return None

    try:
        if kind == "pdf":
            return parse_pdf_bytes(content) or None
        if kind == "hwpx":
            return parse_hwpx_bytes(content) or None
        logger.warning(f"[attachment_parser] 미지원 형식(hwp 구버전): {url}")
        return None
    except Exception as e:
        logger.error(f"[attachment_parser] 파싱 실패: {url} ({e})")
        return None
