"""쿠팡 상품 검색 — coupang-mcp HuggingFace proxy.

k-skills 원본: MCP Streamable HTTP (JSON-RPC) 프로토콜.
먼저 initialize로 세션 ID를 얻고, 그 세션 ID로 tools/call을 호출한다.
응답은 SSE (text/event-stream) 형태일 수 있다.
"""

import httpx
import json as json_module
from tools.registry import register_tool

MCP_URL = "https://yuju777-coupang-mcp.hf.space/mcp"
MCP_HEADERS = {
    "content-type": "application/json",
    "accept": "application/json, text/event-stream",
}


@register_tool(
    name="coupang_search",
    description="쿠팡에서 상품을 검색합니다. 키워드, 최소/최대 가격으로 필터링 가능합니다.",
    parameters={
        "type": "object",
        "properties": {
            "keyword": {"type": "string", "description": "검색할 상품명"},
            "min_price": {"type": "integer", "description": "최소 가격 (원)", "default": 0},
            "max_price": {"type": "integer", "description": "최대 가격 (원, 0이면 제한없음)", "default": 0},
        },
        "required": ["keyword"],
    },
)
async def coupang_search(keyword: str, min_price: int = 0, max_price: int = 0) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            # Step 1: MCP initialize → get session ID
            init_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "k-skill", "version": "1.0"},
                },
            }
            init_resp = await client.post(MCP_URL, json=init_payload, headers=MCP_HEADERS)
            session_id = init_resp.headers.get("mcp-session-id", "")

            # Step 2: tools/call with session ID
            call_headers = {**MCP_HEADERS}
            if session_id:
                call_headers["mcp-session-id"] = session_id

            call_payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "search_coupang_products",
                    "arguments": {
                        "keyword": keyword,
                        "min_price": min_price,
                        "max_price": max_price,
                        "limit": 5,
                    },
                },
            }

            resp = await client.post(MCP_URL, json=call_payload, headers=call_headers)
            if resp.status_code != 200:
                return {"error": f"쿠팡 검색 실패 (status {resp.status_code})"}

            # 응답이 SSE일 수 있음
            content_type = resp.headers.get("content-type", "")
            if "text/event-stream" in content_type:
                # SSE 파싱: data: 줄에서 JSON 추출
                for line in resp.text.split("\n"):
                    if line.startswith("data:"):
                        try:
                            data = json_module.loads(line[5:].strip())
                            return _parse_mcp_result(data, keyword)
                        except Exception:
                            continue
                return {"keyword": keyword, "raw": resp.text[:500]}
            else:
                data = resp.json()
                return _parse_mcp_result(data, keyword)

        except Exception as e:
            return {"error": f"쿠팡 검색 오류: {str(e)}"}


def _parse_mcp_result(data: dict, keyword: str) -> dict:
    """MCP JSON-RPC 응답에서 상품 목록 추출."""
    result = data.get("result", {})
    content = result.get("content", [])

    if content and isinstance(content, list):
        text = content[0].get("text", "")
        try:
            products = json_module.loads(text)
            if isinstance(products, list):
                return {"keyword": keyword, "count": len(products), "products": products[:5]}
        except Exception:
            return {"keyword": keyword, "raw": text[:500]}

    return {"keyword": keyword, "data": data}
