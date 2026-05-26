"""국세청 사업자등록 — 진위확인 및 상태조회 via k-skill-proxy."""

import httpx
from tools.registry import register_tool

PROXY = "https://k-skill-proxy.nomadamas.org"


@register_tool(
    name="nts_business_status",
    description="사업자등록번호로 사업자 상태(계속/휴업/폐업)를 조회합니다.",
    parameters={
        "type": "object",
        "properties": {
            "b_no": {
                "type": "array",
                "items": {"type": "string"},
                "description": "사업자등록번호 목록 (10자리 숫자, 하이픈 제외). 최대 100개"
            },
        },
        "required": ["b_no"],
    },
)
async def nts_business_status(b_no: list[str]) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{PROXY}/v1/nts-business/status",
            json={"b_no": b_no},
        )
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"사업자등록 상태 조회 실패 (status {resp.status_code})", "body": resp.text[:300]}


@register_tool(
    name="nts_business_validate",
    description="사업자등록번호의 진위 여부와 정보(상호, 대표자, 개업일자 등)를 확인합니다.",
    parameters={
        "type": "object",
        "properties": {
            "b_no": {"type": "string", "description": "사업자등록번호 (10자리)"},
            "start_dt": {"type": "string", "description": "개업일자 YYYYMMDD"},
            "p_nm": {"type": "string", "description": "대표자 성명"},
            "b_nm": {"type": "string", "description": "상호 (선택)"},
        },
        "required": ["b_no", "start_dt", "p_nm"],
    },
)
async def nts_business_validate(b_no: str, start_dt: str, p_nm: str,
                                 b_nm: str | None = None) -> dict:
    businesses = {
        "b_no": b_no,
        "start_dt": start_dt,
        "p_nm": p_nm,
    }
    if b_nm:
        businesses["b_nm"] = b_nm
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{PROXY}/v1/nts-business/validate",
            json={"businesses": [businesses]},
        )
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"사업자등록 진위확인 실패 (status {resp.status_code})", "body": resp.text[:300]}
