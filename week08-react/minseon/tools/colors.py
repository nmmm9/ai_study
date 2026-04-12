"""색상 조합 이론 모듈 - 색채학 기반 어울리는 색상 조합을 제공합니다."""

from typing import Optional

# 색상별 어울리는 조합 데이터
# 보색, 유사색, 중성색, 트렌디 조합으로 분류
COLOR_PAIRINGS: dict[str, dict] = {
    "white": {
        "korean_name": "화이트",
        "tone": "light",
        "combinations": ["black", "navy", "gray", "beige", "light_blue", "sage", "dusty_rose"],
        "description": "모든 색상과 잘 어울리는 완벽한 베이직. 특히 네이비, 블랙과 클래식한 조합 연출.",
        "avoid": [],
    },
    "black": {
        "korean_name": "블랙",
        "tone": "dark",
        "combinations": ["white", "gray", "beige", "camel", "burgundy", "red", "cream"],
        "description": "모든 색상과 어울리는 가장 강력한 베이직. 포인트 컬러와 매칭하면 세련된 룩 완성.",
        "avoid": ["dark_gray", "charcoal"],
    },
    "navy": {
        "korean_name": "네이비",
        "tone": "dark",
        "combinations": ["white", "cream", "beige", "light_blue", "red", "tan", "camel"],
        "description": "클래식하고 세련된 색상. 화이트와 마린룩, 베이지와 클래식룩 연출 가능.",
        "avoid": ["black", "dark_gray"],
    },
    "gray": {
        "korean_name": "그레이",
        "tone": "neutral",
        "combinations": ["white", "black", "navy", "burgundy", "yellow", "pink", "light_blue"],
        "description": "어떤 색상과도 무난하게 어울리는 중성 색상. 포인트 컬러와 함께 활용 추천.",
        "avoid": [],
    },
    "beige": {
        "korean_name": "베이지",
        "tone": "neutral",
        "combinations": ["white", "brown", "camel", "navy", "black", "tan", "cream", "sage"],
        "description": "따뜻하고 내추럴한 색상. 어스톤 계열과 조화롭고 블랙으로 포인트 가능.",
        "avoid": ["light_yellow", "cream"],
    },
    "blue": {
        "korean_name": "블루",
        "tone": "medium",
        "combinations": ["white", "navy", "gray", "beige", "brown", "orange", "cream"],
        "description": "청바지 기준의 블루는 모든 색상과 잘 어울림. 화이트와 깔끔한 캐주얼룩 연출.",
        "avoid": ["green", "purple"],
    },
    "light_blue": {
        "korean_name": "하늘색",
        "tone": "light",
        "combinations": ["white", "navy", "beige", "cream", "gray", "tan"],
        "description": "상큼하고 청량한 색상. 화이트/베이지와 봄여름 룩, 네이비와 마린룩 연출.",
        "avoid": ["green", "yellow"],
    },
    "brown": {
        "korean_name": "브라운",
        "tone": "warm",
        "combinations": ["beige", "cream", "camel", "tan", "white", "orange", "rust"],
        "description": "따뜻하고 포근한 어스톤 계열. 같은 계열끼리 어스톤 코디, 화이트와 캐주얼룩.",
        "avoid": ["navy", "blue", "green"],
    },
    "camel": {
        "korean_name": "카멜",
        "tone": "warm",
        "combinations": ["white", "black", "navy", "brown", "beige", "cream", "burgundy"],
        "description": "가을/겨울 시즌에 특히 활용도 높은 색상. 블랙과 세련된 조합, 화이트와 우아한 룩.",
        "avoid": ["yellow", "orange"],
    },
    "cream": {
        "korean_name": "크림",
        "tone": "light",
        "combinations": ["brown", "camel", "tan", "navy", "burgundy", "sage"],
        "description": "화이트보다 따뜻한 느낌의 색상. 브라운 계열과 내추럴룩, 네이비와 클래식룩.",
        "avoid": ["white", "yellow"],
    },
    "burgundy": {
        "korean_name": "버건디",
        "tone": "dark",
        "combinations": ["black", "gray", "camel", "cream", "beige", "white"],
        "description": "가을/겨울 트렌드 컬러. 블랙과 세련된 다크룩, 카멜과 가을 느낌 연출.",
        "avoid": ["navy", "red", "brown"],
    },
    "khaki": {
        "korean_name": "카키",
        "tone": "neutral",
        "combinations": ["white", "beige", "brown", "black", "orange", "tan"],
        "description": "밀리터리 느낌의 중성적 색상. 화이트/베이지와 내추럴룩, 블랙과 스트릿룩.",
        "avoid": ["gray", "light_blue"],
    },
    "sage": {
        "korean_name": "세이지",
        "tone": "light",
        "combinations": ["white", "cream", "beige", "tan", "brown", "black"],
        "description": "트렌디한 자연 그린 색상. 크림/베이지와 내추럴룩, 화이트와 봄여름 룩.",
        "avoid": ["navy", "burgundy"],
    },
    "tan": {
        "korean_name": "탄",
        "tone": "warm",
        "combinations": ["white", "navy", "beige", "brown", "cream", "black"],
        "description": "밝은 브라운 계열의 따뜻한 색상. 대부분의 색상과 잘 어울리는 만능 컬러.",
        "avoid": ["yellow", "orange"],
    },
    "light_gray": {
        "korean_name": "연회색",
        "tone": "light",
        "combinations": ["white", "black", "navy", "pink", "burgundy", "light_blue"],
        "description": "그레이보다 밝고 부드러운 느낌. 다양한 컬러와 잘 어울리는 경량 중성색.",
        "avoid": ["beige", "cream"],
    },
    "dark_gray": {
        "korean_name": "다크그레이",
        "tone": "dark",
        "combinations": ["black", "gray", "sage", "blue", "mustard", "dark_brown"],
        "description": "ColorHunt 실제 데이터 기반 조합. 상위 6개 색상과 잘 어울림.",
        "avoid": ["dusty_rose", "olive", "pink"],
    },
    "mint": {
        "korean_name": "민트",
        "tone": "light",
        "combinations": ["black", "dark_gray", "gray", "camel", "peach"],
        "description": "ColorHunt 실제 데이터 기반 조합. 상위 6개 색상과 잘 어울림.",
        "avoid": ["khaki", "dusty_rose", "olive"],
    },
    "sand": {
        "korean_name": "샌드",
        "tone": "neutral",
        "combinations": ["camel", "peach"],
        "description": "ColorHunt 실제 데이터 기반 조합. 상위 6개 색상과 잘 어울림.",
        "avoid": ["khaki", "dusty_rose", "olive"],
    },
    "peach": {
        "korean_name": "피치",
        "tone": "light",
        "combinations": ["camel", "sage", "pink", "khaki", "hot_pink", "blue"],
        "description": "ColorHunt 실제 데이터 기반 조합. 상위 6개 색상과 잘 어울림.",
        "avoid": ["dusty_rose", "olive", "purple"],
    },
    "hot_pink": {
        "korean_name": "핫핑크",
        "tone": "dark",
        "combinations": ["pink", "peach", "cream", "navy", "beige", "ivory"],
        "description": "ColorHunt 실제 데이터 기반 조합. 상위 6개 색상과 잘 어울림.",
        "avoid": ["khaki", "olive", "brown"],
    },
    "pink": {
        "korean_name": "핑크",
        "tone": "light",
        "combinations": ["peach", "hot_pink", "cream", "lavender", "beige", "light_blue"],
        "description": "ColorHunt 실제 데이터 기반 조합. 상위 6개 색상과 잘 어울림.",
        "avoid": ["khaki", "dusty_rose", "olive"],
    },
    "mustard": {
        "korean_name": "머스타드",
        "tone": "medium",
        "combinations": ["dark_brown", "dark_gray", "peach", "blue", "navy", "green"],
        "description": "ColorHunt 실제 데이터 기반 조합. 상위 6개 색상과 잘 어울림.",
        "avoid": ["dusty_rose", "olive", "pink"],
    },
    "lavender": {
        "korean_name": "라벤더",
        "tone": "light",
        "combinations": ["pink", "beige", "mustard", "coral", "red", "dark_gray"],
        "description": "ColorHunt 실제 데이터 기반 조합. 상위 6개 색상과 잘 어울림.",
        "avoid": ["khaki", "dusty_rose", "olive"],
    },
    "red": {
        "korean_name": "레드",
        "tone": "dark",
        "combinations": ["coral", "ivory", "sky_blue", "blue", "gold", "burgundy"],
        "description": "ColorHunt 실제 데이터 기반 조합. 상위 6개 색상과 잘 어울림.",
        "avoid": ["khaki", "olive", "pink"],
    },
    "ivory": {
        "korean_name": "아이보리",
        "tone": "light",
        "combinations": ["red", "sky_blue", "blue", "navy", "hot_pink", "beige"],
        "description": "ColorHunt 실제 데이터 기반 조합. 상위 6개 색상과 잘 어울림.",
        "avoid": ["olive", "pink", "purple"],
    },
    "sky_blue": {
        "korean_name": "스카이블루",
        "tone": "light",
        "combinations": ["red", "ivory", "blue", "peach", "coral", "gold"],
        "description": "ColorHunt 실제 데이터 기반 조합. 상위 6개 색상과 잘 어울림.",
        "avoid": ["khaki", "dusty_rose", "olive"],
    },
    "dark_brown": {
        "korean_name": "다크브라운",
        "tone": "dark",
        "combinations": ["khaki", "mustard", "dark_gray", "dusty_rose", "ivory", "black"],
        "description": "ColorHunt 실제 데이터 기반 조합. 상위 6개 색상과 잘 어울림.",
        "avoid": ["olive", "pink", "purple"],
    },
    "dusty_rose": {
        "korean_name": "더스티로즈",
        "tone": "light",
        "combinations": ["cream", "dark_brown", "khaki", "ivory", "coral", "red"],
        "description": "ColorHunt 실제 데이터 기반 조합. 상위 6개 색상과 잘 어울림.",
        "avoid": ["olive", "pink", "brown"],
    },
    "green": {
        "korean_name": "그린",
        "tone": "medium",
        "combinations": ["gray", "mustard", "cream"],
        "description": "ColorHunt 실제 데이터 기반 조합. 상위 6개 색상과 잘 어울림.",
        "avoid": ["khaki", "dusty_rose", "olive"],
    },
    "coral": {
        "korean_name": "코랄",
        "tone": "medium",
        "combinations": ["blue", "red", "beige", "gold", "dark_gray", "sky_blue"],
        "description": "ColorHunt 실제 데이터 기반 조합. 상위 6개 색상과 잘 어울림.",
        "avoid": ["khaki", "olive", "pink"],
    },
    "gold": {
        "korean_name": "골드",
        "tone": "warm",
        "combinations": ["coral", "blue", "red", "beige", "sky_blue"],
        "description": "ColorHunt 실제 데이터 기반 조합. 상위 6개 색상과 잘 어울림.",
        "avoid": ["khaki", "dusty_rose", "olive"],
    },
    "royal_blue": {
        "korean_name": "로얄블루",
        "tone": "dark",
        "combinations": ["blue", "khaki", "peach"],
        "description": "ColorHunt 실제 데이터 기반 조합. 상위 6개 색상과 잘 어울림.",
        "avoid": ["dusty_rose", "olive", "pink"],
    },
    "purple": {
        "korean_name": "퍼플",
        "tone": "dark",
        "combinations": ["cream", "dusty_rose", "hot_pink"],
        "description": "ColorHunt 실제 데이터 기반 조합. 상위 6개 색상과 잘 어울림.",
        "avoid": ["khaki", "olive", "pink"],
    },
}

# 계절별 추천 색상 팔레트
SEASONAL_PALETTES: dict[str, dict] = {
    "봄": {
        "core_colors": ["white", "light_blue", "sage", "cream", "tan"],
        "accent_colors": ["dusty_rose", "yellow", "lavender"],
        "description": "파스텔 톤과 밝은 색상으로 상큼한 봄 분위기 연출",
    },
    "여름": {
        "core_colors": ["white", "light_blue", "beige", "navy"],
        "accent_colors": ["red", "yellow", "coral"],
        "description": "시원한 색상과 대비가 선명한 컬러로 여름 활력 표현",
    },
    "가을": {
        "core_colors": ["camel", "burgundy", "brown", "khaki", "beige"],
        "accent_colors": ["rust", "mustard", "forest_green"],
        "description": "어스톤과 딥 컬러로 풍성한 가을 무드 연출",
    },
    "겨울": {
        "core_colors": ["black", "gray", "navy", "cream", "camel"],
        "accent_colors": ["burgundy", "red", "royal_blue"],
        "description": "다크 컬러와 중성색으로 세련된 겨울 룩 완성",
    },
}


def get_color_combinations(color: str) -> dict:
    """특정 색상과 어울리는 색상 조합 정보를 반환합니다.

    Args:
        color: 기준 색상 (예: white, black, navy, beige 등)

    Returns:
        색상 조합 정보 딕셔너리
    """
    color_lower = color.lower().replace(" ", "_")

    if color_lower in COLOR_PAIRINGS:
        info = COLOR_PAIRINGS[color_lower].copy()
        info["queried_color"] = color_lower
        info["found"] = True
        return info

    # 부분 일치 검색
    for key, val in COLOR_PAIRINGS.items():
        if color_lower in key or key in color_lower:
            result = val.copy()
            result["queried_color"] = color_lower
            result["matched_to"] = key
            result["found"] = True
            return result

    # 찾지 못한 경우 - 기본 중성색 조합 반환
    return {
        "queried_color": color,
        "found": False,
        "combinations": ["white", "black", "gray", "beige", "navy"],
        "description": f"'{color}' 색상 정보를 찾을 수 없어 기본 중성색 조합을 제안합니다.",
        "tip": "중성색(화이트, 블랙, 그레이, 베이지, 네이비)은 어떤 색상과도 무난하게 어울립니다.",
    }


def get_seasonal_palette(season: str) -> dict:
    """계절별 추천 색상 팔레트를 반환합니다."""
    # 봄/가을 처리
    if "봄" in season and "가을" in season:
        spring = SEASONAL_PALETTES.get("봄", {})
        autumn = SEASONAL_PALETTES.get("가을", {})
        return {
            "season": season,
            "spring": spring,
            "autumn": autumn,
            "recommendation": "현재 기온에 맞는 계절을 선택하거나 두 계절의 색상을 믹스하세요.",
        }

    for key in SEASONAL_PALETTES:
        if key in season:
            return {"season": key, **SEASONAL_PALETTES[key]}

    return {
        "season": season,
        "note": "계절 팔레트 정보를 찾을 수 없습니다.",
        "recommendation": "베이직 컬러(화이트, 블랙, 네이비)를 중심으로 코디하세요.",
    }


def is_good_combination(color1: str, color2: str) -> tuple[bool, str]:
    """두 색상의 조합이 좋은지 판단합니다.

    Returns:
        (is_good, reason) 튜플
    """
    c1 = color1.lower().replace(" ", "_")
    c2 = color2.lower().replace(" ", "_")

    info1 = COLOR_PAIRINGS.get(c1, {})
    info2 = COLOR_PAIRINGS.get(c2, {})

    # c2가 c1의 추천 조합에 있는 경우
    if c2 in info1.get("combinations", []):
        return True, f"{color1}과(와) {color2}는 잘 어울리는 조합입니다."

    # c2가 c1의 피해야 할 조합에 있는 경우
    if c2 in info1.get("avoid", []):
        return False, f"{color1}과(와) {color2}는 어울리지 않는 조합입니다."

    # 둘 다 중성색인 경우
    neutral_colors = {"white", "black", "gray", "beige", "navy", "cream", "light_gray"}
    if c1 in neutral_colors or c2 in neutral_colors:
        return True, f"중성색이 포함되어 무난하게 어울립니다."

    return True, "일반적으로 어울리는 조합입니다."
