"""한국어 글자수 세기 — 공시/원고지 규격 기준."""

import re
from tools.registry import register_tool


def _count_basic(text: str) -> dict:
    no_space = re.sub(r"\s", "", text)
    chars = len(text)
    chars_no_space = len(no_space)
    bytes_utf8 = len(text.encode("utf-8"))
    # Korean char counts as 2 bytes in EUC-KR; many apps use this for limits
    bytes_eucr = sum(2 if ord(c) > 127 else 1 for c in text)
    words = len(re.findall(r"\S+", text))
    lines = text.count("\n") + 1 if text else 0
    # 원고지 (200자 1매)
    manuscript_pages = (chars + 199) // 200 if chars else 0
    return {
        "chars": chars,
        "chars_no_space": chars_no_space,
        "bytes_utf8": bytes_utf8,
        "bytes_eucr": bytes_eucr,
        "words": words,
        "lines": lines,
        "manuscript_pages_200": manuscript_pages,
    }


@register_tool(
    name="korean_character_count",
    description="한국어 텍스트의 글자수, 공백 제외 글자수, 바이트수, 단어수, 원고지 매수를 계산합니다.",
    parameters={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "분석할 텍스트"},
        },
        "required": ["text"],
    },
)
async def korean_character_count(text: str) -> dict:
    return _count_basic(text)
