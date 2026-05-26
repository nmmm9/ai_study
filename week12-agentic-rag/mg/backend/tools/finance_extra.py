"""금융 확장 — DART 전자공시 / 대신증권 리포트.

- DART: opendart.fss.or.kr (API_K_DART env required)
- 대신증권: GitHub Pages mirror (no auth)
"""

import os
import httpx
from tools.registry import register_tool

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
DART_BASE = "https://opendart.fss.or.kr/api"


def _dart_key() -> str | None:
    return os.environ.get("API_K_DART")


@register_tool(
    name="k_dart_search_disclosure",
    description="DART 전자공시 검색 — 기업 공시 보고서를 회사명/회사코드/기간으로 조회합니다. API_K_DART 환경변수 필요.",
    parameters={
        "type": "object",
        "properties": {
            "corp_code": {"type": "string", "description": "고유 회사코드 8자리 (선택)"},
            "corp_name": {"type": "string", "description": "회사명 (corp_code 없을 때)"},
            "bgn_de": {"type": "string", "description": "검색시작일 YYYYMMDD"},
            "end_de": {"type": "string", "description": "검색종료일 YYYYMMDD"},
            "page_count": {"type": "integer", "default": 10},
        },
    },
)
async def k_dart_search_disclosure(corp_code: str | None = None,
                                    corp_name: str | None = None,
                                    bgn_de: str | None = None,
                                    end_de: str | None = None,
                                    page_count: int = 10) -> dict:
    key = _dart_key()
    if not key:
        return {"error": "API_K_DART 환경변수가 필요합니다 (https://opendart.fss.or.kr)"}

    params: dict = {"crtfc_key": key, "page_count": page_count}
    if corp_code:
        params["corp_code"] = corp_code
    if bgn_de:
        params["bgn_de"] = bgn_de
    if end_de:
        params["end_de"] = end_de

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{DART_BASE}/list.json", params=params)
        if resp.status_code == 200:
            data = resp.json()
            if corp_name and not corp_code:
                # 회사명 클라이언트 사이드 필터링
                items = data.get("list", [])
                items = [i for i in items if corp_name in (i.get("corp_name") or "")]
                data["list"] = items[:page_count]
            return data
        return {"error": f"DART 조회 실패 (status {resp.status_code})"}


@register_tool(
    name="k_dart_company_info",
    description="DART 기업 개황(회사명, 대표자, 주소 등)을 조회합니다. corp_code 8자리 필요.",
    parameters={
        "type": "object",
        "properties": {
            "corp_code": {"type": "string", "description": "고유 회사코드 8자리"},
        },
        "required": ["corp_code"],
    },
)
async def k_dart_company_info(corp_code: str) -> dict:
    key = _dart_key()
    if not key:
        return {"error": "API_K_DART 환경변수가 필요합니다"}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{DART_BASE}/company.json",
                                params={"crtfc_key": key, "corp_code": corp_code})
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"DART 기업개황 조회 실패 (status {resp.status_code})"}


@register_tool(
    name="k_dart_financial",
    description="DART 재무제표(단일회사 주요계정)를 조회합니다.",
    parameters={
        "type": "object",
        "properties": {
            "corp_code": {"type": "string", "description": "회사코드 8자리"},
            "bsns_year": {"type": "string", "description": "사업연도 YYYY"},
            "reprt_code": {"type": "string", "description": "보고서코드 (11011=사업보고서)",
                            "default": "11011"},
        },
        "required": ["corp_code", "bsns_year"],
    },
)
async def k_dart_financial(corp_code: str, bsns_year: str,
                            reprt_code: str = "11011") -> dict:
    key = _dart_key()
    if not key:
        return {"error": "API_K_DART 환경변수가 필요합니다"}
    params = {
        "crtfc_key": key,
        "corp_code": corp_code,
        "bsns_year": bsns_year,
        "reprt_code": reprt_code,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{DART_BASE}/fnlttSinglAcnt.json", params=params)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"DART 재무제표 조회 실패 (status {resp.status_code})"}


# ─────────────────────────────────────
# 대신증권 리포트 — GitHub Pages mirror
# ─────────────────────────────────────

DAISHIN_REPO_TREE = "https://api.github.com/repos/jay-jo-0/github_pages_repo/git/trees/main?recursive=1"
DAISHIN_RAW = "https://raw.githubusercontent.com/Jay-jo-0/github_pages_repo/main"


@register_tool(
    name="daishin_report_search",
    description="대신증권 리포트 미러에서 최신 리포트 목록을 조회합니다. (GitHub Pages mirror)",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "리포트 제목/파일명 필터 (선택)"},
            "limit": {"type": "integer", "default": 20},
        },
    },
)
async def daishin_report_search(query: str | None = None, limit: int = 20) -> dict:
    async with httpx.AsyncClient(timeout=20, headers={"User-Agent": UA}) as client:
        resp = await client.get(DAISHIN_REPO_TREE)
        if resp.status_code != 200:
            return {"error": f"리포트 목록 조회 실패 (status {resp.status_code})"}
        data = resp.json()
        files = []
        for item in data.get("tree", []):
            path = item.get("path", "")
            if item.get("type") != "blob":
                continue
            if not (path.endswith(".html") or path.endswith(".pdf")):
                continue
            if query and query.lower() not in path.lower():
                continue
            files.append({
                "path": path,
                "raw_url": f"{DAISHIN_RAW}/{path}",
                "browser_url": f"https://jay-jo-0.github.io/github_pages_repo/{path}",
            })
            if len(files) >= limit:
                break
        return {"query": query, "count": len(files), "reports": files}
