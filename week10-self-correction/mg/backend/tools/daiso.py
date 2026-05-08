"""다이소 상품/매장/재고 검색 — daisomall.co.kr API (k-skill 원본 참조)."""

import httpx
from tools.registry import register_tool

BROWSER_HEADERS = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "accept": "application/json, text/plain, */*",
    "accept-language": "ko,en-US;q=0.9,en;q=0.8",
}
BASE_API = "https://www.daisomall.co.kr/api"
BASE_SEARCH = "https://www.daisomall.co.kr/ssn/search"


@register_tool(
    name="daiso_search",
    description="다이소 매장과 상품을 검색합니다. 매장 검색, 상품 검색이 가능합니다.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "검색할 상품명 또는 매장 위치"},
            "search_type": {"type": "string", "enum": ["product", "store"], "description": "product=상품검색, store=매장검색", "default": "product"},
        },
        "required": ["query"],
    },
)
async def daiso_search(query: str, search_type: str = "product") -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        if search_type == "store":
            resp = await client.post(
                f"{BASE_API}/ms/msg/selStr",
                json={"keyword": query, "pkupYn": "", "pageSize": 10, "currentPage": 1},
                headers={**BROWSER_HEADERS, "content-type": "application/json"},
            )
            if resp.status_code != 200:
                return {"error": "매장 검색 실패"}
            try:
                data = resp.json()
                stores = data.get("data", [])
                if not isinstance(stores, list):
                    stores = data.get("list", [])
                results = []
                for s in (stores if isinstance(stores, list) else [])[:5]:
                    addr_parts = [s.get("strAddr", ""), s.get("strDtlAddr", "")]
                    results.append({
                        "name": s.get("strNm", ""),
                        "address": " ".join(p for p in addr_parts if p),
                        "code": s.get("strCd", ""),
                        "phone": s.get("strTno", ""),
                        "pickupAvailable": s.get("pkupYn", "") == "Y",
                    })
                return {"query": query, "type": "store", "count": len(results), "stores": results}
            except Exception:
                return {"error": "매장 파싱 실패"}
        else:
            resp = await client.get(
                f"{BASE_SEARCH}/SearchGoods",
                params={
                    "searchTerm": query, "searchQuery": "", "pageNum": "1",
                    "cntPerPage": "10", "brndCd": "", "userId": "",
                    "newPdYn": "", "massOrPsblYn": "", "pkupOrPsblYn": "", "fdrmOrPsblYn": "",
                },
                headers=BROWSER_HEADERS,
            )
            if resp.status_code != 200:
                return {"error": "상품 검색 실패"}
            try:
                data = resp.json()
                result_list = data.get("resultSet", {}).get("result", [])
                documents = []
                for r in result_list:
                    docs = r.get("resultDocuments", [])
                    if docs:
                        documents = docs
                        break

                if not documents:
                    return {"query": query, "type": "product", "count": 0, "products": [], "message": "검색 결과 없음"}

                products = []
                for doc in documents[:10]:
                    products.append({
                        "name": doc.get("exhPdNm", doc.get("pdNm", "")),
                        "price": doc.get("pdPrc", doc.get("sellPrc", "")),
                        "pdNo": doc.get("pdNo", ""),
                        "onldPdNo": doc.get("onldPdNo", doc.get("onlPdNo", "")),
                        "category": doc.get("exhSmallCtgrNm", doc.get("exhCtgrNm", "")),
                        "brand": doc.get("brndNm", ""),
                        "pickup": doc.get("pkupOrPsblYn", "") == "Y",
                    })
                return {"query": query, "type": "product", "count": len(products), "products": products}
            except Exception as e:
                return {"error": f"상품 파싱 실패: {str(e)}"}


@register_tool(
    name="daiso_pickup_stock",
    description="다이소 특정 매장의 특정 상품 픽업 재고를 확인합니다. 먼저 daiso_search로 매장코드(strCd)와 상품번호(pdNo)를 조회한 후 호출하세요.",
    parameters={
        "type": "object",
        "properties": {
            "pd_no": {"type": "string", "description": "상품 번호 (daiso_search 결과의 pdNo)"},
            "str_cd": {"type": "string", "description": "매장 코드 (daiso_search store 결과의 code)"},
        },
        "required": ["pd_no", "str_cd"],
    },
)
async def daiso_pickup_stock(pd_no: str, str_cd: str) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{BASE_API}/pd/pdh/selStrPkupStck",
            json=[{"pdNo": pd_no, "strCd": str_cd}],
            headers={**BROWSER_HEADERS, "content-type": "application/json"},
        )
        if resp.status_code != 200:
            return {"error": "재고 조회 실패"}

        try:
            data = resp.json()
            items = data.get("data", [])
            if not isinstance(items, list) or not items:
                return {"pd_no": pd_no, "str_cd": str_cd, "quantity": 0, "in_stock": False}

            item = items[0]
            quantity = int(item.get("stck", 0))
            return {
                "pd_no": pd_no,
                "str_cd": str_cd,
                "quantity": quantity,
                "in_stock": quantity > 0,
                "message": f"재고 {quantity}개" if quantity > 0 else "품절",
            }
        except Exception:
            return {"error": "재고 파싱 실패"}
