"""한국어 맞춤법 검사 — 나라 맞춤법 검사기 (구 부산대 맞춤법/문법 검사기).

k-skills 원본: https://nara-speller.co.kr/old_speller/results POST.
브라우저형 User-Agent + urllib POST가 가장 안정적이지만,
여기서는 httpx로 호출하되 브라우저 User-Agent를 사용한다.
결과는 HTML이므로 교정 결과를 파싱해서 원문/교정안/이유를 추출한다.
"""

import re
import httpx
from tools.registry import register_tool


@register_tool(
    name="korean_spell_check",
    description="한국어 맞춤법과 문법을 검사합니다. 텍스트를 입력하면 교정 제안을 반환합니다.",
    parameters={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "검사할 한국어 텍스트"},
        },
        "required": ["text"],
    },
)
async def korean_spell_check(text: str) -> dict:
    # 긴 텍스트는 1500자 이내로 제한 (k-skills 원본 정책)
    chunk = text[:1500]

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            "https://nara-speller.co.kr/old_speller/results",
            data={"text": chunk},
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            },
        )
        if resp.status_code != 200:
            return {"error": f"맞춤법 검사 실패 (status {resp.status_code})"}

        html = resp.text
        corrections = []

        # 교정 결과 파싱: 대체 교정(span class에 따라 다름)
        # 일반적인 패턴: <span class='re_*'>원문</span> → 교정안
        # 또는 JavaScript data에서 추출
        # data-org="원문" data-fix="교정안" data-help="설명"
        org_matches = re.findall(r'data-org="([^"]*)"', html)
        fix_matches = re.findall(r'data-fix="([^"]*)"', html)
        help_matches = re.findall(r'data-help="([^"]*)"', html)

        if org_matches and fix_matches:
            for i in range(min(len(org_matches), len(fix_matches))):
                correction = {
                    "original": org_matches[i],
                    "suggestion": fix_matches[i],
                }
                if i < len(help_matches) and help_matches[i]:
                    correction["reason"] = re.sub(r"<[^>]+>", "", help_matches[i]).strip()
                corrections.append(correction)
        else:
            # Fallback: span class='re_*' 패턴에서 추출
            span_matches = re.findall(r"<span class='(re_[^']*)'[^>]*>(.*?)</span>", html)
            for cls, content in span_matches:
                clean = re.sub(r"<[^>]+>", "", content).strip()
                if clean:
                    corrections.append({
                        "original": clean,
                        "type": cls,
                    })

        return {
            "original": text[:200],
            "corrections": corrections,
            "correction_count": len(corrections),
            "message": "맞춤법 검사 완료" if corrections else "교정 사항이 없거나 파싱 결과가 없습니다",
        }
