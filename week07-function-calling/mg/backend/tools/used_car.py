"""중고차 시세 검색 — SK렌터카 다이렉트 타고BUY."""

import re
import json
import httpx
from tools.registry import register_tool


@register_tool(
    name="used_car_price",
    description="중고차 시세를 검색합니다. 차종 키워드로 SK렌터카 타고BUY 매물을 조회합니다. 예: 아반떼, K3, 쏘나타",
    parameters={
        "type": "object",
        "properties": {
            "keyword": {"type": "string", "description": "차종 키워드 (예: 아반떼, K3, 그랜저)"},
        },
        "required": ["keyword"],
    },
)
async def used_car_price(keyword: str) -> dict:
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        resp = await client.get(
            "https://www.skdirect.co.kr/tb",
            headers={"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
        )
        if resp.status_code != 200:
            return {"error": "타고BUY 조회 실패"}

        # __NEXT_DATA__ 에서 inventory 추출
        match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, re.DOTALL)
        if not match:
            return {"error": "데이터 추출 실패"}

        try:
            next_data = json.loads(match.group(1))
            # props.pageProps 안에 차량 목록이 있음
            page_props = next_data.get("props", {}).get("pageProps", {})

            # 차량 목록 찾기
            cars = []
            for key, val in page_props.items():
                if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                    if any(k in str(val[0].keys()) for k in ["carName", "modelName", "price", "rentPrice"]):
                        cars = val
                        break

            if not cars:
                # fallback: 모든 리스트에서 검색
                for key, val in page_props.items():
                    if isinstance(val, list):
                        cars.extend(val) if isinstance(val, list) else None

            # 키워드 필터
            keyword_lower = keyword.lower()
            filtered = [
                c for c in cars
                if isinstance(c, dict) and keyword_lower in json.dumps(c, ensure_ascii=False).lower()
            ][:5]

            if not filtered:
                return {"keyword": keyword, "count": 0, "cars": [], "message": "해당 차종 매물 없음"}

            results = []
            for c in filtered:
                results.append({
                    "name": c.get("carName", c.get("modelName", c.get("name", ""))),
                    "year": c.get("year", c.get("carYear", "")),
                    "price": c.get("price", c.get("buyPrice", "")),
                    "rent": c.get("rentPrice", c.get("monthlyRent", "")),
                    "mileage": c.get("mileage", c.get("km", "")),
                })
            return {"keyword": keyword, "count": len(results), "cars": results}
        except Exception as e:
            return {"error": f"파싱 실패: {str(e)}"}
