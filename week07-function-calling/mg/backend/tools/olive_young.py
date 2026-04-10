"""올리브영 매장/상품/재고 검색 — daiso CLI (hmmhmmhm/daiso-mcp) 경유."""

import json
import subprocess
from tools.registry import register_tool


def _run_daiso_cli(*args: str) -> dict:
    """npx daiso CLI 실행. JSON 결과 반환."""
    try:
        # Windows: shell=True로 npx 호출 (경로 공백 문제 방지)
        cmd = "npx --yes daiso " + " ".join(args) + " --json"
        result = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8",
            timeout=30, shell=True,
        )
        # stdout에 JSON이 있으면 성공 (stderr의 assertion 경고 무시)
        stdout = result.stdout.strip()
        if stdout:
            try:
                return json.loads(stdout)
            except json.JSONDecodeError:
                pass
        if result.returncode != 0:
            return {"error": f"CLI 실패: {result.stderr[:200]}"}
        return {"raw": stdout[:500]}
    except subprocess.TimeoutExpired:
        return {"error": "CLI 타임아웃 (30초)"}
    except FileNotFoundError:
        return {"error": "npx를 찾을 수 없습니다. Node.js가 설치되어 있는지 확인하세요."}


@register_tool(
    name="oliveyoung_store_search",
    description="올리브영 매장을 지역명으로 검색합니다. 예: 강남, 명동, 홍대",
    parameters={
        "type": "object",
        "properties": {
            "keyword": {"type": "string", "description": "지역명 또는 매장명 (예: 명동, 강남역)"},
        },
        "required": ["keyword"],
    },
)
async def oliveyoung_store_search(keyword: str) -> dict:
    return _run_daiso_cli("get", "/api/oliveyoung/stores", "--keyword", keyword, "--limit", "5")


@register_tool(
    name="oliveyoung_product_search",
    description="올리브영 상품을 검색합니다. 예: 선크림, 토너, 마스크팩",
    parameters={
        "type": "object",
        "properties": {
            "keyword": {"type": "string", "description": "상품 키워드 (예: 선크림, 토너)"},
        },
        "required": ["keyword"],
    },
)
async def oliveyoung_product_search(keyword: str) -> dict:
    return _run_daiso_cli("get", "/api/oliveyoung/products", "--keyword", keyword, "--size", "5")


@register_tool(
    name="oliveyoung_inventory",
    description="올리브영 특정 매장의 상품 재고를 확인합니다. 상품 키워드와 매장 지역을 모두 입력하세요.",
    parameters={
        "type": "object",
        "properties": {
            "product_keyword": {"type": "string", "description": "상품 키워드 (예: 선크림)"},
            "store_keyword": {"type": "string", "description": "매장 지역 (예: 명동, 강남역)"},
        },
        "required": ["product_keyword", "store_keyword"],
    },
)
async def oliveyoung_inventory(product_keyword: str, store_keyword: str) -> dict:
    return _run_daiso_cli(
        "get", "/api/oliveyoung/inventory",
        "--keyword", product_keyword,
        "--storeKeyword", store_keyword,
        "--size", "5",
    )
