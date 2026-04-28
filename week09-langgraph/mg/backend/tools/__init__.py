# Import all tool modules to trigger registration
from tools import (
    # 8주차에서 가져온 26개
    delivery,
    lotto,
    fine_dust,
    han_river,
    kbo,
    kleague,
    spell_check,
    law_search,
    sillok,
    blue_ribbon,
    cheap_gas,
    real_estate,
    zipcode,
    weather_info,
    daiso,
    coupang,
    kakao_bar,
    olive_young,
    subway,
    used_car,
    lck,
    hwp,
    # 9주차 신규 14개 (k-skills 최신 동기화)
    korea_weather,
    naver_news,
    naver_shopping,
    korean_stock,
    parking_lot,
    household_waste,
    mfds_drug,
    mfds_food,
    library,
    lh_notice,
    school_meal,
    kbl,
    geeknews,
    char_count,
    # 9주차 추가 확장 10개 (50개 달성)
    library_extra,
    stock_extra,
    mfds_extra,
    lh_detail,
    gas_detail,
    korean_slang,
    real_estate_region,
)


# Domain mapping — 8개 도메인
TOOL_DOMAINS: dict[str, str] = {
    # ────── Shopping (8) ──────
    "daiso_search": "shopping",
    "daiso_pickup_stock": "shopping",
    "coupang_search": "shopping",
    "oliveyoung_store_search": "shopping",
    "oliveyoung_product_search": "shopping",
    "oliveyoung_inventory": "shopping",
    "used_car_price": "shopping",
    "naver_shopping_search": "shopping",

    # ────── Lifestyle (14) ──────
    "delivery_tracking": "lifestyle",
    "fine_dust": "lifestyle",
    "korea_weather": "lifestyle",
    "han_river_water_level": "lifestyle",
    "cheap_gas_nearby": "lifestyle",
    "cheap_gas_detail": "lifestyle",
    "real_estate_price": "lifestyle",
    "real_estate_region_code": "lifestyle",
    "zipcode_search": "lifestyle",
    "seoul_subway_arrival": "lifestyle",
    "blue_ribbon_nearby": "lifestyle",
    "kakao_bar_nearby": "lifestyle",
    "parking_lot_nearby": "lifestyle",
    "household_waste_info": "lifestyle",

    # ────── Sports (4) ──────
    "kbo_results": "sports",
    "kleague_results": "sports",
    "lck_results": "sports",
    "kbl_results": "sports",

    # ────── News (2) ──────
    "naver_news_search": "news",
    "geeknews_search": "news",

    # ────── Finance (3) ──────
    "korean_stock_search": "finance",
    "korean_stock_trade_info": "finance",
    "korean_stock_base_info": "finance",

    # ────── Government (6) ──────
    "mfds_drug_safety": "government",
    "mfds_food_safety": "government",
    "mfds_food_inspection_fail": "government",
    "mfds_food_recall": "government",
    "mfds_health_food_ingredient": "government",
    "lh_notice_search": "government",
    "lh_notice_detail": "government",

    # ────── Education (4) ──────
    "library_book_search": "education",
    "library_book_detail": "education",
    "library_search": "education",
    "library_libraries_by_book": "education",
    "school_meal": "education",

    # ────── Info (9) ──────
    "korean_spell_check": "info",
    "korean_character_count": "info",
    "korean_slang_lookup": "info",
    "korean_law_search": "info",
    "joseon_sillok_search": "info",
    "lotto_results": "info",
    "get_current_time": "info",
    "calculate": "info",
    "hwp_convert": "info",
}


def get_tools_for_domain(domain: str) -> list[str]:
    return [name for name, dom in TOOL_DOMAINS.items() if dom == domain]


DOMAINS = ["shopping", "lifestyle", "sports", "news", "finance", "government", "education", "info"]
