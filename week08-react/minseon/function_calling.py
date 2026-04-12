"""
function_calling.py
───────────────────
OOTD 에이전트에서 사용하는 모든 도구(Tool)의 스키마와 실행 함수를 정의합니다.

구조
  TOOL_SCHEMAS  : OpenAI Chat Completions API에 전달하는 JSON 스키마 목록
  execute_tool  : 도구 이름 + 입력값을 받아 결과를 JSON 문자열로 반환하는 통합 실행기
"""

import json
from tools.weather import fetch_weather
from tools.wardrobe import filter_wardrobe, get_wardrobe_summary
from tools.colors import get_color_combinations, get_seasonal_palette


# ══════════════════════════════════════════════════════════════
# 1. Tool Schema Definitions  (OpenAI API 형식)
# ══════════════════════════════════════════════════════════════

TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": (
                "현재 날씨와 기온 정보를 조회합니다. "
                "기온(°C), 체감온도, 습도, 풍속, 날씨 카테고리(맑음/흐림/비/눈)를 반환합니다."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "날씨를 조회할 도시 이름 (예: 서울, 부산, Seoul)",
                    }
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_rain_and_umbrella",
            "description": (
                "비·눈 예보를 확인하고 우산 필요 여부를 판단합니다. "
                "현재 비/눈이 내리거나 습도 80% 이상이면 우산 알림을 포함합니다."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "우산 여부를 확인할 도시 이름",
                    }
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_wardrobe_items",
            "description": (
                "옷장에 있는 아이템을 조회합니다. "
                "카테고리·계절·날씨 조건으로 필터링할 수 있습니다."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "카테고리 필터: 상의, 하의, 아우터, 신발, 액세서리 (빈 문자열 = 전체)",
                    },
                    "season": {
                        "type": "string",
                        "description": "계절 필터: 봄, 여름, 가을, 겨울 (빈 문자열 = 전체)",
                    },
                    "weather_condition": {
                        "type": "string",
                        "description": "날씨 조건 필터: 맑음, 흐림, 비, 눈 (빈 문자열 = 전체)",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_wardrobe_overview",
            "description": (
                "옷장 전체 구성 요약(카테고리별·색상별 수량)을 반환합니다. "
                "어떤 아이템들이 있는지 전체적으로 파악할 때 먼저 호출하세요."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_color_pairings",
            "description": (
                "특정 색상과 잘 어울리는 색상 조합을 색채학 기반으로 반환합니다. "
                "코디 색상 매칭에 사용하세요."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "color": {
                        "type": "string",
                        "description": (
                            "기준 색상 이름 (영문 소문자): "
                            "white, black, navy, beige, gray, blue, light_blue, "
                            "camel, burgundy, khaki, sage, cream, tan, brown 등"
                        ),
                    }
                },
                "required": ["color"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_season_palette",
            "description": "계절별 추천 색상 팔레트(핵심 컬러 + 포인트 컬러)를 반환합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "season": {
                        "type": "string",
                        "description": "계절 이름: 봄, 여름, 가을, 겨울, 봄/가을",
                    }
                },
                "required": ["season"],
            },
        },
    },
]


# ══════════════════════════════════════════════════════════════
# 2. 개별 실행 함수
# ══════════════════════════════════════════════════════════════

def _run_get_weather(location: str) -> dict:
    return fetch_weather(location)


def _run_check_rain_and_umbrella(location: str) -> dict:
    """날씨 데이터를 분석해 우산 필요 여부와 옷차림 조언을 반환합니다."""
    weather = fetch_weather(location)
    category = weather.get("category", "")
    humidity = weather.get("humidity", 0)

    is_precipitation = category in ("비", "눈")
    high_humidity = humidity >= 80
    umbrella_needed = is_precipitation or high_humidity

    if category == "비":
        rain_status = "현재 비가 내리고 있습니다"
        umbrella_advice = "☂️ 우산 필수! 반드시 우산을 챙기세요."
        clothing_advice = (
            "방수 아우터 또는 레인코트 권장. 방수 처리된 신발 추천. "
            "밝은 색상 면 소재는 젖으면 비칠 수 있으니 주의하세요."
        )
    elif category == "눈":
        rain_status = "현재 눈이 내리고 있습니다"
        umbrella_advice = "☂️ 우산 또는 방수 모자 필수"
        clothing_advice = (
            "방수·방한 부츠 착용. 미끄럼 방지 밑창 신발 권장. "
            "두꺼운 패딩 또는 방수 코트 필수."
        )
    elif high_humidity:
        rain_status = f"습도가 높습니다 ({humidity}%) — 비가 올 가능성 있음"
        umbrella_advice = "🌂 우산을 챙기는 것을 권장합니다."
        clothing_advice = (
            "땀 흡수·속건 소재 추천. 린넨이나 두꺼운 면 소재는 피하세요. "
            "습도가 높아 불쾌지수가 높을 수 있습니다."
        )
    else:
        rain_status = "비 예보 없음 ☀️"
        umbrella_advice = "우산 불필요"
        clothing_advice = "날씨가 맑으니 일반 코디를 즐기세요."

    return {
        "location": location,
        "weather_category": category,
        "temperature": weather.get("temperature"),
        "humidity": humidity,
        "umbrella_needed": umbrella_needed,
        "rain_status": rain_status,
        "umbrella_advice": umbrella_advice,
        "clothing_advice": clothing_advice,
    }


def _run_get_wardrobe_items(
    category: str = "",
    season: str = "",
    weather_condition: str = "",
) -> dict:
    items = filter_wardrobe(
        category=category or None,
        season=season or None,
        weather=weather_condition or None,
    )
    return {
        "items": items,
        "count": len(items),
        "filters": {
            "category": category or "전체",
            "season": season or "전체",
            "weather_condition": weather_condition or "전체",
        },
    }


def _run_get_wardrobe_overview() -> dict:
    return get_wardrobe_summary()


def _run_get_color_pairings(color: str) -> dict:
    return get_color_combinations(color)


def _run_get_season_palette(season: str) -> dict:
    return get_seasonal_palette(season)


# ══════════════════════════════════════════════════════════════
# 3. 통합 실행기 (Tool Dispatcher)
# ══════════════════════════════════════════════════════════════

_EXECUTORS: dict = {
    "get_weather":              lambda inp: _run_get_weather(**inp),
    "check_rain_and_umbrella":  lambda inp: _run_check_rain_and_umbrella(**inp),
    "get_wardrobe_items":       lambda inp: _run_get_wardrobe_items(**inp),
    "get_wardrobe_overview":    lambda _:   _run_get_wardrobe_overview(),
    "get_color_pairings":       lambda inp: _run_get_color_pairings(**inp),
    "get_season_palette":       lambda inp: _run_get_season_palette(**inp),
}


def execute_tool(tool_name: str, tool_inputs: dict) -> str:
    """
    도구를 실행하고 결과를 JSON 문자열로 반환합니다.

    Args:
        tool_name  : TOOL_SCHEMAS에 정의된 도구 이름
        tool_inputs: Claude가 생성한 입력 파라미터 dict

    Returns:
        JSON 직렬화된 결과 문자열 (오류 시에도 JSON 반환)
    """
    executor = _EXECUTORS.get(tool_name)
    if not executor:
        return json.dumps(
            {"error": f"알 수 없는 도구: {tool_name}"},
            ensure_ascii=False,
        )
    try:
        result = executor(tool_inputs)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as exc:
        return json.dumps(
            {"error": f"[{tool_name}] 실행 오류: {exc}"},
            ensure_ascii=False,
        )
