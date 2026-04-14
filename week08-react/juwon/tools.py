"""
tools.py - 여행 플래너 Agent 도구 모음 (8주차)

7주차 함수 4개 유지 + 새로운 함수 6개 추가 = 총 10개
AI가 ReAct 패턴으로 이 함수들을 스스로 조합해서 사용함
"""

import json
import requests


# ─────────────────────────────────────────────
# 도시별 통합 데이터베이스
# ─────────────────────────────────────────────

CITY_DB = {
    "제주": {
        "attractions": {
            "자연": ["한라산 국립공원", "성산일출봉", "협재해수욕장", "천지연폭포", "용머리해안", "비자림"],
            "문화": ["제주민속촌", "국립제주박물관", "돌하르방공원", "테디베어뮤지엄", "제주현대미술관"],
        },
        "restaurants": [
            {"name": "흑돼지거리", "cuisine": "흑돼지구이", "price": "중급", "specialty": "제주 흑돼지 오겹살", "area": "제주시 연동"},
            {"name": "동문시장 고기국수", "cuisine": "국수", "price": "저렴", "specialty": "제주식 고기국수", "area": "동문시장"},
            {"name": "애월 카페거리", "cuisine": "카페/디저트", "price": "중급", "specialty": "오션뷰 카페", "area": "애월"},
            {"name": "성산 해물뚝배기", "cuisine": "해물", "price": "중급", "specialty": "신선한 해물뚝배기", "area": "성산"},
            {"name": "옥돔식당", "cuisine": "생선구이", "price": "고급", "specialty": "제주 옥돔구이", "area": "제주시"},
        ],
        "accommodation": [
            {"name": "롯데호텔 제주", "type": "고급", "price": "250,000원~", "location": "중문관광단지", "features": "오션뷰, 수영장, 스파"},
            {"name": "한화리조트 제주", "type": "중급", "price": "120,000원~", "location": "중문", "features": "리조트 시설, 편의점"},
            {"name": "제주 게스트하우스", "type": "저렴", "price": "35,000원~", "location": "제주시 구도심", "features": "무료 조식, 자전거 대여"},
        ],
        "transportation": {
            "서울→제주": {"비행기": "1시간 10분, 60,000~120,000원", "배편": "11시간, 30,000원~"},
            "부산→제주": {"비행기": "1시간, 50,000~100,000원"},
            "현지교통": "렌터카 강력 추천 (하루 50,000~80,000원), 대중교통은 불편함",
        },
        "festivals": [
            {"name": "제주 유채꽃 축제", "month": "3~4월", "location": "가시리", "desc": "드넓은 유채꽃밭 감상"},
            {"name": "성산일출제", "month": "1월 1일", "location": "성산일출봉", "desc": "새해 일출 행사"},
            {"name": "제주 들불축제", "month": "3월", "location": "새별오름", "desc": "오름 들불놓기 전통 행사"},
            {"name": "제주 마라톤", "month": "3월", "location": "제주시", "desc": "제주 전역 마라톤"},
        ],
        "local_tips": [
            "렌터카 없으면 이동 매우 불편 - 미리 예약 필수",
            "제주 바람이 강해 얇은 겉옷 항상 챙기기",
            "성산일출봉 일출 보려면 새벽 5시 이전 도착",
            "흑돼지는 제주시 연동 흑돼지거리에서 즐기기",
            "동문·서문시장에서 제주 특산품 저렴하게 구입 가능",
            "7~8월은 태풍 시즌, 일정 여유 있게 계획하기",
            "제주 올레길 트래킹 코스 잘 조성되어 있음",
        ],
        "best_season": {
            "최적시기": "3~5월(봄), 9~11월(가을)",
            "봄": "유채꽃·벚꽃, 온화한 날씨, 여행 성수기",
            "여름": "해수욕 가능, 7~8월 태풍 주의, 습하고 더움",
            "가을": "단풍·억새, 맑은 하늘, 두 번째 성수기",
            "겨울": "한라산 설경, 귤 수확철, 바람 강함",
            "tip": "7~8월은 태풍과 인파로 비추천",
        },
    },
    "부산": {
        "attractions": {
            "자연": ["해운대해수욕장", "광안리해수욕장", "태종대", "이기대공원", "몰운대"],
            "문화": ["감천문화마을", "자갈치시장", "국제시장", "부산현대미술관", "영도다리"],
        },
        "restaurants": [
            {"name": "남포동 씨앗호떡", "cuisine": "길거리음식", "price": "저렴", "specialty": "씨앗호떡", "area": "남포동"},
            {"name": "기장 대게집", "cuisine": "해물", "price": "고급", "specialty": "대게, 킹크랩", "area": "기장"},
            {"name": "서면 돼지국밥", "cuisine": "국밥", "price": "저렴", "specialty": "부산식 돼지국밥", "area": "서면"},
            {"name": "해운대 시장 어묵", "cuisine": "분식", "price": "저렴", "specialty": "부산 어묵", "area": "해운대"},
            {"name": "광안리 횟집거리", "cuisine": "횟집", "price": "중급", "specialty": "신선한 회", "area": "광안리"},
        ],
        "accommodation": [
            {"name": "파라다이스 호텔 부산", "type": "고급", "price": "300,000원~", "location": "해운대", "features": "해운대 바다뷰, 카지노"},
            {"name": "노보텔 앰배서더 부산", "type": "중급", "price": "130,000원~", "location": "해운대", "features": "해변 근접, 편의시설"},
            {"name": "부산 게스트하우스", "type": "저렴", "price": "30,000원~", "location": "남포동", "features": "자갈치 도보, 무료 조식"},
        ],
        "transportation": {
            "서울→부산": {"KTX": "2시간 30분, 59,800원", "고속버스": "4시간, 23,900원", "비행기": "1시간, 60,000원~"},
            "현지교통": "지하철·버스 편리 (교통카드 추천), 해운대-남포동 지하철 30분",
        },
        "festivals": [
            {"name": "부산국제영화제(BIFF)", "month": "10월", "location": "해운대 센텀시티", "desc": "아시아 최대 국제 영화제"},
            {"name": "부산 불꽃축제", "month": "10월", "location": "광안리해수욕장", "desc": "광안대교 배경 불꽃놀이"},
            {"name": "자갈치 문화관광축제", "month": "10월", "location": "자갈치시장", "desc": "해산물 축제"},
        ],
        "local_tips": [
            "교통카드 하나로 지하철·버스 모두 이용 가능",
            "자갈치시장은 오전 일찍 방문해야 신선한 해산물 구입 가능",
            "해운대 성수기(7~8월)는 숙소 2~3개월 전 예약 필수",
            "광안리 불꽃축제 시 주변 숙소 몇 달 전부터 예약 마감",
            "감천문화마을은 오전 일찍 방문 추천 (오후엔 인파 많음)",
        ],
        "best_season": {
            "최적시기": "4~6월(봄), 9~10월(가을)",
            "봄": "벚꽃 명소 많음, 선선하고 맑음",
            "여름": "해수욕 최고, 더위 심하고 혼잡",
            "가을": "맑은 날씨, 국제영화제",
            "겨울": "전국 대비 온화, 눈 거의 없음",
            "tip": "10월 부산국제영화제 기간 숙소 미리 예약 필수",
        },
    },
    "서울": {
        "attractions": {
            "자연": ["북한산 국립공원", "한강공원", "남산타워", "올림픽공원", "서울숲"],
            "문화": ["경복궁", "북촌한옥마을", "인사동", "홍대 거리", "이태원", "동대문 DDP"],
        },
        "restaurants": [
            {"name": "광장시장", "cuisine": "전통/분식", "price": "저렴", "specialty": "녹두빈대떡, 마약김밥", "area": "종로"},
            {"name": "을지로 골목 맛집", "cuisine": "다양", "price": "중급", "specialty": "레트로 감성 맛집", "area": "을지로"},
            {"name": "망원동 카페거리", "cuisine": "카페", "price": "중급", "specialty": "감성 카페 거리", "area": "망원동"},
            {"name": "성수동 브런치", "cuisine": "브런치/카페", "price": "중급", "specialty": "힙한 브런치", "area": "성수동"},
            {"name": "홍대 포장마차", "cuisine": "분식/술집", "price": "저렴", "specialty": "트렌디한 야식", "area": "홍대"},
        ],
        "accommodation": [
            {"name": "롯데호텔 서울", "type": "고급", "price": "350,000원~", "location": "명동", "features": "명동 중심, 최고급 시설"},
            {"name": "이비스 앰배서더", "type": "중급", "price": "100,000원~", "location": "홍대/명동/강남", "features": "위치 좋음, 합리적"},
            {"name": "홍대 게스트하우스", "type": "저렴", "price": "25,000원~", "location": "홍대", "features": "홍대 도보, 외국인 많음"},
        ],
        "transportation": {
            "김포공항→서울": {"공항철도": "30분, 9,000원", "택시": "30~40분, 30,000원~"},
            "인천공항→서울": {"공항철도": "50분, 9,500원", "리무진버스": "60~90분, 15,000원"},
            "현지교통": "지하철 매우 편리, T머니 교통카드 추천, 카카오T 앱으로 택시 이용",
        },
        "festivals": [
            {"name": "서울 벚꽃 축제", "month": "4월", "location": "여의도, 석촌호수", "desc": "벚꽃 명소 축제"},
            {"name": "서울 빛초롱 축제", "month": "11~12월", "location": "청계천", "desc": "겨울 빛 축제"},
            {"name": "서울 재즈페스티벌", "month": "5월", "location": "올림픽공원", "desc": "야외 재즈 공연"},
        ],
        "local_tips": [
            "T머니 교통카드로 지하철·버스 환승 할인",
            "경복궁은 화요일 휴관",
            "명동 면세점 방문 시 신분증 지참 필수",
            "카카오T 앱으로 택시 호출 편리",
            "한강공원 편의점에서 치킨·피자 배달 가능",
        ],
        "best_season": {
            "최적시기": "4~5월(봄), 9~11월(가을)",
            "봄": "벚꽃·튤립 축제, 야외 활동 최적",
            "여름": "장마·폭염, 실내 여행 위주",
            "가을": "단풍, 선선한 날씨",
            "겨울": "크리스마스 야경, 한파 주의",
            "tip": "봄·가을은 숙소 가격 높으니 미리 예약",
        },
    },
    "경주": {
        "attractions": {
            "자연": ["보문호", "토함산", "양동마을", "옥산서원"],
            "문화": ["불국사", "석굴암", "첨성대", "대릉원", "국립경주박물관", "황리단길"],
        },
        "restaurants": [
            {"name": "황리단길 카페", "cuisine": "카페/디저트", "price": "중급", "specialty": "황리단길 감성 카페", "area": "황리단길"},
            {"name": "성동시장 황남빵", "cuisine": "빵/디저트", "price": "저렴", "specialty": "경주 황남빵", "area": "성동시장"},
            {"name": "교촌마을 쌈밥", "cuisine": "한식", "price": "중급", "specialty": "전통 쌈밥 정식", "area": "교촌마을"},
            {"name": "경주 한우 식당", "cuisine": "고기", "price": "고급", "specialty": "경주 한우 구이", "area": "시내"},
        ],
        "accommodation": [
            {"name": "경주 힐튼", "type": "고급", "price": "200,000원~", "location": "보문관광단지", "features": "보문호 뷰, 골프장"},
            {"name": "보문 리조트", "type": "중급", "price": "90,000원~", "location": "보문", "features": "리조트 시설"},
            {"name": "경주 한옥 게스트하우스", "type": "저렴", "price": "40,000원~", "location": "황리단길 근처", "features": "한옥 체험"},
        ],
        "transportation": {
            "서울→경주": {"KTX": "2시간 10분, 49,900원 (신경주역)", "고속버스": "3시간 30분, 22,400원"},
            "부산→경주": {"일반열차": "1시간, 7,600원", "버스": "1시간 30분, 6,000원"},
            "현지교통": "자전거 대여 추천 (하루 5,000원), 버스도 편리, 주요 관광지 도보 가능",
        },
        "festivals": [
            {"name": "신라문화제", "month": "10월", "location": "경주 시내", "desc": "신라 역사 재현 축제"},
            {"name": "경주 벚꽃 마라톤", "month": "4월", "location": "보문호 일대", "desc": "벚꽃길 마라톤"},
        ],
        "local_tips": [
            "불국사·석굴암은 오전 일찍 방문 (오후에 관광객 증가)",
            "황리단길은 주말에 매우 혼잡, 평일 방문 추천",
            "경주 자전거 투어 코스 매우 잘 조성되어 있음",
            "황남빵은 성동시장에서 직접 구입이 저렴",
            "대릉원 야간 개방 시 분위기 특별함",
        ],
        "best_season": {
            "최적시기": "4~5월(봄), 10월(가을)",
            "봄": "벚꽃 명소, 야경 투어 인기",
            "여름": "덥지만 야간 관광 가능",
            "가을": "단풍과 문화재 조화, 신라문화제",
            "겨울": "한산하고 조용, 야경 아름다움",
            "tip": "황리단길은 주말 혼잡, 평일 방문 추천",
        },
    },
    "강릉": {
        "attractions": {
            "자연": ["경포해수욕장", "정동진", "순포습지", "안반데기"],
            "문화": ["오죽헌", "선교장", "강릉중앙시장", "강릉커피거리"],
        },
        "restaurants": [
            {"name": "초당순두부마을", "cuisine": "두부요리", "price": "저렴", "specialty": "강릉 초당순두부", "area": "초당동"},
            {"name": "강릉 장칼국수", "cuisine": "국수", "price": "저렴", "specialty": "장칼국수", "area": "시내"},
            {"name": "안목 커피거리", "cuisine": "커피", "price": "중급", "specialty": "바다 보며 커피", "area": "안목"},
            {"name": "주문진 횟집", "cuisine": "횟집", "price": "중급", "specialty": "신선한 회", "area": "주문진"},
        ],
        "accommodation": [
            {"name": "씨마크 호텔", "type": "고급", "price": "200,000원~", "location": "경포", "features": "오션뷰, 수영장"},
            {"name": "강릉 중급 호텔", "type": "중급", "price": "80,000원~", "location": "시내", "features": "시내 중심"},
            {"name": "경포 게스트하우스", "type": "저렴", "price": "30,000원~", "location": "경포", "features": "해변 도보"},
        ],
        "transportation": {
            "서울→강릉": {"KTX": "2시간 2분, 27,600원", "고속버스": "2시간 30분, 16,300원"},
            "현지교통": "버스 이용 가능하나 렌터카 편리, 자전거 대여도 좋음",
        },
        "festivals": [
            {"name": "강릉 단오제", "month": "음력 5월", "location": "강릉 시내", "desc": "유네스코 무형문화유산"},
            {"name": "강릉 커피축제", "month": "10월", "location": "안목해변", "desc": "국내 최대 커피 축제"},
        ],
        "local_tips": [
            "초당순두부는 아침 일찍 방문해야 줄이 짧음",
            "안목 커피거리는 일출 보며 커피 마시기 좋음",
            "정동진 일출은 새벽 5시 이전 도착 필수",
            "KTX 강릉역에서 시내버스로 주요 관광지 이동 가능",
        ],
        "best_season": {
            "최적시기": "6~8월(여름 해수욕), 9~10월(가을)",
            "봄": "벚꽃과 오죽헌 투어",
            "여름": "해수욕 최성수기",
            "가을": "단풍, 선선한 날씨",
            "겨울": "정동진 일출, 눈 설경",
            "tip": "여름 성수기 숙소 미리 예약 필수",
        },
    },
}


def get_city_key(city: str):
    """도시 이름으로 DB 키 찾기 (부분 일치)"""
    for key in CITY_DB:
        if key in city or city in key:
            return key
    return None


# ─────────────────────────────────────────────
# 7주차 함수 4개 (유지 + 개선)
# ─────────────────────────────────────────────

def get_weather(city: str, date: str = "today") -> dict:
    """Open-Meteo API로 실시간 날씨 조회 (무료, API 키 불필요)"""
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=ko"
        geo_res = requests.get(geo_url, timeout=5).json()
        if not geo_res.get("results"):
            return {"error": f"'{city}'를 찾을 수 없습니다."}
        loc = geo_res["results"][0]
        lat, lon = loc["latitude"], loc["longitude"]
        city_name = loc.get("name", city)

        weather_url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,weathercode,windspeed_10m,relative_humidity_2m,precipitation"
            f"&daily=temperature_2m_max,temperature_2m_min,weathercode"
            f"&timezone=Asia%2FSeoul&forecast_days=4"
        )
        data = requests.get(weather_url, timeout=5).json()
        cur = data["current"]
        daily = data.get("daily", {})

        weather_map = {
            0: "맑음 ☀️", 1: "대체로 맑음 🌤", 2: "구름 많음 ⛅", 3: "흐림 ☁️",
            51: "비 🌧", 53: "비 🌧", 61: "비 🌧", 63: "비 🌧", 65: "폭우 🌧",
            71: "눈 ❄️", 73: "눈 ❄️", 80: "소나기 🌦", 95: "뇌우 ⛈",
        }
        condition = weather_map.get(cur["weathercode"], "흐림 ☁️")
        temp = cur["temperature_2m"]

        if temp >= 28:   outfit = "반팔, 반바지, 선크림 필수"
        elif temp >= 20: outfit = "얇은 긴팔, 가디건"
        elif temp >= 12: outfit = "자켓, 긴바지"
        else:            outfit = "코트, 두꺼운 옷, 방한용품"

        forecast = []
        for i in range(min(3, len(daily.get("time", [])))):
            forecast.append({
                "날짜": daily["time"][i],
                "최고": f"{daily['temperature_2m_max'][i]}°C",
                "최저": f"{daily['temperature_2m_min'][i]}°C",
                "날씨": weather_map.get(daily["weathercode"][i], "흐림"),
            })

        return {
            "city": city_name,
            "현재날씨": condition,
            "현재기온": f"{temp}°C",
            "습도": f"{cur['relative_humidity_2m']}%",
            "풍속": f"{cur['windspeed_10m']} km/h",
            "옷차림": outfit,
            "우산여부": "우산 챙기세요! ☂️" if cur.get("precipitation", 0) > 0 else "우산 불필요 ✅",
            "3일예보": forecast,
        }
    except Exception as e:
        return {"city": city, "error": f"날씨 조회 실패: {str(e)}"}


def search_attractions(city: str, category: str = "전체") -> dict:
    """도시별 관광지 검색"""
    key = get_city_key(city)
    if not key:
        return {"error": f"'{city}' 정보 없음", "지원도시": list(CITY_DB.keys())}
    attractions = CITY_DB[key]["attractions"]
    result = attractions if category == "전체" else {category: attractions.get(category, [])}
    return {"city": key, "category": category, "관광지": result}


def calculate_budget(
    days: int,
    accommodation_type: str = "중급",
    meal_budget: str = "보통",
    transport: str = "대중교통",
) -> dict:
    """여행 예산 계산"""
    acc_map   = {"저렴": 40_000,  "중급": 100_000, "고급": 250_000}
    meal_map  = {"절약": 20_000,  "보통":  40_000,  "여유":  80_000}
    trans_map = {"대중교통": 15_000, "렌트카": 80_000, "택시": 50_000}

    nights   = max(days - 1, 0)
    acc      = acc_map.get(accommodation_type, 100_000) * nights
    meal     = meal_map.get(meal_budget, 40_000) * days
    trans    = trans_map.get(transport, 15_000) * days
    activity = 20_000 * days
    total    = acc + meal + trans + activity

    return {
        "여행일수": f"{days}일 ({nights}박)",
        "숙박비":   f"{acc:,}원  ({accommodation_type} · {nights}박)",
        "식비":     f"{meal:,}원  ({meal_budget} · {days}일)",
        "교통비":   f"{trans:,}원  ({transport} · {days}일)",
        "활동비":   f"{activity:,}원  ({days}일)",
        "총예산":   f"{total:,}원",
        "1일평균":  f"{total // days:,}원/일",
    }


def get_best_season(city: str) -> dict:
    """여행 최적 시기"""
    key = get_city_key(city)
    if not key:
        return {"city": city, "추천": "봄(4~5월)과 가을(9~10월)이 한국 여행 최적기입니다."}
    return {"city": key, **CITY_DB[key]["best_season"]}


# ─────────────────────────────────────────────
# 8주차 신규 함수 6개
# ─────────────────────────────────────────────

def search_restaurants(city: str, cuisine: str = "전체") -> dict:
    """맛집 검색"""
    key = get_city_key(city)
    if not key:
        return {"error": f"'{city}' 맛집 정보 없음"}
    restaurants = CITY_DB[key]["restaurants"]
    if cuisine != "전체":
        restaurants = [r for r in restaurants if cuisine in r["cuisine"]]
    return {"city": key, "맛집목록": restaurants, "총개수": len(restaurants)}


def search_accommodation(city: str, accommodation_type: str = "전체") -> dict:
    """숙소 추천"""
    key = get_city_key(city)
    if not key:
        return {"error": f"'{city}' 숙소 정보 없음"}
    accommodations = CITY_DB[key]["accommodation"]
    if accommodation_type != "전체":
        accommodations = [a for a in accommodations if a["type"] == accommodation_type]
    return {"city": key, "숙소목록": accommodations}


def get_transportation(destination: str, origin: str = "서울", transport_type: str = "전체") -> dict:
    """교통편 정보"""
    key = get_city_key(destination)
    if not key:
        return {"error": f"'{destination}' 교통 정보 없음"}
    trans_data = CITY_DB[key]["transportation"]
    route_key  = f"{origin}→{key}"
    route_info = trans_data.get(route_key, {k: v for k, v in trans_data.items() if "→" in k})
    return {
        "목적지":   key,
        "출발지":   origin,
        "교통편":   route_info,
        "현지교통": trans_data.get("현지교통", "정보 없음"),
    }


def get_local_tips(city: str) -> dict:
    """여행지 꿀팁"""
    key = get_city_key(city)
    if not key:
        return {"city": city, "꿀팁": ["여행 전 날씨 확인", "현지 교통수단 미리 파악", "숙소 사전 예약"]}
    return {"city": key, "꿀팁": CITY_DB[key]["local_tips"]}


def get_festivals(city: str, month: str = None) -> dict:
    """축제/행사 정보"""
    key = get_city_key(city)
    if not key:
        return {"city": city, "축제목록": []}
    festivals = CITY_DB[key]["festivals"]
    if month:
        festivals = [f for f in festivals if month in f["month"]]
    return {"city": key, "축제목록": festivals, "총개수": len(festivals)}


def create_itinerary(city: str, days: int, attractions: list = None, restaurants: list = None) -> dict:
    """날짜별 여행 일정표 생성"""
    key = get_city_key(city)
    if not key:
        return {"error": f"'{city}' 정보 없음"}

    db = CITY_DB[key]
    all_attractions = []
    for items in db["attractions"].values():
        all_attractions.extend(items)

    if not attractions:
        attractions = all_attractions
    if not restaurants:
        restaurants = [r["name"] for r in db["restaurants"]]

    schedule = {}
    for day in range(1, days + 1):
        idx     = (day - 1) * 2
        morning = attractions[idx]     if idx     < len(attractions) else "자유 일정"
        afternoon = attractions[idx+1] if idx + 1 < len(attractions) else "자유 탐방"
        lunch   = restaurants[(day - 1) % len(restaurants)]
        dinner  = restaurants[day % len(restaurants)] if len(restaurants) > 1 else restaurants[0]
        schedule[f"{day}일차"] = {
            "오전": morning,
            "점심": lunch,
            "오후": afternoon,
            "저녁": dinner,
        }

    return {"city": key, "총일수": f"{days}일", "일정표": schedule}


# ─────────────────────────────────────────────
# JSON 스키마 정의 (AI가 함수를 이해하는 설명서)
# ─────────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "특정 도시의 현재 날씨와 3일 예보를 조회합니다. 날씨·기온·우산 필요 여부를 물어볼 때 사용합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "날씨를 조회할 도시 (예: 제주, 부산, 서울)"},
                    "date": {"type": "string", "description": "조회 날짜 (today 또는 YYYY-MM-DD)", "default": "today"},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_attractions",
            "description": "도시의 관광지와 명소를 검색합니다. 어디 가면 좋을지, 볼거리를 물어볼 때 사용합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "관광지를 검색할 도시"},
                    "category": {"type": "string", "enum": ["자연", "문화", "전체"], "description": "관광지 카테고리", "default": "전체"},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_budget",
            "description": "여행 총 예산을 계산합니다. 비용이 얼마나 드는지 물어볼 때 사용합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "여행 일수 (2박3일이면 3, 3박4일이면 4)"},
                    "accommodation_type": {"type": "string", "enum": ["저렴", "중급", "고급"], "default": "중급"},
                    "meal_budget": {"type": "string", "enum": ["절약", "보통", "여유"], "default": "보통"},
                    "transport": {"type": "string", "enum": ["대중교통", "렌트카", "택시"], "default": "대중교통"},
                },
                "required": ["days"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_best_season",
            "description": "도시별 여행 최적 시기와 계절별 특징을 알려줍니다. 언제 가면 좋은지 물어볼 때 사용합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "여행 시기를 확인할 도시"},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_restaurants",
            "description": "도시의 맛집을 검색합니다. 어디서 밥 먹을지, 맛집 추천 부탁할 때 사용합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "맛집을 검색할 도시"},
                    "cuisine": {"type": "string", "description": "음식 종류 (전체, 해물, 카페, 국밥 등)", "default": "전체"},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_accommodation",
            "description": "숙소를 추천합니다. 어디서 잘지, 호텔·리조트·게스트하우스를 물어볼 때 사용합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "숙소를 찾을 도시"},
                    "accommodation_type": {"type": "string", "enum": ["전체", "저렴", "중급", "고급"], "default": "전체"},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_transportation",
            "description": "교통편 정보를 조회합니다. KTX·버스·비행기 등 이동 수단을 물어볼 때 사용합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {"type": "string", "description": "목적지 도시"},
                    "origin": {"type": "string", "description": "출발지 도시", "default": "서울"},
                    "transport_type": {"type": "string", "description": "교통수단 종류 (전체, KTX, 버스, 비행기)", "default": "전체"},
                },
                "required": ["destination"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_local_tips",
            "description": "여행지 꿀팁과 주의사항을 알려줍니다. 준비물, 알아두면 좋은 것을 물어볼 때 사용합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "꿀팁을 알고 싶은 도시"},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_festivals",
            "description": "축제와 행사 정보를 알려줍니다. 축제·이벤트·행사를 물어볼 때 사용합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "축제를 검색할 도시"},
                    "month": {"type": "string", "description": "특정 월 (예: 4월, 10월)", "default": None},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_itinerary",
            "description": "날짜별 여행 일정표를 만듭니다. 일정 짜줘, 스케줄 만들어줘 할 때 사용합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "여행 도시"},
                    "days": {"type": "integer", "description": "여행 일수"},
                    "attractions": {"type": "array", "items": {"type": "string"}, "description": "포함할 관광지 목록"},
                    "restaurants": {"type": "array", "items": {"type": "string"}, "description": "포함할 맛집 목록"},
                },
                "required": ["city", "days"],
            },
        },
    },
]


# ─────────────────────────────────────────────
# 함수 실행 디스패처
# ─────────────────────────────────────────────

TOOL_MAP = {
    "get_weather":          get_weather,
    "search_attractions":   search_attractions,
    "calculate_budget":     calculate_budget,
    "get_best_season":      get_best_season,
    "search_restaurants":   search_restaurants,
    "search_accommodation": search_accommodation,
    "get_transportation":   get_transportation,
    "get_local_tips":       get_local_tips,
    "get_festivals":        get_festivals,
    "create_itinerary":     create_itinerary,
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
