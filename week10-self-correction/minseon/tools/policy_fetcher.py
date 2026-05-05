"""
policy_fetcher.py
─────────────────
공공데이터포털 청년정책현황정보서비스 API → 정책 문서 자동 수집

API 등록: https://www.data.go.kr → "청년정책현황정보서비스" 검색 → 활용신청 (무료)
발급된 인증키를 .env의 PUBLIC_DATA_API_KEY에 입력

지역 코드표:
  003001 서울  003002 부산  003003 대구  003004 인천
  003005 광주  003006 대전  003007 울산  003008 세종
  003009 경기  003010 강원  003011 충북  003012 충남
  003013 전북  003014 전남  003015 경북  003016 경남
  003017 제주

분야 코드표:
  023001 일자리  023002 주거  023003 교육  023004 복지·문화  023005 참여·권리
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime

import requests

API_URL   = "https://apis.data.go.kr/1051000/YouthPolicyService1/getYouthPolicyList1"
DATA_DIR  = Path(__file__).parent / "data" / "fetched"

REGION_CODES: dict[str, str] = {
    "서울": "003001", "부산": "003002", "대구": "003003", "인천": "003004",
    "광주": "003005", "대전": "003006", "울산": "003007", "세종": "003008",
    "경기": "003009", "강원": "003010", "충북": "003011", "충남": "003012",
    "전북": "003013", "전남": "003014", "경북": "003015", "경남": "003016",
    "제주": "003017",
}

FIELD_CODES: dict[str, str] = {
    "일자리": "023001",
    "주거":   "023002",
    "교육":   "023003",
    "복지":   "023004",
    "참여":   "023005",
}

CATEGORY_MAP: dict[str, str] = {
    "023001": "취업",
    "023002": "주거",
    "023003": "장학금",
    "023004": "복지",
    "023005": "복지",
}


def _get_api_key() -> str | None:
    return os.getenv("PUBLIC_DATA_API_KEY", "").strip() or None


def fetch_raw(
    age: int | None = None,
    region: str | None = None,
    keyword: str = "",
    page: int = 1,
    display: int = 100,
) -> dict:
    """
    API 호출 후 raw JSON 반환.
    API 키가 없으면 빈 결과 반환.
    """
    api_key = _get_api_key()
    if not api_key:
        return {"totalCount": 0, "youthPolicyList": []}

    params: dict = {
        "openApiVlak": api_key,
        "display":     display,
        "pageIndex":   page,
        "type":        "json",
    }
    if age:
        params["age"] = age
    if keyword:
        params["keyword"] = keyword
    if region and region in REGION_CODES:
        params["district"] = REGION_CODES[region]

    try:
        resp = requests.get(API_URL, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[fetcher] API 오류: {e}")
        return {"totalCount": 0, "youthPolicyList": []}


def _policy_to_doc(policy: dict) -> dict:
    """API 응답의 정책 1개를 RAG용 dict로 변환."""
    name     = policy.get("polyNm", "").strip()
    intro    = policy.get("polyItcnCn", "").strip()
    benefit  = policy.get("sporScls", "").strip()
    qualify  = policy.get("prcpCn", "").strip()
    how      = policy.get("rqutProcCn", "").strip()
    age_info = policy.get("ageInfo", "").strip()
    region   = policy.get("sporCnCd", "").strip()
    start    = policy.get("aplySttDt", "").strip()
    end      = policy.get("aplyEndDt", "").strip()
    url      = policy.get("polyUrl", "").strip()
    dept     = policy.get("cnsgNmor", "").strip()
    field    = policy.get("polyBizSecd", "")

    period = ""
    if start and end:
        period = f"{start[:4]}.{start[4:6]}.{start[6:]} ~ {end[:4]}.{end[4:6]}.{end[6:]}"

    content = f"""# {name}

## 개요
{intro}

## 지원 내용
{benefit}

## 신청 자격
- 연령: {age_info}
- 지역: {region}
{qualify}

## 신청 방법
{how}

## 신청 기간
{period}

## 주관 기관
{dept}

## 참고 링크
{url}
""".strip()

    category = CATEGORY_MAP.get(field[:6], "기타")

    return {
        "title":    name,
        "content":  content,
        "source":   f"공공데이터포털_{name[:20]}.md",
        "category": category,
    }


def fetch_and_save(
    age: int | None = None,
    region: str | None = None,
    keyword: str = "",
    max_count: int = 200,
) -> list[dict]:
    """
    API에서 정책을 수집하고 DATA_DIR에 MD 파일로 저장한 뒤
    doc dict 목록을 반환합니다.
    """
    if not _get_api_key():
        print("[fetcher] PUBLIC_DATA_API_KEY 없음 — API 수집 건너뜀")
        return []

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    docs: list[dict] = []
    page   = 1
    total  = None

    print(f"[fetcher] 수집 시작: age={age}, region={region}, keyword='{keyword}'")

    while True:
        raw     = fetch_raw(age=age, region=region, keyword=keyword,
                            page=page, display=100)
        items   = raw.get("youthPolicyList") or []
        if total is None:
            total = int(raw.get("totalCount", 0))
            print(f"[fetcher] 총 {total}개 정책 발견")

        if not items:
            break

        for item in items:
            doc = _policy_to_doc(item)
            if not doc["title"]:
                continue
            docs.append(doc)

            # MD 파일 저장 (파일명에 사용 불가 문자 제거)
            safe_name = "".join(c for c in doc["title"] if c not in r'\/:*?"<>|')[:40]
            md_path   = DATA_DIR / f"{safe_name}.md"
            md_path.write_text(doc["content"], encoding="utf-8")

        print(f"[fetcher] 페이지 {page} 완료 — 누적 {len(docs)}개")

        if len(docs) >= max_count or len(docs) >= total:
            break

        page += 1
        time.sleep(0.3)   # API 부하 방지

    # 수집 메타 저장
    meta = {
        "fetched_at": datetime.now().isoformat(),
        "count":      len(docs),
        "age":        age,
        "region":     region,
        "keyword":    keyword,
    }
    (DATA_DIR / "_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"[fetcher] 완료: {len(docs)}개 저장 → {DATA_DIR}")
    return docs


def get_fetched_docs() -> list[dict]:
    """이미 수집된 MD 파일들을 dict로 로드합니다."""
    if not DATA_DIR.exists():
        return []

    docs: list[dict] = []
    seen: set[str]   = set()

    for md_file in sorted(DATA_DIR.glob("*.md")):
        try:
            content = md_file.read_text(encoding="utf-8")
            # 제목 추출
            title = ""
            for line in content.splitlines():
                if line.startswith("# "):
                    title = line[2:].strip()
                    break
            title = title or md_file.stem

            if title in seen:
                continue
            seen.add(title)

            docs.append({
                "title":    title,
                "content":  content,
                "source":   md_file.name,
                "category": _guess_category(content),
            })
        except Exception:
            continue

    return docs


def get_fetch_meta() -> dict | None:
    """마지막 수집 메타 정보 반환."""
    meta_path = DATA_DIR / "_meta.json"
    if not meta_path.exists():
        return None
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _guess_category(content: str) -> str:
    lower = content.lower()
    scores = {
        "장학금": sum(lower.count(k) for k in ["장학금", "학자금", "등록금", "교육비"]),
        "취업":   sum(lower.count(k) for k in ["취업", "일자리", "고용", "채용", "근로"]),
        "주거":   sum(lower.count(k) for k in ["주거", "월세", "전세", "청약", "주택"]),
        "금융":   sum(lower.count(k) for k in ["적금", "계좌", "저축", "대출"]),
        "복지":   sum(lower.count(k) for k in ["복지", "바우처", "수당"]),
    }
    return max(scores, key=lambda c: scores[c])


def has_api_key() -> bool:
    return bool(_get_api_key())
