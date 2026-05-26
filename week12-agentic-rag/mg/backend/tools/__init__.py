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
    # 12주차 Agentic RAG — 문서 검색
    document_search,
    # 12주차 확장 — k-skills 88개 동기화 후 신규 11개
    kakao_geocode,
    kosis_stats,
    kstartup,
    nts_business,
    seoul_density,
    # 12주차 전면 통합 — k-skills 88개 그대로 반영 (인증 필요한 것 제외)
    daangn,           # 4 tools
    shopping_extra,   # 4 tools (danawa×2, kurly, ohou)
    gov_extra,        # 5 tools (emergency, sh, court, election, donation)
    transport,        # 5 tools (express, intercity, terminal, forest, transit)
    finance_extra,    # 4 tools (k_dart×3, daishin)
    culture,          # 3 tools (cinema, marathon, ticket)
    misc_skills,      # 8 tools (gangnamunni, blog×2, restroom, gongsijiga, patent, scholarship, lost)
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

    # ────── Lifestyle (15) ──────
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
    "kakao_geocode": "lifestyle",

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

    # ────── Government (13) ──────
    "mfds_drug_safety": "government",
    "mfds_food_safety": "government",
    "mfds_food_inspection_fail": "government",
    "mfds_food_recall": "government",
    "mfds_health_food_ingredient": "government",
    "lh_notice_search": "government",
    "lh_notice_detail": "government",
    "kstartup_announcements": "government",
    "kstartup_business_info": "government",
    "kstartup_contents": "government",
    "kstartup_statistics": "government",
    "nts_business_status": "government",
    "nts_business_validate": "government",

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
    "date_arithmetic": "info",
    "hwp_convert": "info",

    # ────── Documents (2) — 12주차 Agentic RAG ──────
    "document_search": "documents",
    "list_uploaded_documents": "documents",

    # ────── Data (4) — 12주차 확장 ──────
    "kosis_search": "data",
    "kosis_meta": "data",
    "kosis_data": "data",
    "seoul_density": "data",

    # ────── Shopping 추가 (12) — 당근 + 다나와/컬리/오집 ──────
    "daangn_used_goods_search": "shopping",
    "daangn_cars_search": "shopping",
    "daangn_jobs_search": "shopping",
    "daangn_realty_search": "shopping",
    "danawa_price_search": "shopping",
    "danawa_price_compare": "shopping",
    "market_kurly_search": "shopping",
    "ohou_today_deal": "shopping",

    # ────── Government 추가 — 응급실/SH/법원/선거/기부 ──────
    "emergency_room_beds": "government",
    "sh_notice_search": "government",
    "court_auction_search": "government",
    "local_election_candidate_search": "government",
    "donation_place_search": "government",

    # ────── Travel (신규 도메인) — 교통/예약 ──────
    "express_bus_search": "travel",
    "intercity_bus_search": "travel",
    "bus_terminal_list": "travel",
    "foresttrip_vacancy": "travel",
    "korean_transit_route": "travel",

    # ────── Finance 추가 — DART / 대신증권 ──────
    "k_dart_search_disclosure": "finance",
    "k_dart_company_info": "finance",
    "k_dart_financial": "finance",
    "daishin_report_search": "finance",

    # ────── Culture (신규 도메인) — 영화/마라톤/티켓 ──────
    "korean_cinema_search": "culture",
    "korean_marathon_schedule": "culture",
    "ticket_availability": "culture",

    # ────── Health (신규 도메인) — 강남언니 / 응급실은 government ──────
    "gangnamunni_clinic_search": "health",

    # ────── News 추가 — 네이버 블로그 ──────
    "naver_blog_search": "news",
    "naver_blog_read": "news",

    # ────── Lifestyle 추가 — 화장실/공시지가 ──────
    "public_restroom_nearby": "lifestyle",
    "gongsijiga_search": "lifestyle",

    # ────── Info 추가 — 특허 / 장학금 / 분실물 ──────
    "korean_patent_search": "info",
    "korean_scholarship_search": "info",
    "subway_lost_property": "info",
}


def get_tools_for_domain(domain: str) -> list[str]:
    return [name for name, dom in TOOL_DOMAINS.items() if dom == domain]


DOMAINS = ["shopping", "lifestyle", "sports", "news", "finance", "government",
           "education", "info", "documents", "data", "travel", "culture", "health"]
