"""
tools.py - 여행 플래너 Agent 도구 모음

7주차 핵심: 각 함수마다 JSON 스키마를 정의해서
AI가 사용자 질문을 보고 어떤 함수를 써야 할지 스스로 판단하게 함
"""

import json
import requests


# ─────────────────────────────────────────────
# 1. 함수 구현
# ─────────────────────────────────────────────

def get_weather(city: str, date: str = "today") -> dict:
    """
    Open-Meteo API로 도시 날씨 조회
    - 완전 무료, API 키 불필요
    - 실시간 기상 데이터 제공
    """
    # Step 1: 도시 이름 → 위도/경도 변환 (Geocoding)
    geo_url = (
        f"https://geocoding-api.open-meteo.com/v1/search"
        f"?name={city}&count=1&language=ko"
    )
    geo_res = requests.get(geo_url, timeout=5).json()

    if not geo_res.get("results"):
        return {"error": f"'{city}'를 찾을 수 없습니다. 도시 이름을 다시 확인해주세요."}

    loc = geo_res["results"][0]
    lat, lon = loc["latitude"], loc["longitude"]
    city_name = loc.get("name", city)

    # Step 2: 좌표로 날씨 조회
    weather_url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,weathercode,windspeed_10m,relative_humidity_2m"
        f"&timezone=Asia%2FSeoul"
    )
    weather_res = requests.get(weather_url, timeout=5).json()
    current = weather_res["current"]

    # Step 3: 날씨 코드 → 한국어 설명
    code = current["weathercode"]
    if code == 0:
        condition = "맑음 ☀️"
    elif code == 1:
        condition = "대체로 맑음 🌤"
    elif code == 2:
        condition = "구름 많음 ⛅"
    elif code == 3:
        condition = "흐림 ☁️"
    elif code in range(51, 68):
        condition = "비 🌧"
    elif code in range(71, 78):
        condition = "눈 ❄️"
    elif code in range(80, 83):
        condition = "소나기 🌦"
    elif code in range(95, 100):
        condition = "뇌우 ⛈"
    else:
        condition = "알 수 없음"

    return {
        "city": city_name,
        "date": date,
        "temperature": f"{current['temperature_2m']}°C",
        "condition": condition,
        "humidity": f"{current['relative_humidity_2m']}%",
        "wind_speed": f"{current['windspeed_10m']} km/h",
    }


def search_attractions(city: str, category: str = "전체") -> dict:
    """
    도시별 관광지/맛집 추천
    - 샘플 데이터 기반 (실제 서비스에서는 Google Places API 연동)
    """
    db = {
        "제주": {
            "자연": ["한라산 국립공원", "성산일출봉", "협재해수욕장", "천지연폭포", "용머리해안"],
            "문화": ["제주민속촌", "국립제주박물관", "돌하르방공원", "테디베어뮤지엄"],
            "맛집": ["흑돼지거리 (제주시)", "동문시장 고기국수", "애월 카페거리", "성산 해물뚝배기"],
        },
        "부산": {
            "자연": ["해운대해수욕장", "광안리해수욕장", "태종대", "이기대공원"],
            "문화": ["감천문화마을", "자갈치시장", "국제시장", "부산현대미술관"],
            "맛집": ["남포동 씨앗호떡", "기장 대게거리", "서면 먹자골목", "해운대 시장 돼지국밥"],
        },
        "서울": {
            "자연": ["북한산 국립공원", "한강공원", "남산타워", "올림픽공원"],
            "문화": ["경복궁", "북촌한옥마을", "인사동", "홍대 거리", "이태원"],
            "맛집": ["광장시장 빈대떡", "을지로 골목", "망원동 카페거리", "성수동 뚝섬"],
        },
        "경주": {
            "자연": ["보문호", "토함산", "양동마을"],
            "문화": ["불국사", "석굴암", "첨성대", "대릉원", "국립경주박물관"],
            "맛집": ["황리단길", "성동시장 경주빵", "교촌마을 쌈밥"],
        },
        "강릉": {
            "자연": ["경포해수욕장", "정동진", "오죽헌"],
            "문화": ["선교장", "강릉중앙시장", "강릉커피거리"],
            "맛집": ["초당순두부마을", "강릉 장칼국수", "안목해변 커피거리"],
        },
    }

    # 도시 이름 매칭 (부분 일치)
    matched = None
    for key in db:
        if key in city or city in key:
            matched = key
            break

    if not matched:
        return {
            "error": f"'{city}' 정보가 없습니다.",
            "지원 도시": list(db.keys()),
        }

    data = db[matched]
    result = data if category == "전체" else {category: data.get(category, [])}

    return {"city": matched, "category": category, "attractions": result}


def calculate_budget(
    days: int,
    accommodation_type: str = "중급",
    meal_budget: str = "보통",
    transport: str = "대중교통",
) -> dict:
    """
    여행 총 예산 계산
    - 숙박/식비/교통/활동비 항목별 분류
    """
    accommodation_per_night = {"저렴": 40_000, "중급": 100_000, "고급": 250_000}
    meal_per_day = {"절약": 20_000, "보통": 40_000, "여유": 80_000}
    transport_per_day = {"대중교통": 15_000, "렌트카": 80_000, "택시": 50_000}

    nights = max(days - 1, 0)
    acc = accommodation_per_night.get(accommodation_type, 100_000) * nights
    meal = meal_per_day.get(meal_budget, 40_000) * days
    trans = transport_per_day.get(transport, 15_000) * days
    activity = 20_000 * days  # 입장료/체험비 기본값

    total = acc + meal + trans + activity

    return {
        "여행 일수": f"{days}일 ({nights}박)",
        "항목별 예산": {
            "숙박비": f"{acc:,}원  ({accommodation_type} · {nights}박)",
            "식비": f"{meal:,}원  ({meal_budget} · {days}일)",
            "교통비": f"{trans:,}원  ({transport} · {days}일)",
            "활동/입장료": f"{activity:,}원  ({days}일)",
        },
        "총 예산": f"{total:,}원",
        "1일 평균": f"{total // days:,}원/일",
    }


def get_best_season(city: str) -> dict:
    """
    도시별 여행 최적 시기 및 계절별 특징
    """
    db = {
        "제주": {
            "최적 시기": "3~5월 (봄), 9~11월 (가을)",
            "봄 (3~5월)": "유채꽃·벚꽃 만개, 날씨 온화, 여행 최성수기",
            "여름 (6~8월)": "해수욕 가능, 7~8월 태풍 주의, 습하고 더움",
            "가을 (9~11월)": "단풍·억새, 맑은 날씨, 두 번째 성수기",
            "겨울 (12~2월)": "한라산 설경, 귤 수확철, 바람 강함",
            "tip": "7~8월은 태풍과 인파로 비추천",
        },
        "부산": {
            "최적 시기": "4~6월 (봄), 9~10월 (가을)",
            "봄 (3~5월)": "벚꽃 명소 많음, 선선하고 맑음",
            "여름 (6~8월)": "해수욕 최고, 더위 심하고 혼잡",
            "가을 (9~11월)": "맑은 날씨, 국제영화제 (10월)",
            "겨울 (12~2월)": "전국 대비 온화, 눈 거의 없음",
            "tip": "10월 부산국제영화제 기간 숙소 미리 예약 필수",
        },
        "서울": {
            "최적 시기": "4~5월 (봄), 9~11월 (가을)",
            "봄 (3~5월)": "벚꽃·튤립 축제, 야외 활동 최적",
            "여름 (6~8월)": "장마·폭염, 실내 여행 위주 추천",
            "가을 (9~11월)": "단풍, 선선한 날씨, 축제 다양",
            "겨울 (12~2월)": "눈 구경, 크리스마스 야경, 한파 주의",
            "tip": "봄·가을은 숙소 가격이 오르니 미리 예약",
        },
        "경주": {
            "최적 시기": "4~5월 (봄), 10월 (가을)",
            "봄 (3~5월)": "벚꽃 명소, 야경 투어 인기",
            "여름 (6~8월)": "덥지만 야간 관광 가능",
            "가을 (9~11월)": "단풍과 문화재 조화, 10월 신라문화제",
            "겨울 (12~2월)": "한산하고 조용, 야경 아름다움",
            "tip": "황리단길은 주말에 매우 혼잡, 평일 방문 추천",
        },
    }

    matched = None
    for key in db:
        if key in city or city in key:
            matched = key
            break

    if not matched:
        return {
            "city": city,
            "일반 추천": "한국은 봄(4~5월)과 가을(9~10월)이 여행 최적기입니다.",
            "지원 도시": list(db.keys()),
        }

    return {"city": matched, **db[matched]}


# ─────────────────────────────────────────────
# 2. JSON 스키마 정의 (AI가 함수를 이해하는 설명서)
# ─────────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": (
                "특정 도시의 현재 날씨를 조회합니다. "
                "여행지 날씨가 궁금하거나, 우산이 필요한지, "
                "비가 오는지 물어볼 때 사용합니다."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "날씨를 조회할 도시 이름 (예: 제주, 부산, Seoul, Tokyo)",
                    },
                    "date": {
                        "type": "string",
                        "description": "조회할 날짜. 오늘은 'today', 특정 날짜는 'YYYY-MM-DD' 형식",
                        "default": "today",
                    },
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_attractions",
            "description": (
                "특정 도시의 관광지, 명소, 맛집을 검색합니다. "
                "어디 가면 좋을지, 뭘 볼 수 있는지, "
                "어떤 음식을 먹을 수 있는지 물어볼 때 사용합니다."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "관광지를 검색할 도시 이름 (예: 제주, 부산, 서울, 경주, 강릉)",
                    },
                    "category": {
                        "type": "string",
                        "description": "검색할 카테고리. 자연경관은 '자연', 역사/문화는 '문화', 음식점은 '맛집', 전부 보고 싶으면 '전체'",
                        "enum": ["자연", "문화", "맛집", "전체"],
                        "default": "전체",
                    },
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_budget",
            "description": (
                "여행 예산을 계산합니다. "
                "여행 비용이 얼마나 드는지, 예산이 얼마나 필요한지 "
                "물어볼 때 사용합니다."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "여행 일수 (예: 2박3일이면 3, 3박4일이면 4)",
                    },
                    "accommodation_type": {
                        "type": "string",
                        "description": "숙박 유형. 게스트하우스/모텔은 '저렴', 일반 호텔은 '중급', 리조트/특급호텔은 '고급'",
                        "enum": ["저렴", "중급", "고급"],
                        "default": "중급",
                    },
                    "meal_budget": {
                        "type": "string",
                        "description": "1일 식비 수준. 편의점/분식은 '절약', 일반 식당은 '보통', 맛집 위주는 '여유'",
                        "enum": ["절약", "보통", "여유"],
                        "default": "보통",
                    },
                    "transport": {
                        "type": "string",
                        "description": "주요 이동 수단",
                        "enum": ["대중교통", "렌트카", "택시"],
                        "default": "대중교통",
                    },
                },
                "required": ["days"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_best_season",
            "description": (
                "특정 도시의 여행 최적 시기와 계절별 특징을 알려줍니다. "
                "언제 가면 좋은지, 어느 계절이 좋은지, "
                "지금 가도 괜찮은지 물어볼 때 사용합니다."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "여행 시기를 확인할 도시 이름",
                    },
                },
                "required": ["city"],
            },
        },
    },
]


# ─────────────────────────────────────────────
# 3. 함수 실행 디스패처
# ─────────────────────────────────────────────

TOOL_MAP = {
    "get_weather": get_weather,
    "search_attractions": search_attractions,
    "calculate_budget": calculate_budget,
    "get_best_season": get_best_season,
}


def execute_tool(tool_name: str, tool_args: dict) -> str:
    """AI가 선택한 함수를 실행하고 결과를 JSON 문자열로 반환"""
    if tool_name not in TOOL_MAP:
        return json.dumps({"error": f"존재하지 않는 함수: {tool_name}"}, ensure_ascii=False)

    try:
        result = TOOL_MAP[tool_name](**tool_args)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
