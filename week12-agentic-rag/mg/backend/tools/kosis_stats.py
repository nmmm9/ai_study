"""KOSIS 국가통계포털 — 통계표 검색/메타/데이터 조회."""

import httpx
from tools.registry import register_tool

PROXY = "https://k-skill-proxy.nomadamas.org"


@register_tool(
    name="kosis_search",
    description="KOSIS 국가통계포털에서 통계표를 키워드로 검색합니다. 통계표 ID(orgId, tblId)를 얻기 위한 첫 단계.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "통계표 검색 키워드 (예: '인구', '실업률')"},
            "limit": {"type": "integer", "default": 10},
        },
        "required": ["query"],
    },
)
async def kosis_search(query: str, limit: int = 10) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{PROXY}/v1/kosis/search",
            params={"q": query, "limit": limit},
        )
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"KOSIS 검색 실패 (status {resp.status_code})", "body": resp.text[:300]}


@register_tool(
    name="kosis_meta",
    description="KOSIS 통계표의 메타 정보(분류 항목, 시점 등)를 조회합니다.",
    parameters={
        "type": "object",
        "properties": {
            "orgId": {"type": "string", "description": "통계기관 ID"},
            "tblId": {"type": "string", "description": "통계표 ID"},
        },
        "required": ["orgId", "tblId"],
    },
)
async def kosis_meta(orgId: str, tblId: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{PROXY}/v1/kosis/meta",
            params={"orgId": orgId, "tblId": tblId},
        )
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"KOSIS 메타 조회 실패 (status {resp.status_code})", "body": resp.text[:300]}


@register_tool(
    name="kosis_data",
    description="KOSIS 통계표의 실제 데이터(시점별 수치)를 조회합니다. orgId, tblId 필수.",
    parameters={
        "type": "object",
        "properties": {
            "orgId": {"type": "string", "description": "통계기관 ID"},
            "tblId": {"type": "string", "description": "통계표 ID"},
            "prdSe": {"type": "string", "description": "시점 (Y=연간, Q=분기, M=월간)"},
            "newEstPrdCnt": {"type": "integer", "description": "최근 몇 개 시점", "default": 5},
        },
        "required": ["orgId", "tblId"],
    },
)
async def kosis_data(orgId: str, tblId: str, prdSe: str | None = None,
                     newEstPrdCnt: int = 5) -> dict:
    params: dict = {"orgId": orgId, "tblId": tblId, "newEstPrdCnt": newEstPrdCnt}
    if prdSe:
        params["prdSe"] = prdSe
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(f"{PROXY}/v1/kosis/data", params=params)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"KOSIS 데이터 조회 실패 (status {resp.status_code})", "body": resp.text[:300]}
