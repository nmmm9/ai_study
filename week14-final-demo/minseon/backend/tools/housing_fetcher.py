"""
housing_fetcher.py
──────────────────
LH(한국토지주택공사) + HUG(주택도시보증공사) API 연동
주택 청약·임대 공고를 수집하고 신규 공고를 감지합니다.

LH  API: https://openapi.lh.or.kr  (LH_SUPPLY_API_KEY)
HUG API: https://openapi.hug.co.kr (HUG_JEONSE_API_KEY / HUG_LEASE_API_KEY)

신규 공고 감지 방식:
  - 공고번호(PAN_NO / ANN_NO)를 _seen_ids.json에 저장
  - 다음 수집 시 새로운 ID가 있으면 신규 공고로 반환
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

import requests

from backend.config import settings
from backend.logging_config import get_logger
from backend.tools.attachment_parser import fetch_and_parse_attachment

logger = get_logger(__name__)

# ── 데이터 저장 경로 ───────────────────────────────────────────────
DATA_DIR  = Path(__file__).parent.parent.parent / "database" / "data" / "housing"
SEEN_FILE = DATA_DIR / "_seen_ids.json"

# ── LH OpenAPI 엔드포인트 ──────────────────────────────────────────
LH_BASE     = "https://openapi.lh.or.kr/openapi/service"
LH_RENT_URL = f"{LH_BASE}/LhRentAnncList"   # 임대주택 입주자 모집공고
LH_SALE_URL = f"{LH_BASE}/LhSaleAnncList"   # 분양(청약) 공고

# ── HUG OpenAPI 엔드포인트 ─────────────────────────────────────────
HUG_BASE      = "https://openapi.hug.co.kr/openapi/service"
HUG_JEONSE_URL = f"{HUG_BASE}/HugJeonsePriceInfo"  # 전세가격 정보
HUG_LEASE_URL  = f"{HUG_BASE}/HugLeaseAnncInfo"    # 전세임대 공고


# ── API 키 헬퍼 ────────────────────────────────────────────────────

def _lh_key() -> Optional[str]:
    return settings.lh_supply_api_key or None

def _hug_jeonse_key() -> Optional[str]:
    return settings.hug_jeonse_api_key or None

def _hug_lease_key() -> Optional[str]:
    return settings.hug_lease_api_key or None


# ── 공고 ID 영속성 ─────────────────────────────────────────────────

def _load_seen() -> set[str]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SEEN_FILE.exists():
        return set()
    try:
        return set(json.loads(SEEN_FILE.read_text(encoding="utf-8")))
    except Exception:
        return set()


def _save_seen(seen: set[str]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SEEN_FILE.write_text(
        json.dumps(sorted(seen), ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ── LH 임대주택 입주자 모집공고 ────────────────────────────────────

def _fetch_lh_rent(page: int = 1, count: int = 20) -> list[dict]:
    """LH 임대주택 입주자 모집공고 목록을 가져옵니다."""
    key = _lh_key()
    if not key:
        return []

    params = {
        "apiKey":   key,
        "PG_NUM":   page,
        "CNT":      count,
        "type":     "json",
    }
    try:
        resp = requests.get(LH_RENT_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("dsList") or data.get("data") or data.get("list") or []
    except requests.exceptions.HTTPError as e:
        logger.error(f"[housing] LH 임대공고 HTTP 오류: {e}")
        return []
    except Exception as e:
        logger.error(f"[housing] LH 임대공고 조회 실패: {e}")
        return []


def _lh_rent_to_doc(item: dict) -> dict:
    ann_no   = str(item.get("PAN_NO") or item.get("ANN_NO") or "")
    title    = item.get("PAN_NM") or item.get("ANN_NM") or "LH 임대주택 공고"
    region   = item.get("SUBSCRPT_AREA_CODE_NM") or item.get("AREA_NM") or ""
    address  = item.get("HSSPLY_ADRES") or item.get("ADRES") or ""
    units    = item.get("MDHSTL_UNIT_CNT") or item.get("UNIT_CNT") or ""
    start_dt = item.get("RCPT_BGDD") or item.get("START_DT") or ""
    end_dt   = item.get("RCPT_ENDDD") or item.get("END_DT") or ""
    ann_url  = item.get("PBLANC_URL") or item.get("ANN_URL") or "https://apply.lh.or.kr"
    house_tp = item.get("HOUSE_SECD_NM") or item.get("HOUSE_TP") or "임대주택"

    period = ""
    if start_dt and end_dt:
        period = f"{start_dt} ~ {end_dt}"
    elif start_dt:
        period = f"{start_dt} ~"

    content = f"""# [LH] {title}

## 공고 유형
{house_tp}

## 지역 / 주소
- 지역: {region}
- 주소: {address}

## 공급 세대수
{units}세대

## 청약 접수 기간
{period}

## 신청 방법
- LH 청약센터(apply.lh.or.kr) 또는 모바일 앱에서 온라인 신청
- 공고번호: {ann_no}

## 공고 링크
{ann_url}
""".strip()

    return {
        "id":       f"lh_rent_{ann_no}",
        "title":    f"[LH 임대] {title}",
        "content":  content,
        "source":   "LH한국토지주택공사",
        "category": "주거",
        "region":   region,
        "period":   period,
        "url":      ann_url,
        "type":     "임대",
        "fetched":  datetime.now().isoformat(),
    }


# ── LH 분양(청약) 공고 ─────────────────────────────────────────────

def _fetch_lh_sale(page: int = 1, count: int = 20) -> list[dict]:
    """LH 분양주택 청약 공고 목록을 가져옵니다."""
    key = _lh_key()
    if not key:
        return []

    params = {
        "apiKey": key,
        "PG_NUM": page,
        "CNT":    count,
        "type":   "json",
    }
    try:
        resp = requests.get(LH_SALE_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("dsList") or data.get("data") or data.get("list") or []
    except Exception as e:
        logger.error(f"[housing] LH 분양공고 조회 실패: {e}")
        return []


def _lh_sale_to_doc(item: dict) -> dict:
    ann_no  = str(item.get("PAN_NO") or item.get("ANN_NO") or "")
    title   = item.get("PAN_NM") or item.get("ANN_NM") or "LH 분양주택 공고"
    region  = item.get("SUBSCRPT_AREA_CODE_NM") or item.get("AREA_NM") or ""
    address = item.get("HSSPLY_ADRES") or item.get("ADRES") or ""
    units   = item.get("TOT_SUPLY_HSHLDCO") or item.get("UNIT_CNT") or ""
    start_dt = item.get("RCPT_BGDD") or item.get("START_DT") or ""
    end_dt   = item.get("RCPT_ENDDD") or item.get("END_DT") or ""
    ann_url  = item.get("PBLANC_URL") or item.get("ANN_URL") or "https://apply.lh.or.kr"
    price    = item.get("MIN_LTTOT_PRCE") or ""

    period = ""
    if start_dt and end_dt:
        period = f"{start_dt} ~ {end_dt}"

    content = f"""# [LH] {title}

## 공고 유형
분양(청약)

## 지역 / 주소
- 지역: {region}
- 주소: {address}

## 총 공급 세대수
{units}세대

## 분양 최저가
{price}

## 청약 접수 기간
{period}

## 신청 방법
- LH 청약센터(apply.lh.or.kr) 또는 모바일 앱에서 온라인 신청
- 청약홈(applyhome.co.kr) 확인
- 공고번호: {ann_no}

## 공고 링크
{ann_url}
""".strip()

    return {
        "id":       f"lh_sale_{ann_no}",
        "title":    f"[LH 분양] {title}",
        "content":  content,
        "source":   "LH한국토지주택공사",
        "category": "주거",
        "region":   region,
        "period":   period,
        "url":      ann_url,
        "type":     "분양",
        "fetched":  datetime.now().isoformat(),
    }


# ── HUG 전세임대 공고 ──────────────────────────────────────────────

def _fetch_hug_lease(page: int = 1, count: int = 20) -> list[dict]:
    """HUG 전세임대 공고를 가져옵니다."""
    key = _hug_lease_key()
    if not key:
        return []

    params = {
        "apiKey": key,
        "pageNo": page,
        "numOfRows": count,
        "type":   "json",
    }
    try:
        resp = requests.get(HUG_LEASE_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        items = (
            data.get("body", {}).get("items") or
            data.get("data") or
            data.get("list") or
            []
        )
        if isinstance(items, dict):
            items = items.get("item") or []
        return items if isinstance(items, list) else []
    except Exception as e:
        logger.error(f"[housing] HUG 전세임대 공고 조회 실패: {e}")
        return []


def _hug_lease_to_doc(item: dict) -> dict:
    ann_no  = str(item.get("ANN_NO") or item.get("annNo") or item.get("id") or "")
    title   = item.get("ANN_NM") or item.get("annNm") or item.get("title") or "HUG 전세임대 공고"
    region  = item.get("AREA_NM") or item.get("areaNm") or item.get("region") or ""
    start_dt = item.get("RCPT_BGN_DT") or item.get("startDt") or ""
    end_dt   = item.get("RCPT_END_DT") or item.get("endDt") or ""
    ann_url  = item.get("ANN_URL") or item.get("annUrl") or "https://www.hug.co.kr"
    target   = item.get("TRGET_NM") or item.get("target") or "청년/신혼부부"

    period = ""
    if start_dt and end_dt:
        period = f"{start_dt} ~ {end_dt}"

    content = f"""# [HUG] {title}

## 공고 유형
HUG 전세임대

## 신청 대상
{target}

## 지역
{region}

## 신청 접수 기간
{period}

## 신청 방법
- HUG 공식 홈페이지(www.hug.co.kr)에서 신청
- 공고번호: {ann_no}

## 공고 링크
{ann_url}
""".strip()

    return {
        "id":       f"hug_lease_{ann_no}",
        "title":    f"[HUG 전세임대] {title}",
        "content":  content,
        "source":   "HUG주택도시보증공사",
        "category": "주거",
        "region":   region,
        "period":   period,
        "url":      ann_url,
        "type":     "전세임대",
        "fetched":  datetime.now().isoformat(),
    }


# ── HUG 전세가격 정보 ─────────────────────────────────────────────

def _fetch_hug_jeonse(region_code: str = "", page: int = 1, count: int = 10) -> list[dict]:
    """HUG 전세가격 정보를 가져옵니다 (참고용)."""
    key = _hug_jeonse_key()
    if not key:
        return []

    params = {
        "apiKey":    key,
        "pageNo":    page,
        "numOfRows": count,
        "type":      "json",
    }
    if region_code:
        params["regionCode"] = region_code

    try:
        resp = requests.get(HUG_JEONSE_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("body", {}).get("items") or data.get("data") or []
        if isinstance(items, dict):
            items = items.get("item") or []
        return items if isinstance(items, list) else []
    except Exception as e:
        logger.error(f"[housing] HUG 전세가격 정보 조회 실패: {e}")
        return []


# ── 통합 수집 함수 ─────────────────────────────────────────────────

def enrich_announcement_with_attachment(doc: dict) -> dict:
    """
    공고 doc의 url이 실제로 PDF/HWPX 첨부파일을 가리키면 다운로드해 본문에
    상세 정보를 추가한다. url이 일반 안내 페이지(HTML)거나 다운로드가
    실패하면 doc을 그대로 반환한다 (원본 API가 상세 조건을 첨부파일에만
    담는 경우를 대비한 best-effort 보강이며, 실패해도 기존 요약 정보는 유지된다).
    """
    url = doc.get("url", "")
    extra = fetch_and_parse_attachment(url)
    if not extra:
        return doc
    doc = dict(doc)
    doc["content"] = doc["content"] + f"\n\n## 첨부파일 상세 정보\n{extra[:3000]}"
    return doc


def fetch_all_announcements(count: int = 20, with_attachments: bool = False) -> list[dict]:
    """
    LH + HUG 전체 공고를 수집하여 반환합니다.
    with_attachments=True면 각 공고의 첨부파일(PDF/HWPX)까지 다운로드해 본문을
    보강합니다 — 공고 수만큼 추가 네트워크 요청이 발생하므로 기본값은 False입니다.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    docs: list[dict] = []

    # LH 임대주택 공고
    lh_rent_items = _fetch_lh_rent(count=count)
    for item in lh_rent_items:
        doc = _lh_rent_to_doc(item)
        if doc["id"] != "lh_rent_":
            docs.append(doc)
    logger.info(f"[housing] LH 임대공고 {len(lh_rent_items)}건 수집")

    time.sleep(0.5)

    # LH 분양(청약) 공고
    lh_sale_items = _fetch_lh_sale(count=count)
    for item in lh_sale_items:
        doc = _lh_sale_to_doc(item)
        if doc["id"] != "lh_sale_":
            docs.append(doc)
    logger.info(f"[housing] LH 분양공고 {len(lh_sale_items)}건 수집")

    time.sleep(0.5)

    # HUG 전세임대 공고
    hug_items = _fetch_hug_lease(count=count)
    for item in hug_items:
        doc = _hug_lease_to_doc(item)
        if doc["id"] != "hug_lease_":
            docs.append(doc)
    logger.info(f"[housing] HUG 전세임대공고 {len(hug_items)}건 수집")

    if with_attachments:
        docs = [enrich_announcement_with_attachment(d) for d in docs]

    # 수집 결과를 JSON으로 저장
    if docs:
        cache_file = DATA_DIR / "announcements.json"
        cache_file.write_text(
            json.dumps(docs, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    return docs


def fetch_new_announcements() -> list[dict]:
    """
    전체 공고를 수집한 후 이전에 보지 못한 신규 공고만 반환합니다.
    스케줄러에서 주기적으로 호출하세요.
    """
    seen = _load_seen()
    all_docs = fetch_all_announcements()

    new_docs = [d for d in all_docs if d["id"] not in seen]

    if new_docs:
        seen.update(d["id"] for d in new_docs)
        _save_seen(seen)
        logger.info(f"[housing] 신규 공고 {len(new_docs)}건 감지")
    else:
        logger.warning("[housing] 신규 공고 없음")

    return new_docs


def get_cached_announcements(
    region: str = "",
    ann_type: str = "",   # "임대" | "분양" | "전세임대" | ""
    top_k: int = 10,
) -> list[dict]:
    """
    캐시된 공고를 지역/유형으로 필터링하여 반환합니다.
    챗봇 검색 시 호출합니다.
    """
    cache_file = DATA_DIR / "announcements.json"
    if not cache_file.exists():
        return []

    try:
        docs: list[dict] = json.loads(cache_file.read_text(encoding="utf-8"))
    except Exception:
        return []

    if region:
        docs = [d for d in docs if region in d.get("region", "")]
    if ann_type:
        docs = [d for d in docs if ann_type in d.get("type", "")]

    return docs[:top_k]


def search_housing_by_keyword(query: str, top_k: int = 5) -> list[dict]:
    """
    캐시된 공고를 키워드로 검색합니다.
    """
    cache_file = DATA_DIR / "announcements.json"
    if not cache_file.exists():
        return []

    try:
        docs: list[dict] = json.loads(cache_file.read_text(encoding="utf-8"))
    except Exception:
        return []

    keywords = query.lower().split()
    results = []
    for doc in docs:
        text = (doc.get("title", "") + " " + doc.get("content", "")).lower()
        if any(kw in text for kw in keywords):
            results.append(doc)

    return results[:top_k]


def has_any_key() -> bool:
    return bool(_lh_key() or _hug_jeonse_key() or _hug_lease_key())
