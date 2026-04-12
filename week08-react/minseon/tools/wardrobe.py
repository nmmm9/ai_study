"""옷장 관리 모듈 - wardrobe.json에서 아이템을 로드하고 필터링합니다."""

import json
import os
from typing import Optional


# wardrobe.json 파일 경로 (이 파일 기준 상위 디렉토리)
_WARDROBE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wardrobe.json")

_wardrobe_cache: Optional[list] = None


def load_wardrobe() -> list:
    """옷장 데이터를 로드합니다. 캐시가 있으면 캐시를 반환합니다."""
    global _wardrobe_cache
    if _wardrobe_cache is not None:
        return _wardrobe_cache

    if not os.path.exists(_WARDROBE_PATH):
        return []

    with open(_WARDROBE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    _wardrobe_cache = data.get("items", [])
    return _wardrobe_cache


def filter_wardrobe(
    category: Optional[str] = None,
    season: Optional[str] = None,
    weather: Optional[str] = None,
    style: Optional[str] = None,
    color: Optional[str] = None,
) -> list:
    """조건에 맞는 옷장 아이템을 필터링합니다.

    Args:
        category: 카테고리 (상의, 하의, 아우터, 신발, 액세서리)
        season: 계절 (봄, 여름, 가을, 겨울)
        weather: 날씨 조건 (맑음, 흐림, 비, 눈)
        style: 스타일 키워드
        color: 색상 이름

    Returns:
        필터링된 아이템 리스트
    """
    items = load_wardrobe()
    result = []

    for item in items:
        # 카테고리 필터
        if category and item.get("category") != category:
            continue

        # 계절 필터
        if season and season not in item.get("season", []):
            continue

        # 날씨 조건 필터
        if weather and weather not in item.get("weather_condition", []):
            continue

        # 스타일 필터
        if style and style not in item.get("style", []):
            continue

        # 색상 필터
        if color and item.get("color") != color:
            continue

        result.append(item)

    return result


def get_wardrobe_summary() -> dict:
    """옷장 전체 요약 정보를 반환합니다."""
    items = load_wardrobe()

    summary = {
        "total": len(items),
        "by_category": {},
        "by_color": {},
    }

    for item in items:
        cat = item.get("category", "기타")
        summary["by_category"][cat] = summary["by_category"].get(cat, 0) + 1

        color = item.get("color", "unknown")
        summary["by_color"][color] = summary["by_color"].get(color, 0) + 1

    return summary


def add_item(item: dict) -> bool:
    """새 아이템을 옷장에 추가합니다."""
    global _wardrobe_cache

    required_fields = ["id", "name", "category", "color", "style", "season", "weather_condition"]
    for field in required_fields:
        if field not in item:
            return False

    items = load_wardrobe()

    # 중복 ID 확인
    existing_ids = {i["id"] for i in items}
    if item["id"] in existing_ids:
        return False

    items.append(item)
    _wardrobe_cache = items

    with open(_WARDROBE_PATH, "w", encoding="utf-8") as f:
        json.dump({"items": items}, f, ensure_ascii=False, indent=2)

    return True


def remove_item(item_id: str) -> bool:
    """아이템을 옷장에서 제거합니다."""
    global _wardrobe_cache

    items = load_wardrobe()
    new_items = [i for i in items if i["id"] != item_id]

    if len(new_items) == len(items):
        return False  # 해당 ID 없음

    _wardrobe_cache = new_items

    with open(_WARDROBE_PATH, "w", encoding="utf-8") as f:
        json.dump({"items": new_items}, f, ensure_ascii=False, indent=2)

    return True
