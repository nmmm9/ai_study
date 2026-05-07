"""LH 청약 공고 상세 — k-skill-proxy."""

import httpx
from tools.registry import register_tool

PROXY = "https://k-skill-proxy.nomadamas.org"


@register_tool(
    name="lh_notice_detail",
    description="LH 청약 공고의 상세 내용(자격, 일정, 공급세대수)을 조회합니다.",
    parameters={
        "type": "object",
        "properties": {
            "panId": {"type": "string", "description": "공고 ID"},
            "csCd": {"type": "string", "description": "공고 분류 코드"},
        },
        "required": ["panId"],
    },
)
async def lh_notice_detail(panId: str, csCd: str | None = None) -> dict:
    params = {"panId": panId}
    if csCd:
        params["csCd"] = csCd
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{PROXY}/v1/lh-notice/detail", params=params)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"LH 공고 상세 조회 실패 (status {resp.status_code})"}
