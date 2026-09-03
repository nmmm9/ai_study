"""
ocr_tool.py — 이미지/PDF OCR 분석 (Feature 6)

GPT-4o Vision API로 이미지를 읽어 정책 정보 추출.
PDF는 첫 페이지를 이미지로 변환 후 처리.
"""

import base64
import io
from pathlib import Path
from openai import OpenAI

_client = OpenAI()

_SYSTEM = """\
당신은 청년정책 공고문 분석 전문가입니다.
제공된 이미지(포스터, 공고문, 스캔본)에서 아래 항목을 추출하세요.

## 추출 항목
1. **정책명/사업명**
2. **지원 대상** (나이, 자격 조건)
3. **지원 내용** (금액, 기간, 혜택)
4. **신청 기간** (시작일 ~ 마감일)
5. **신청 방법** (온라인/방문/서류)
6. **필요 서류**
7. **문의처** (전화, 사이트)

## 출력 형식
### [정책명]

**지원 대상**: ...
**지원 내용**: ...
**신청 기간**: ...
**신청 방법**: ...
**필요 서류**: ...
**문의처**: ...

텍스트가 잘 보이지 않거나 정책 공고가 아닌 경우 솔직하게 알려주세요.
"""


def analyze_image_bytes(image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """
    이미지 바이트 → GPT-4o Vision으로 정책 정보 추출.
    mime_type: "image/jpeg", "image/png", "image/webp", "image/gif"
    """
    b64 = base64.b64encode(image_bytes).decode()
    data_url = f"data:{mime_type};base64,{b64}"

    resp = _client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": _SYSTEM},
            {
                "role": "user",
                "content": [
                    {"type": "text",      "text": "이 공고문에서 정책 정보를 추출해주세요."},
                    {"type": "image_url", "image_url": {"url": data_url, "detail": "high"}},
                ],
            },
        ],
        max_tokens=1500,
    )
    return resp.choices[0].message.content or "분석 결과를 가져오지 못했습니다."


def analyze_pdf_bytes(pdf_bytes: bytes) -> str:
    """PDF → 첫 페이지 이미지 변환 후 OCR."""
    try:
        import fitz  # PyMuPDF
        doc  = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc[0]
        mat  = fitz.Matrix(2, 2)   # 2x 해상도
        pix  = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        doc.close()
        return analyze_image_bytes(img_bytes, mime_type="image/png")
    except ImportError:
        return "PDF 분석을 위해 'pip install pymupdf'가 필요합니다."
    except Exception as e:
        return f"PDF 분석 중 오류: {e}"


def analyze_file(file_bytes: bytes, filename: str) -> str:
    """파일 확장자에 따라 자동 분기."""
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return analyze_pdf_bytes(file_bytes)
    mime_map = {
        ".jpg":  "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png":  "image/png",
        ".webp": "image/webp",
        ".gif":  "image/gif",
    }
    mime = mime_map.get(ext, "image/jpeg")
    return analyze_image_bytes(file_bytes, mime)
