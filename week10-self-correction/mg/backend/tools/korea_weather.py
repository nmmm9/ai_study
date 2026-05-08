"""한국 날씨 — KMA via k-skill-proxy."""

import httpx
from tools.registry import register_tool

PROXY = "https://k-skill-proxy.nomadamas.org"


@register_tool(
    name="korea_weather",
    description="한국 단기예보 날씨를 조회합니다. 위도/경도(lat, lon) 또는 격자좌표(nx, ny)를 입력하세요. 위도/경도 예: 서울=37.5665,126.9780, 부산=35.1796,129.0756, 대구=35.8714,128.6014",
    parameters={
        "type": "object",
        "properties": {
            "lat": {"type": "number", "description": "위도"},
            "lon": {"type": "number", "description": "경도"},
            "nx": {"type": "integer", "description": "기상청 격자 X (선택)"},
            "ny": {"type": "integer", "description": "기상청 격자 Y (선택)"},
        },
    },
)
async def korea_weather(lat: float | None = None, lon: float | None = None,
                        nx: int | None = None, ny: int | None = None) -> dict:
    params: dict = {}
    if lat is not None and lon is not None:
        params["lat"] = lat
        params["lon"] = lon
    elif nx is not None and ny is not None:
        params["nx"] = nx
        params["ny"] = ny
    else:
        return {"error": "lat/lon 또는 nx/ny가 필요합니다"}

    async with httpx.AsyncClient(timeout=12) as client:
        resp = await client.get(f"{PROXY}/v1/korea-weather/forecast", params=params)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"날씨 조회 실패 (status {resp.status_code})", "body": resp.text[:300]}
