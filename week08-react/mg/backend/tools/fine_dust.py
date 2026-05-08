"""미세먼지 조회 — AirKorea via k-skill-proxy.

regionHint가 애매하면 candidate_stations를 리턴하므로,
첫 번째 후보 측정소로 자동 재시도한다.
"""

import httpx
from tools.registry import register_tool

PROXY = "https://k-skill-proxy.nomadamas.org"


@register_tool(
    name="fine_dust",
    description="한국 미세먼지(PM10, PM2.5)를 조회합니다. 반드시 '시도 + 도시/구' 형태로 입력하세요. 예: '서울 강남구', '경기 안양', '부산 해운대구'. 사용자가 '안양'만 말하면 '경기 안양'으로 변환해서 호출하세요.",
    parameters={
        "type": "object",
        "properties": {
            "region": {"type": "string", "description": "지역명 (예: 서울 강남구, 부산 해운대구, 경기도 안양)"},
        },
        "required": ["region"],
    },
)
async def fine_dust(region: str) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        # First try with regionHint
        resp = await client.get(
            f"{PROXY}/v1/fine-dust/report",
            params={"regionHint": region},
        )

        if resp.status_code == 200:
            return resp.json()

        # If ambiguous, try with candidate stations
        if resp.status_code == 400:
            try:
                error_data = resp.json()
                candidates = error_data.get("candidate_stations", [])
                if candidates:
                    # Retry with first candidate station name
                    station = candidates[0]
                    retry = await client.get(
                        f"{PROXY}/v1/fine-dust/report",
                        params={"stationName": station},
                    )
                    if retry.status_code == 200:
                        result = retry.json()
                        result["note"] = f"'{region}' 검색 → '{station}' 측정소 기준"
                        return result

                    # If stationName also fails, try regionHint with station name
                    retry2 = await client.get(
                        f"{PROXY}/v1/fine-dust/report",
                        params={"regionHint": station},
                    )
                    if retry2.status_code == 200:
                        result = retry2.json()
                        result["note"] = f"'{region}' 검색 → '{station}' 측정소 기준"
                        return result

                # Return candidate list so agent can ask user
                return {
                    "error": "지역이 애매합니다",
                    "region": region,
                    "candidates": candidates,
                    "message": f"'{region}' 지역에 여러 측정소가 있습니다. 다음 중 선택해주세요: {', '.join(candidates)}" if candidates else f"'{region}' 지역을 찾을 수 없습니다",
                }
            except Exception:
                pass

        return {"error": f"미세먼지 조회 실패 (status {resp.status_code})"}
