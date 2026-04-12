"""날씨 정보 조회 모듈

기상청 초단기실황조회 API (공공데이터포털) 사용
API 키: .env 또는 환경변수 KMA_API_KEY 설정 필요

API 키 발급: https://data.go.kr → "기상청_단기예보 조회서비스" 검색 → 활용신청
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Optional


# ── 기상청 격자 좌표 (nx, ny) ─────────────────────────────────────────
# 더 많은 좌표는 기상청 공식 격자 좌표표 참고
# https://www.kma.go.kr/kma/pages/kma04_03.do
CITY_GRID: dict[str, tuple[int, int]] = {
    "서울":   (60, 127),
    "서울특별시": (60, 127),
    "부산":   (98, 76),
    "부산광역시": (98, 76),
    "인천":   (55, 124),
    "인천광역시": (55, 124),
    "대구":   (89, 90),
    "대구광역시": (89, 90),
    "광주":   (58, 74),
    "광주광역시": (58, 74),
    "대전":   (67, 100),
    "대전광역시": (67, 100),
    "울산":   (102, 84),
    "울산광역시": (102, 84),
    "세종":   (66, 103),
    "세종특별자치시": (66, 103),
    "수원":   (60, 121),
    "성남":   (63, 124),
    "고양":   (57, 128),
    "용인":   (64, 119),
    "창원":   (91, 77),
    "전주":   (63, 89),
    "천안":   (63, 110),
    "청주":   (69, 107),
    "포항":   (102, 94),
    "제주":   (52, 38),
    "제주도":  (52, 38),
    "제주시":  (52, 38),
    "강릉":   (92, 131),
    "춘천":   (73, 134),
    "여수":   (73, 66),
    "순천":   (75, 72),
    "목포":   (50, 67),
    "경주":   (100, 91),
}

# ── 강수형태 코드 ──────────────────────────────────────────────────────
PTY_MAP = {
    "0": "없음",
    "1": "비",
    "2": "비/눈",
    "3": "눈",
    "4": "소나기",
    "5": "빗방울",
    "6": "빗방울/눈날림",
    "7": "눈날림",
}

# ── 하늘상태 코드 (단기예보) ──────────────────────────────────────────
SKY_MAP = {
    "1": "맑음",
    "3": "구름많음",
    "4": "흐림",
}


def _get_grid(location: str) -> tuple[int, int]:
    """도시 이름을 격자 좌표로 변환합니다. 알 수 없는 경우 서울 기본값."""
    # 완전 일치
    if location in CITY_GRID:
        return CITY_GRID[location]
    # 부분 일치 (예: "서울 강남구" → "서울")
    for city, grid in CITY_GRID.items():
        if city in location or location in city:
            return grid
    # 기본값: 서울
    return (60, 127)


def _get_base_datetime() -> tuple[str, str]:
    """기상청 초단기실황 base_date, base_time을 계산합니다.

    초단기실황은 매 정시 발표 (30분 이후부터 조회 가능).
    현재 시각 기준 가장 최근 정시를 사용하되, 현재 분이 30 미만이면
    1시간 전 정시 데이터를 조회합니다.
    """
    now = datetime.now()

    if now.minute < 30:
        # 1시간 전 정시
        base_dt = now - timedelta(hours=1)
    else:
        base_dt = now

    base_date = base_dt.strftime("%Y%m%d")
    base_time = base_dt.strftime("%H00")  # 정시 (예: "0900", "1400")
    return base_date, base_time


def _call_kma_api(nx: int, ny: int, api_key: str) -> dict:
    """기상청 초단기실황조회 API를 호출합니다.

    Returns:
        카테고리별 obsrValue 딕셔너리 (예: {"T1H": "18.0", "PTY": "0", ...})
    """
    base_date, base_time = _get_base_datetime()

    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
    params = {
        "serviceKey": api_key,   # 인코딩된 키 그대로 사용
        "numOfRows": "10",
        "pageNo": "1",
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": str(nx),
        "ny": str(ny),
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    body = response.json().get("response", {}).get("body", {})
    items = body.get("items", {}).get("item", [])

    return {item["category"]: item["obsrValue"] for item in items}


def _parse_kma_data(obs: dict, location: str) -> dict:
    """기상청 관측값 딕셔너리를 OOTD 에이전트 형식으로 변환합니다."""
    temp_c = float(obs.get("T1H", 20))
    humidity = int(float(obs.get("REH", 50)))
    wind_speed_ms = float(obs.get("WSD", 2))
    wind_speed_kmh = round(wind_speed_ms * 3.6, 1)
    pty_code = obs.get("PTY", "0")
    rn1 = float(obs.get("RN1", 0))    # 강수량 mm

    # 강수형태 → 날씨 카테고리
    pty_desc = PTY_MAP.get(pty_code, "없음")
    if pty_code in ("1", "4", "5"):
        category = "비"
        description = "비"
    elif pty_code in ("2", "6"):
        category = "비"
        description = "비/눈"
    elif pty_code in ("3", "7"):
        category = "눈"
        description = "눈"
    else:
        category = "맑음"
        description = "맑음"

    # 기온 카테고리 & 의류 팁
    if temp_c >= 28:
        temp_category = "매우 더움"
        clothing_tip = "반팔, 반바지, 린넨 소재 추천"
    elif temp_c >= 23:
        temp_category = "더움"
        clothing_tip = "반팔 티셔츠, 가벼운 원피스 추천"
    elif temp_c >= 17:
        temp_category = "따뜻함"
        clothing_tip = "얇은 긴팔, 가벼운 자켓 준비"
    elif temp_c >= 10:
        temp_category = "서늘함"
        clothing_tip = "긴팔, 카디건 또는 얇은 자켓 필수"
    elif temp_c >= 3:
        temp_category = "추움"
        clothing_tip = "두꺼운 스웨터, 코트, 목도리 추천"
    else:
        temp_category = "매우 추움"
        clothing_tip = "패딩, 두꺼운 코트, 방한 용품 필수"

    # 계절 추정
    if temp_c >= 22:
        estimated_season = "여름"
    elif temp_c >= 13:
        estimated_season = "봄/가을"
    else:
        estimated_season = "겨울"

    return {
        "location": location,
        "temperature": round(temp_c, 1),
        "feels_like": round(temp_c, 1),   # 초단기실황에는 체감온도 없음 → 기온으로 대체
        "humidity": humidity,
        "wind_speed": wind_speed_kmh,
        "uv_index": 0,                    # 초단기실황에는 UV 없음
        "description": description,
        "pty_code": pty_code,
        "pty_desc": pty_desc,
        "rainfall_mm": rn1,
        "category": category,
        "temp_category": temp_category,
        "clothing_tip": clothing_tip,
        "estimated_season": estimated_season,
    }


def _fallback_wttr(location: str) -> dict:
    """API 키 없을 때 wttr.in으로 폴백합니다."""
    url = f"https://wttr.in/{location}?format=j1"
    response = requests.get(url, timeout=10, headers={"User-Agent": "OOTD-Agent/1.0"})
    response.raise_for_status()
    data = response.json()
    return _parse_wttr(data, location)


def _parse_wttr(data: dict, location: str) -> dict:
    """wttr.in 응답을 파싱합니다 (폴백용)."""
    current = data.get("current_condition", [{}])[0]
    temp_c = int(current.get("temp_C", 20))
    feels_like_c = int(current.get("FeelsLikeC", 20))
    humidity = int(current.get("humidity", 50))
    wind_speed = int(current.get("windspeedKmph", 10))
    uv_index = int(current.get("uvIndex", 3))
    weather_desc = current.get("weatherDesc", [{}])[0].get("value", "Unknown")

    desc_lower = weather_desc.lower()
    if any(w in desc_lower for w in ["rain", "drizzle", "shower", "mist"]):
        category = "비"
    elif any(w in desc_lower for w in ["snow", "blizzard", "sleet"]):
        category = "눈"
    elif any(w in desc_lower for w in ["cloud", "overcast", "fog"]):
        category = "흐림"
    else:
        category = "맑음"

    if temp_c >= 28:
        temp_category, clothing_tip = "매우 더움", "반팔, 반바지, 린넨 소재 추천"
    elif temp_c >= 23:
        temp_category, clothing_tip = "더움", "반팔 티셔츠, 가벼운 원피스 추천"
    elif temp_c >= 17:
        temp_category, clothing_tip = "따뜻함", "얇은 긴팔, 가벼운 자켓 준비"
    elif temp_c >= 10:
        temp_category, clothing_tip = "서늘함", "긴팔, 카디건 또는 얇은 자켓 필수"
    elif temp_c >= 3:
        temp_category, clothing_tip = "추움", "두꺼운 스웨터, 코트, 목도리 추천"
    else:
        temp_category, clothing_tip = "매우 추움", "패딩, 두꺼운 코트, 방한 용품 필수"

    estimated_season = "여름" if temp_c >= 22 else ("봄/가을" if temp_c >= 13 else "겨울")

    return {
        "location": location,
        "temperature": temp_c,
        "feels_like": feels_like_c,
        "humidity": humidity,
        "wind_speed": wind_speed,
        "uv_index": uv_index,
        "description": weather_desc,
        "category": category,
        "temp_category": temp_category,
        "clothing_tip": clothing_tip,
        "estimated_season": estimated_season,
        "source": "wttr.in (폴백)",
    }


def fetch_weather(location: str) -> dict:
    """날씨 데이터를 가져옵니다.

    KMA_API_KEY 환경변수가 설정되어 있으면 기상청 초단기실황 API를 사용하고,
    없으면 wttr.in으로 폴백합니다.

    환경변수 설정 방법:
        Windows:  set KMA_API_KEY=your_encoded_key
        Linux/Mac: export KMA_API_KEY=your_encoded_key
        .env 파일: KMA_API_KEY=your_encoded_key  (python-dotenv 사용 시)
    """
    api_key = os.environ.get("KMA_API_KEY", "").strip()

    try:
        if api_key:
            nx, ny = _get_grid(location)
            obs = _call_kma_api(nx, ny, api_key)
            result = _parse_kma_data(obs, location)
            result["source"] = "기상청 초단기실황"
            result["grid"] = {"nx": nx, "ny": ny}
            return result
        else:
            # API 키 없음 → wttr.in 폴백
            result = _fallback_wttr(location)
            return result

    except requests.RequestException as e:
        return _error_response(location, f"날씨 조회 실패: {e}")
    except (KeyError, IndexError, ValueError, TypeError) as e:
        return _error_response(location, f"날씨 데이터 파싱 실패: {e}")


def _error_response(location: str, message: str) -> dict:
    """오류 시 기본 응답을 반환합니다."""
    return {
        "location": location,
        "error": message,
        "temperature": 20,
        "feels_like": 20,
        "humidity": 50,
        "description": "알 수 없음",
        "category": "맑음",
        "temp_category": "따뜻함",
        "clothing_tip": "평범한 복장 추천",
        "estimated_season": "봄/가을",
        "wind_speed": 10,
        "uv_index": 3,
    }
