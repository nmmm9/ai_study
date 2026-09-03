"""
bokjiro_fetcher.py
──────────────────
한국사회보장정보원 복지서비스 API (지자체복지서비스 / 중앙부처복지서비스) → 정책 문서 자동 수집

API 등록: https://www.data.go.kr → "지자체복지서비스" / "중앙부처복지서비스" 검색 → 활용신청 (무료)
발급된 인증키를 .env의 BOKJORO_API_KEY에 입력

두 API는 같은 제공기관(B554287)이지만 오퍼레이션 경로·요청 파라미터·응답 필드명이
서로 다르다 (실제 호출로 확인함). 그래서 각각 별도 함수로 처리한다.

── 지자체복지서비스 (실제 호출로 확인 완료) ──────────────────────
목록조회: GET .../LocalGovernmentWelfareInformations/LcgvWelfarelist
  요청: serviceKey, pageNo, numOfRows
  응답(<servList> 반복): servId, servNm, servDgst, bizChrDeptNm, ctpvNm, sggNm,
    lifeNmArray, intrsThemaNmArray, aplyMtdNm, sprtCycNm, srvPvsnNm,
    servDtlLink, inqNum, lastModYmd
상세조회: GET .../LocalGovernmentWelfareInformations/LcgvWelfaredetailed
  요청: serviceKey, servId
  응답(<wantedDtl>): servId, servNm, bizChrDeptNm, ctpvNm, sggNm, enfcBgngYmd, enfcEndYmd,
    servDgst, sprtTrgtCn(지원대상), slctCritCn(선정기준), alwServCn(지원내용),
    aplyMtdNm, aplyMtdCn(신청방법 설명), lifeNmArray, trgterIndvdlNmArray, intrsThemaNmArray,
    inqplCtadrList/inqplHmpgReldList/baslawList/basfrmList (각 wlfareInfoDtlCd/
    wlfareInfoReldCn/wlfareInfoReldNm 반복 — basfrmList의 wlfareInfoReldCn이 첨부파일 URL)

── 중앙부처복지서비스 ────────────────────────────────────────────
목록조회(Swagger 실행으로 확인): GET .../NationalWelfareInformationsV001/NationalWelfarelistV001
  요청: serviceKey, callTp=L, pageNo, numOfRows, srchKeyCode, lifeArray, trgterIndvdlArray,
        intrsThemaArray, age, onapPsbltYn, orderBy
  응답(<servList> 반복): servId, servNm, servDgst, jurMnofNm, jurOrgNm, lifeArray,
    trgterIndvdlArray, intrsThemaArray, onapPsbltYn, servDtlLink, sprtCycNm, srvPvsnNm,
    svcfrstRegTs, inqNum
상세조회: NationalWelfaredetailedV001 + callTp=D — 실제 수집 테스트에서 슬롯이 채워지는 것을
  확인함(예: 청년내일저축계좌 지원 조건이 실제로 반환됨). 다만 사전 문서화(Swagger/참고문서)로
  직접 대조 확인한 것은 아니라서, 필드명이 지자체와 동일한지(slctCritCn 등)는 이 방식으로만 검증됨.
"""

import time
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime

import requests

from backend.config import settings
from backend.logging_config import get_logger

logger = get_logger(__name__)

# 지자체복지서비스 (실제 호출로 확인됨)
LOCAL_BASE_URL   = "https://apis.data.go.kr/B554287/LocalGovernmentWelfareInformations"
LOCAL_LIST_URL   = f"{LOCAL_BASE_URL}/LcgvWelfarelist"
LOCAL_DETAIL_URL = f"{LOCAL_BASE_URL}/LcgvWelfaredetailed"

# 중앙부처복지서비스 (목록조회는 Swagger, 상세조회는 실제 수집 테스트로 확인됨)
CENTRAL_BASE_URL   = "https://apis.data.go.kr/B554287/NationalWelfareInformationsV001"
CENTRAL_LIST_URL   = f"{CENTRAL_BASE_URL}/NationalWelfarelistV001"
CENTRAL_DETAIL_URL = f"{CENTRAL_BASE_URL}/NationalWelfaredetailedV001"  # 실제 수집 테스트로 동작 확인됨

DATA_DIR = Path(__file__).parent.parent.parent / "database" / "data" / "fetched"

# data.go.kr 응답이 종종 느려서(수 초~수십 초) 넉넉하게 잡는다.
_TIMEOUT = 30


def _get_api_key() -> str | None:
    return settings.bokjoro_api_key or None


def _parse_xml_items(xml_text: str, item_tag: str) -> tuple[list[dict], dict]:
    """XML 응답을 파싱해 item_tag 반복 요소들과 결과 메타(resultCode 등)를 반환."""
    root = ET.fromstring(xml_text)
    items = []
    for el in root.findall(item_tag):
        item = {child.tag: (child.text or "").strip() for child in el}
        items.append(item)

    meta = {
        "resultCode":    (root.findtext("resultCode") or "").strip(),
        "resultMessage": (root.findtext("resultMessage") or "").strip(),
        "totalCount":    (root.findtext("totalCount") or "0").strip(),
    }
    return items, meta


def _parse_xml_detail(xml_text: str) -> dict:
    """상세조회 응답(<wantedDtl>)을 평면 dict + 반복 리스트 필드로 변환."""
    root = ET.fromstring(xml_text)
    detail: dict = {}
    repeated: dict[str, list[dict]] = {}
    for child in root:
        if len(child) == 0:
            detail[child.tag] = (child.text or "").strip()
        else:
            sub = {c.tag: (c.text or "").strip() for c in child}
            repeated.setdefault(child.tag, []).append(sub)
    detail["_repeated"] = repeated
    return detail


# ════════════════════════════════════════════════════════════════
# 지자체복지서비스
# ════════════════════════════════════════════════════════════════

def fetch_local_list_raw(page: int = 1, num_of_rows: int = 100) -> tuple[list[dict], dict]:
    """지자체복지서비스 목록조회. 키 없거나 오류 시 빈 리스트 반환."""
    api_key = _get_api_key()
    if not api_key:
        return [], {"resultCode": "-1", "resultMessage": "API 키 없음", "totalCount": "0"}

    params = {"serviceKey": api_key, "pageNo": page, "numOfRows": num_of_rows}
    try:
        resp = requests.get(LOCAL_LIST_URL, params=params, timeout=_TIMEOUT)
        resp.raise_for_status()
        return _parse_xml_items(resp.text, "servList")
    except Exception as e:
        logger.error(f"[bokjiro] 지자체 목록조회 오류: {e}")
        return [], {"resultCode": "-1", "resultMessage": str(e), "totalCount": "0"}


def fetch_local_detail_raw(serv_id: str) -> dict | None:
    """지자체복지서비스 상세조회 (servId 기준 단건)."""
    api_key = _get_api_key()
    if not api_key:
        return None

    params = {"serviceKey": api_key, "servId": serv_id}
    try:
        resp = requests.get(LOCAL_DETAIL_URL, params=params, timeout=_TIMEOUT)
        resp.raise_for_status()
        return _parse_xml_detail(resp.text)
    except Exception as e:
        logger.error(f"[bokjiro] 지자체 상세조회 오류 (servId={serv_id}): {e}")
        return None


def _local_item_to_doc(item: dict, detail: dict | None) -> dict:
    """지자체 목록조회 항목(+선택적 상세조회)을 RAG용 doc dict로 변환."""
    name    = item.get("servNm", "").strip()
    summary = item.get("servDgst", "").strip()
    dept    = item.get("bizChrDeptNm", "").strip()
    ctpv    = item.get("ctpvNm", "").strip()
    sgg     = item.get("sggNm", "").strip()
    life    = item.get("lifeNmArray", "").strip()
    theme   = item.get("intrsThemaNmArray", "").strip()
    cycle   = item.get("sprtCycNm", "").strip()
    method  = item.get("srvPvsnNm", "").strip()
    apply_m = item.get("aplyMtdNm", "").strip()
    url     = item.get("servDtlLink", "").strip()

    eligibility = ""
    benefit     = ""
    apply_how   = ""
    attach_links: list[str] = []
    target      = ""
    if detail:
        eligibility = detail.get("slctCritCn", "") or detail.get("sprtTrgtCn", "")
        benefit     = detail.get("alwServCn", "")
        apply_how   = detail.get("aplyMtdCn", "")
        target      = detail.get("trgterIndvdlNmArray", "")
        for row in detail.get("_repeated", {}).get("basfrmList", []):
            link = row.get("wlfareInfoReldCn", "")
            label = row.get("wlfareInfoReldNm", "첨부파일")
            if link:
                attach_links.append(f"- [{label}]({link})")

    region = " ".join(p for p in [ctpv, sgg] if p and p != "-")

    content = f"""# {name}

## 개요
{summary}

## 지원 대상
- 지역: {region or '전국(지자체 무관)'}
- 생애주기: {life}
- 대상 특성: {target}
- 관심 주제: {theme}

## 신청 자격
{eligibility or "(상세 조건은 아래 참고 링크에서 확인)"}

## 지원 내용
{benefit or f"제공 방식: {method} / 지원 주기: {cycle}"}

## 신청 방법
{apply_how or apply_m or "관할 기관에 문의"}

## 소관 기관
{dept}

## 첨부파일
{chr(10).join(attach_links) if attach_links else "(없음)"}

## 참고 링크
{url}
""".strip()

    return {
        "title":    name,
        "content":  content,
        "source":   f"지자체복지서비스_{name[:20]}.md",
        "category": _guess_category(theme, life),
    }


def fetch_local_and_save(max_count: int = 100, with_detail: bool = True, youth_only: bool = True) -> list[dict]:
    """
    지자체복지서비스 수집 → MD 저장 → doc dict 목록 반환.
    youth_only=True면 응답의 lifeNmArray에 "청년"이 포함된 항목만 남긴다.
    """
    if not _get_api_key():
        logger.warning("[bokjiro] BOKJORO_API_KEY 없음 — 지자체 수집 건너뜀")
        return []

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    docs: list[dict] = []
    page, total = 1, None

    logger.info("[bokjiro] 지자체복지서비스 수집 시작")

    while True:
        items, meta = fetch_local_list_raw(page=page, num_of_rows=100)

        if meta.get("resultCode") not in ("0", ""):
            logger.error(f"[bokjiro] 지자체 API 오류: {meta.get('resultMessage')}")
            break

        if total is None:
            total = int(meta.get("totalCount") or 0)
            logger.info(f"[bokjiro] 지자체복지서비스 총 {total}건 발견")

        if not items:
            break

        for item in items:
            if youth_only and "청년" not in item.get("lifeNmArray", ""):
                continue

            serv_id = item.get("servId", "")
            detail  = fetch_local_detail_raw(serv_id) if (with_detail and serv_id) else None
            if with_detail and serv_id:
                time.sleep(0.2)

            doc = _local_item_to_doc(item, detail)
            if not doc["title"]:
                continue
            docs.append(doc)

            safe_name = "".join(c for c in doc["title"] if c not in r'\/:*?"<>|')[:40]
            (DATA_DIR / f"{safe_name}.md").write_text(doc["content"], encoding="utf-8")

        logger.info(f"[bokjiro] 지자체복지서비스 페이지 {page} 완료 — 누적 {len(docs)}건")

        if len(docs) >= max_count or page * 100 >= total:
            break

        page += 1
        time.sleep(0.3)

    logger.info(f"[bokjiro] 지자체복지서비스 완료: {len(docs)}건 저장 → {DATA_DIR}")
    return docs


# ════════════════════════════════════════════════════════════════
# 중앙부처복지서비스
# ════════════════════════════════════════════════════════════════

def fetch_central_list_raw(
    page: int = 1,
    num_of_rows: int = 100,
    age: int | None = None,
    order_by: str = "popular",
) -> tuple[list[dict], dict]:
    """중앙부처복지서비스 목록조회 (Swagger 실행으로 확인된 파라미터)."""
    api_key = _get_api_key()
    if not api_key:
        return [], {"resultCode": "-1", "resultMessage": "API 키 없음", "totalCount": "0"}

    params = {
        "serviceKey":  api_key,
        "callTp":      "L",
        "srchKeyCode": "001",
        "pageNo":      page,
        "numOfRows":   num_of_rows,
        "orderBy":     order_by,
    }
    if age is not None:
        params["age"] = age

    try:
        resp = requests.get(CENTRAL_LIST_URL, params=params, timeout=_TIMEOUT)
        resp.raise_for_status()
        return _parse_xml_items(resp.text, "servList")
    except Exception as e:
        logger.error(f"[bokjiro] 중앙부처 목록조회 오류: {e}")
        return [], {"resultCode": "-1", "resultMessage": str(e), "totalCount": "0"}


def fetch_central_detail_raw(serv_id: str) -> dict | None:
    """중앙부처복지서비스 상세조회 — 경로/파라미터 미검증(추정치)."""
    api_key = _get_api_key()
    if not api_key:
        return None

    params = {"serviceKey": api_key, "callTp": "D", "servId": serv_id}
    try:
        resp = requests.get(CENTRAL_DETAIL_URL, params=params, timeout=_TIMEOUT)
        resp.raise_for_status()
        return _parse_xml_detail(resp.text)
    except Exception as e:
        logger.error(f"[bokjiro] 중앙부처 상세조회 오류 (servId={serv_id}): {e}")
        return None


def _central_item_to_doc(item: dict, detail: dict | None) -> dict:
    name    = item.get("servNm", "").strip()
    summary = item.get("servDgst", "").strip()
    dept    = item.get("jurMnofNm", "").strip()
    org     = item.get("jurOrgNm", "").strip()
    life    = item.get("lifeArray", "").strip()
    target  = item.get("trgterIndvdlArray", "").strip()
    theme   = item.get("intrsThemaArray", "").strip()
    cycle   = item.get("sprtCycNm", "").strip()
    method  = item.get("srvPvsnNm", "").strip()
    online  = item.get("onapPsbltYn", "").strip()
    url     = item.get("servDtlLink", "").strip()

    eligibility = ""
    benefit     = ""
    if detail:
        eligibility = detail.get("slctCritCn", "") or detail.get("tgtrDtlCn", "")
        benefit     = detail.get("alwServCn", "")

    content = f"""# {name}

## 개요
{summary}

## 지원 대상
- 생애주기: {life}
- 대상 특성: {target}
- 관심 주제: {theme}

## 신청 자격
{eligibility or "(상세 조건은 아래 참고 링크에서 확인)"}

## 지원 내용
{benefit or f"제공 방식: {method} / 지원 주기: {cycle}"}

## 신청 방법
{"온라인 신청 가능" if online == "Y" else "관할 기관에 문의"}

## 소관 기관
{dept} {org}

## 참고 링크
{url}
""".strip()

    return {
        "title":    name,
        "content":  content,
        "source":   f"중앙부처복지서비스_{name[:20]}.md",
        "category": _guess_category(theme, life),
    }


def fetch_central_and_save(age: int = 25, max_count: int = 100, with_detail: bool = True, youth_only: bool = True) -> list[dict]:
    """중앙부처복지서비스 수집 → MD 저장 → doc dict 목록 반환."""
    if not _get_api_key():
        logger.warning("[bokjiro] BOKJORO_API_KEY 없음 — 중앙부처 수집 건너뜀")
        return []

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    docs: list[dict] = []
    page, total = 1, None

    logger.info("[bokjiro] 중앙부처복지서비스 수집 시작")

    while True:
        items, meta = fetch_central_list_raw(page=page, num_of_rows=100, age=age)

        if meta.get("resultCode") not in ("0", ""):
            logger.error(f"[bokjiro] 중앙부처 API 오류: {meta.get('resultMessage')}")
            break

        if total is None:
            total = int(meta.get("totalCount") or 0)
            logger.info(f"[bokjiro] 중앙부처복지서비스 총 {total}건 발견")

        if not items:
            break

        for item in items:
            if youth_only and "청년" not in item.get("lifeArray", ""):
                continue

            serv_id = item.get("servId", "")
            detail  = fetch_central_detail_raw(serv_id) if (with_detail and serv_id) else None
            if with_detail and serv_id:
                time.sleep(0.2)

            doc = _central_item_to_doc(item, detail)
            if not doc["title"]:
                continue
            docs.append(doc)

            safe_name = "".join(c for c in doc["title"] if c not in r'\/:*?"<>|')[:40]
            (DATA_DIR / f"{safe_name}.md").write_text(doc["content"], encoding="utf-8")

        logger.info(f"[bokjiro] 중앙부처복지서비스 페이지 {page} 완료 — 누적 {len(docs)}건")

        if len(docs) >= max_count or (total and page * 100 >= total):
            break

        page += 1
        time.sleep(0.3)

    logger.info(f"[bokjiro] 중앙부처복지서비스 완료: {len(docs)}건 저장 → {DATA_DIR}")
    return docs


def _guess_category(theme: str, life: str) -> str:
    text = f"{theme} {life}"
    scores = {
        "장학금":   sum(text.count(k) for k in ["교육", "학자금"]),
        "취업":     sum(text.count(k) for k in ["일자리", "고용", "취업"]),
        "주거":     sum(text.count(k) for k in ["주거", "주택"]),
        "복지":     sum(text.count(k) for k in ["생활지원", "저소득", "복지"]),
        "신체건강": sum(text.count(k) for k in ["신체건강", "임신", "출산", "의료"]),
        "마음건강": sum(text.count(k) for k in ["마음건강", "정신"]),
    }
    best = max(scores, key=lambda c: scores[c])
    return best if scores[best] > 0 else "생활지원"


def has_api_key() -> bool:
    return bool(_get_api_key())


if __name__ == "__main__":
    # 빠른 연결 테스트: python -m backend.tools.bokjiro_fetcher
    print("=== 지자체복지서비스 ===")
    items, meta = fetch_local_list_raw(page=1, num_of_rows=5)
    print("META:", meta)
    for it in items[:3]:
        print("-", it.get("servNm"), "|", it.get("servId"), "|", it.get("lifeNmArray"))

    print("\n=== 중앙부처복지서비스 ===")
    items2, meta2 = fetch_central_list_raw(page=1, num_of_rows=5, age=25)
    print("META:", meta2)
    for it in items2[:3]:
        print("-", it.get("servNm"), "|", it.get("servId"), "|", it.get("lifeArray"))
