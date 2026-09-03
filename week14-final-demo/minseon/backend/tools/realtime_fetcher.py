"""
realtime_fetcher.py — 하이브리드 실시간 정책 수집기
─────────────────────────────────────────────────────
[Layer 1] 정부 RSS 피드 (스케줄 자동화, API 키 불필요)
  - 고용노동부 / 국토교통부 / 복지로 / 정책브리핑 / 교육부 / 중기부
  - 스케줄러가 4시간마다 수집 → 캐시 저장 → 신규 시 이메일 발송

[Layer 2] Tavily 실시간 보완 검색 (사용자 질문 트리거)
  - RSS에서 답을 못 찾거나, 사용자가 구체적 최신 정보를 요청할 때
  - 정부 도메인으로 범위 제한해 신뢰도 유지
  - 결과를 RSS 캐시와 병합하여 챗봇에 전달

.env:
  TAVILY_API_KEY=tvly-...   (선택. 없으면 RSS만 사용)
"""

import re
import json
import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Optional

from backend.logging_config import get_logger

logger = get_logger(__name__)

import requests

# ── 경로 ───────────────────────────────────────────────────────────
DATA_DIR   = Path(__file__).parent.parent.parent / "database" / "data" / "realtime"
CACHE_FILE = DATA_DIR / "rss_cache.json"       # RSS 수집 캐시
SEEN_FILE  = DATA_DIR / "_seen_ids.json"        # 신규 감지용 ID 저장

# ── 청년 필터 키워드 ────────────────────────────────────────────────
_YOUTH_KW = [
    "청년", "대학생", "취업", "청약", "임대주택", "장학금", "학자금",
    "신혼부부", "월세", "전세", "일자리", "고용", "인턴", "창업",
    "지원금", "바우처", "수당", "보조금", "혜택", "자립",
]

# ── 지역 별칭 ──────────────────────────────────────────────────────
_REGION_ALIAS: dict[str, list[str]] = {
    "서울": ["서울", "서울시", "서울특별시"],
    "부산": ["부산", "부산광역시"],
    "대구": ["대구", "대구광역시"],
    "인천": ["인천", "인천광역시"],
    "광주": ["광주", "광주광역시"],
    "대전": ["대전", "대전광역시"],
    "울산": ["울산"], "세종": ["세종"],
    "경기": ["경기", "경기도", "수원", "성남", "용인", "화성", "안양"],
    "강원": ["강원", "강원도"], "충북": ["충북", "충청북도", "청주"],
    "충남": ["충남", "충청남도", "천안"], "전북": ["전북", "전라북도", "전주"],
    "전남": ["전남", "전라남도"], "경북": ["경북", "경상북도", "포항"],
    "경남": ["경남", "경상남도", "창원"], "제주": ["제주"],
}

# ── 정부 공식 RSS 피드 목록 ────────────────────────────────────────
RSS_FEEDS = [
    {
        "name":     "정책브리핑",
        "url":      "https://www.korea.kr/rss/editorialNewsList.xml",
        "category": "기타",
    },
    {
        "name":     "고용노동부",
        "url":      "https://www.moel.go.kr/rss/newsList.do",
        "category": "취업",
    },
    {
        "name":     "국토교통부",
        "url":      "https://www.molit.go.kr/rss/USR_000007_P6.xml",
        "category": "주거",
    },
    {
        "name":     "복지로",
        "url":      "https://www.bokjiro.go.kr/ssis-tbu/twatbr/rss/selectTWABRRssInfo.do",
        "category": "복지",
    },
    {
        "name":     "교육부",
        "url":      "https://www.moe.go.kr/boardCnts/getRss.do?boardID=316&m=0301",
        "category": "장학금",
    },
    {
        "name":     "중소벤처기업부",
        "url":      "https://www.mss.go.kr/rss/pressNews.xml",
        "category": "창업",
    },
]

# ── Tavily 허용 도메인 화이트리스트 ───────────────────────────────

# 정부·공공기관 (기본 항상 허용)
_GOV_DOMAINS = [
    "gov.kr", "go.kr", "korea.kr",
    "youthcenter.go.kr", "moel.go.kr", "molit.go.kr",
    "mogef.go.kr", "mss.go.kr", "moe.go.kr",
    "nhis.or.kr", "hf.go.kr", "lh.or.kr", "hug.co.kr",
    "bokjiro.go.kr", "fss.or.kr",
]

# 금융기관 (금융 관련 질문 시 추가)
_FINANCE_DOMAINS = [
    # 1금융권 은행
    "shinhan.com",       # 신한은행
    "kbstar.com",        # KB국민은행
    "kebhana.com",       # KEB하나은행
    "wooribank.com",     # 우리은행
    "nonghyup.com",      # NH농협은행
    "ibk.co.kr",         # IBK기업은행
    "bnk.co.kr",         # BNK부산·경남은행
    "dgb.co.kr",         # DGB대구은행
    "jbbank.co.kr",      # 전북은행
    "scbank.co.kr",      # SC제일은행
    # 인터넷 전문은행
    "kakaobank.com",     # 카카오뱅크
    "tossbank.com",      # 토스뱅크
    "kbanknow.com",      # 케이뱅크
    # 공공 금융기관
    "kinfa.or.kr",       # 서민금융진흥원
    "kodit.or.kr",       # 신용보증기금
    "kibo.or.kr",        # 기술보증기금
    "semas.or.kr",       # 소상공인시장진흥공단
    "fine.fss.or.kr",    # 금융감독원 금융상품한눈에
    "nhuf.molit.go.kr",  # 국민주택기금
    "hf.go.kr",          # 한국주택금융공사
    "sbiz.or.kr",        # 소상공인진흥공단
]

# 금융 질문 트리거 키워드
_FINANCE_KEYWORDS = [
    "은행", "대출", "금리", "카드", "적금", "예금", "이자",
    "신용", "보증", "대환", "전세대출", "주담대", "모기지",
    "비교", "우대금리", "이율", "한도", "신청",
]

# 기본 화이트리스트 (gov only)
_TRUSTED_DOMAINS = _GOV_DOMAINS


def _build_domain_filter(query: str) -> list[str] | None:
    """
    질문에 금융 키워드가 포함되면 금융 도메인을 동적으로 추가.
    매우 구체적인 금융 상품 비교 질문이면 도메인 제한 해제(None).
    """
    q_lower = query.lower()
    matched = [kw for kw in _FINANCE_KEYWORDS if kw in q_lower]

    if not matched:
        return _GOV_DOMAINS  # 일반 질문: 정부 도메인만

    # 은행 비교 / 금리 비교처럼 상업 도메인이 꼭 필요한 경우
    needs_commercial = any(kw in q_lower for kw in ["은행 비교", "금리 비교", "어느 은행", "이율 비교"])
    if needs_commercial:
        logger.info(f"[domain_filter] 금융 비교 질문 → 도메인 제한 해제 (matched: {matched})")
        return None  # Tavily include_domains 파라미터 자체를 생략

    logger.info(f"[domain_filter] 금융 키워드 감지 → 금융 도메인 추가 (matched: {matched})")
    return list(set(_GOV_DOMAINS + _FINANCE_DOMAINS))


# ════════════════════════════════════════════════════════════════════
# Layer 1 — RSS 스케줄 수집
# ════════════════════════════════════════════════════════════════════

def _fetch_rss(feed: dict) -> list[dict]:
    try:
        resp = requests.get(
            feed["url"],
            headers={"User-Agent": "Mozilla/5.0 (YouthPolicyBot/1.0)"},
            timeout=10,
        )
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        root = ET.fromstring(resp.content)
    except Exception as e:
        logger.error(f"[realtime/rss] {feed['name']} 실패: {e}")
        return []

    items = []
    for item in root.iter("item"):
        title   = (item.findtext("title") or "").strip()
        link    = (item.findtext("link") or "").strip()
        desc    = (item.findtext("description") or "").strip()
        pub_raw = (item.findtext("pubDate") or "").strip()
        if not title or not link:
            continue

        pub_date = ""
        if pub_raw:
            try:
                pub_date = parsedate_to_datetime(pub_raw).strftime("%Y-%m-%d")
            except Exception:
                pub_date = pub_raw[:10]

        items.append({
            "title":    title,
            "link":     link,
            "desc":     re.sub(r"<[^>]+>", "", desc).strip(),
            "pub_date": pub_date,
            "source":   feed["name"],
            "category": feed["category"],
        })
    return items


def _is_youth_related(text: str) -> bool:
    return any(kw in text for kw in _YOUTH_KW)


def _item_to_doc(item: dict, layer: str = "rss") -> dict:
    title    = item["title"]
    desc     = item.get("desc", item.get("content", ""))
    link     = item.get("link") or item.get("url", "")
    pub_date = item.get("pub_date", "")
    source   = item.get("source", "")
    category = item.get("category", "기타")

    content = f"""# {title}

## 출처
{source}{f' ({pub_date})' if pub_date else ''}

## 내용
{desc or '(원문 링크 참조)'}

## 원문 링크
{link}
""".strip()

    uid = hashlib.md5(link.encode()).hexdigest()[:12]
    return {
        "id":       f"{layer}_{uid}",
        "title":    title,
        "content":  content,
        "source":   source,
        "category": category,
        "url":      link,
        "pub_date": pub_date,
        "layer":    layer,        # "rss" | "tavily"
        "fetched":  datetime.now().isoformat(),
    }


def collect_rss(youth_only: bool = True) -> list[dict]:
    """모든 RSS 피드를 수집하고 청년 관련 항목만 반환합니다."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    docs: list[dict] = []
    seen_links: set[str] = set()

    for feed in RSS_FEEDS:
        for item in _fetch_rss(feed):
            link = item["link"]
            if link in seen_links:
                continue
            text = item["title"] + " " + item["desc"]
            if youth_only and not _is_youth_related(text):
                continue
            seen_links.add(link)
            docs.append(_item_to_doc(item, layer="rss"))

    # 최신 날짜순 정렬
    docs.sort(key=lambda d: d.get("pub_date", ""), reverse=True)
    logger.info(f"[realtime/rss] 수집 완료: {len(docs)}건")
    return docs


def collect_rss_and_detect_new() -> list[dict]:
    """
    RSS를 수집하고 신규 항목만 반환 + 캐시 갱신.
    스케줄러가 4시간마다 호출합니다.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    seen: set[str] = set()
    if SEEN_FILE.exists():
        try:
            seen = set(json.loads(SEEN_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass

    all_docs = collect_rss()
    new_docs = [d for d in all_docs if d["id"] not in seen]

    if new_docs:
        seen.update(d["id"] for d in new_docs)
        SEEN_FILE.write_text(
            json.dumps(sorted(seen), ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # 캐시 갱신 (최대 300건)
    existing: list[dict] = []
    if CACHE_FILE.exists():
        try:
            existing = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    merged = new_docs + [e for e in existing if e["id"] not in {d["id"] for d in new_docs}]
    CACHE_FILE.write_text(
        json.dumps(merged[:300], ensure_ascii=False, indent=2), encoding="utf-8"
    )

    logger.info(f"[realtime/rss] 신규 {len(new_docs)}건 / 전체 캐시 {len(merged[:300])}건")
    return new_docs


_RSS_STOPWORDS = {"정책", "지원", "청년", "지원해줘", "알려줘", "관련", "있어", "뭐가", "나온", "관해서"}


def search_rss_cache(query: str = "", region: str = "", top_k: int = 5) -> list[dict]:
    """캐시된 RSS 항목을 키워드·지역으로 검색합니다."""
    if not CACHE_FILE.exists():
        return collect_rss()[:top_k]

    try:
        docs: list[dict] = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

    # "정책", "청년"처럼 거의 모든 캐시 문서에 들어있는 단어만으로는 매칭시키지 않는다.
    # (이 단어들만 겹쳐서 오래된 캐시가 "관련 있음"으로 잘못 걸리는 문제 방지)
    keywords = [kw for kw in query.lower().split() if kw not in _RSS_STOPWORDS]
    aliases  = _REGION_ALIAS.get(region, [region]) if region else []

    results = []
    for doc in docs:
        text = (doc.get("title", "") + " " + doc.get("content", "")).lower()
        region_ok  = (not aliases) or any(a in text for a in aliases)
        # 의미있는 키워드가 있으면 전부 일치해야 함(AND) — 느슨한 OR 매칭은 무관한 옛 캐시를 끌어옴
        keyword_ok = (not keywords) or all(kw in text for kw in keywords)
        if region_ok and keyword_ok:
            results.append(doc)

    return results[:top_k]


# ════════════════════════════════════════════════════════════════════
# Layer 2 — Tavily 실시간 보완 검색 (사용자 질문 트리거)
# ════════════════════════════════════════════════════════════════════

def _tavily_key() -> Optional[str]:
    from backend.config import settings
    return settings.tavily_api_key or None


def _tavily_search_raw(query: str, max_results: int = 5) -> list[dict]:
    """Tavily API 직접 호출 — 질문에 따라 도메인 필터 동적 적용."""
    key = _tavily_key()
    if not key:
        return []

    domains = _build_domain_filter(query)
    payload: dict = {
        "api_key":      key,
        "query":        query,
        "search_depth": "advanced",
        "max_results":  max_results,
    }
    if domains is not None:
        payload["include_domains"] = domains
    # domains가 None이면 include_domains 생략 → 전체 웹 검색

    try:
        resp = requests.post("https://api.tavily.com/search", json=payload, timeout=15)
        resp.raise_for_status()
        return resp.json().get("results", [])
    except Exception as e:
        logger.error(f"[realtime/tavily] 검색 오류: {e}")
        return []


def tavily_search(
    query: str,
    region: str = "",
    age: int = 0,
    max_results: int = 5,
) -> list[dict]:
    """
    Tavily로 보완 검색합니다.
    사용자가 구체적인 최신 정보를 요청할 때 tool_dispatcher에서 호출됩니다.
    """
    if not _tavily_key():
        logger.warning("[realtime/tavily] TAVILY_API_KEY 없음 — RSS 캐시만 사용")
        return search_rss_cache(query=query, region=region, top_k=max_results)

    # 쿼리 보강 (지역·나이 추가)
    enriched = query
    if region:
        enriched += f" {region}"
    if age:
        enriched += f" 만{age}세"
    enriched += " 청년 정책 지원"

    now = datetime.now()
    enriched += f" {now.year}년 {now.month}월"

    raw_results = _tavily_search_raw(enriched, max_results=max_results)

    docs = []
    for r in raw_results:
        doc = _item_to_doc(
            {
                "title":    r.get("title", "").strip(),
                "link":     r.get("url", ""),
                "desc":     r.get("content", "").strip(),
                "pub_date": "",
                "source":   "Tavily 실시간검색",
                "category": _guess_category(r.get("title", "") + " " + r.get("content", "")),
            },
            layer="tavily",
        )
        docs.append(doc)

    logger.info(f"[realtime/tavily] '{enriched[:40]}' → {len(docs)}건")
    return docs


_TEMPORAL_TRIGGERS = [
    "이번 달", "이번달", "이번 주", "이번주", "최근", "최신", "오늘",
    "방금", "요즘", "지금", "현재", "새로", "신규",
]


def is_temporal_query(query: str) -> bool:
    """질문이 '최신성'을 요구하는지 판단 — 이 경우 RSS 캐시만으로 답하면 안 되고 실시간 검색이 필요하다."""
    return any(kw in query for kw in _TEMPORAL_TRIGGERS)


def hybrid_search(
    query: str,
    region: str = "",
    age: int = 0,
    top_k: int = 5,
) -> list[dict]:
    """
    하이브리드 검색: RSS 캐시 우선 조회 → 결과 부족 시 Tavily 보완.
    "이번 달"/"최근"처럼 최신성이 중요한 질문은 캐시 매칭 개수와 무관하게
    항상 Tavily 실시간 검색도 함께 수행한다 (오래된 캐시가 우연히 키워드만
    겹쳐서 최신 답변인 것처럼 보이는 것을 방지).
    챗봇 tool_dispatcher에서 호출합니다.
    """
    rss_docs = search_rss_cache(query=query, region=region, top_k=top_k)
    force_web = is_temporal_query(query)

    if not force_web and len(rss_docs) >= top_k:
        logger.info(f"[realtime/hybrid] RSS 캐시로 충분: {len(rss_docs)}건")
        return rss_docs

    tavily_needed = max(top_k - len(rss_docs), top_k if force_web else 0)
    tavily_docs   = tavily_search(query=query, region=region, age=age, max_results=tavily_needed + 2)

    # 중복 URL 제거 후 병합. 최신성이 중요한 질문이면 Tavily(실시간) 결과를 우선 배치한다.
    seen_urls = {d["url"] for d in rss_docs}
    extra = [d for d in tavily_docs if d["url"] not in seen_urls]

    merged = (extra + rss_docs) if force_web else (rss_docs + extra)
    logger.info(f"[realtime/hybrid] RSS {len(rss_docs)}건 + Tavily {len(extra)}건 = {len(merged[:top_k])}건 (force_web={force_web})")
    return merged[:top_k]


# ── 유틸 ───────────────────────────────────────────────────────────

def _guess_category(text: str) -> str:
    t = text.lower()
    scores = {
        "주거":   sum(t.count(k) for k in ["주거", "임대", "청약", "전세", "월세", "주택"]),
        "취업":   sum(t.count(k) for k in ["취업", "일자리", "고용", "채용", "근로"]),
        "장학금": sum(t.count(k) for k in ["장학금", "학자금", "등록금", "교육비"]),
        "금융":   sum(t.count(k) for k in ["적금", "대출", "계좌", "저축"]),
        "복지":   sum(t.count(k) for k in ["복지", "바우처", "수당", "지원금"]),
        "창업":   sum(t.count(k) for k in ["창업", "스타트업", "벤처", "사업"]),
    }
    best = max(scores, key=lambda c: scores[c])
    return best if scores[best] > 0 else "기타"
