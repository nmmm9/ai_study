"""
youthcenter_crawler.py
──────────────────────
온통청년 (youthcenter.go.kr) 청년정책 API 크롤러

API 엔드포인트: POST https://www.youthcenter.go.kr/pubot/search/portalPolicySearch
파라미터:
  - query       : 검색 키워드
  - pageNum     : 페이지 번호
  - listCount   : 페이지당 개수 (최대 100)
  - SPRT_TRGT_AGE : 지원 대상 나이
  - searchFields  : "all"
  - sortFields    : "" (최신순)
"""

import re
import json
import time
from datetime import datetime
from pathlib import Path

import requests


def _strip_html(text: str) -> str:
    """HTML 태그 제거."""
    return re.sub(r"<[^>]+>", "", text).strip()

DATA_DIR = Path(__file__).parent.parent / "data" / "youthcenter"

API_URL = "https://www.youthcenter.go.kr/pubot/search/portalPolicySearch"
HEADERS = {
    "User-Agent":   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Content-Type": "application/json;charset=UTF-8",
    "Referer":      "https://www.youthcenter.go.kr/youngMain.do",
    "Origin":       "https://www.youthcenter.go.kr",
}


def _build_payload(
    query: str = "",
    page: int = 1,
    count: int = 100,
    age: str = "",
) -> dict:
    return {
        "PLCY_KYWD_SN":       "",
        "PVSN_INST_GROUP_CD": "",
        "QLFC_ACBG_NM":       "",
        "SPCL_FLD_NM":        "",
        "SPRT_TRGT_AGE":      age,
        "STDG_NM":            "",
        "USER_LCLSF_NO":      "",
        "listCount":          count,
        "pageNum":            page,
        "query":              query,
        "searchFields":       "all",
        "sortFields":         "",
        "APLY_PRD_BGNG_YMD":  "",
        "APLY_PRD_END_YMD":   "",
        "APLY_PRD_SE_CD":     "",
        "EARN_MAX_AMT":       "",
        "EARN_MIN_AMT":       "",
        "EMPM_STTS_NM":       "",
        "MJR_CND_NM":         "",
        "MRG_STTS_CD":        "",
        "ODTM_CD":            "",
    }


def fetch_policies(
    query: str = "청년",
    age: str = "",
    max_count: int = 300,
) -> list[dict]:
    """
    온통청년 API에서 정책 목록을 가져옵니다.

    Args:
        query    : 검색 키워드
        age      : 나이 (예: "25")
        max_count: 최대 수집 개수

    Returns:
        정책 dict 목록
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    all_policies = []
    page = 1

    print(f"[youthcenter] 수집 시작: query='{query}', age={age or '전체'}")

    while len(all_policies) < max_count:
        payload = _build_payload(query=query, page=page, count=100, age=age)

        try:
            resp = requests.post(
                API_URL,
                json=payload,
                headers=HEADERS,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[youthcenter] 오류 (page={page}): {e}")
            break

        # 결과 추출: searchResult → youthpolicy (리스트)
        search_result = data.get("searchResult", {})
        youth_policy  = search_result.get("youthpolicy", [])
        items = youth_policy if isinstance(youth_policy, list) else []

        if not items:
            print(f"[youthcenter] 페이지 {page}: 데이터 없음 → 종료")
            break

        all_policies.extend(items)
        print(f"[youthcenter] 페이지 {page}: {len(items)}개 (누적 {len(all_policies)}개)")

        total = int(data.get("totalCount", 0) or len(items))
        if len(all_policies) >= int(total):
            break

        page += 1
        time.sleep(0.5)

    print(f"[youthcenter] 수집 완료: {len(all_policies)}개")
    return all_policies[:max_count]


def save_as_docs(raw_policies: list[dict]) -> list[dict]:
    """API 결과를 RAG용 MD 파일로 변환·저장합니다."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    docs = []
    seen: set[str] = set()

    for p in raw_policies:
        # 다양한 키 이름 대응
        name = _strip_html(
            p.get("polyNm") or p.get("PLCY_NM") or
            p.get("title")  or p.get("policyName") or ""
        )

        if not name or name in seen:
            continue
        seen.add(name)

        summary  = _strip_html(p.get("polyItcnCn") or p.get("PLCY_INTDC_CN") or p.get("summary") or "")
        benefit  = _strip_html(p.get("sporScls")   or p.get("SPRT_CN")       or p.get("benefit") or "")
        qualify  = _strip_html(p.get("prcpCn")     or p.get("PRCP_TRGT_CN")  or p.get("qualify") or "")
        age_info = _strip_html(p.get("ageInfo")    or p.get("SPRT_TRGT_AGE") or "")
        region   = _strip_html(p.get("sporCnCd")   or p.get("CTPVS_NM")      or "전국")
        url      = _strip_html(p.get("polyUrl")    or p.get("HMPG_URL")      or "")
        dept     = _strip_html(p.get("cnsgNmor")   or p.get("PVSN_INST_NM")  or "")

        md = f"""# {name}

## 개요
{summary}

## 지원 내용
{benefit}

## 신청 자격
- 연령: {age_info}
- 지역: {region}
{qualify}

## 주관 기관
{dept}

## 참고 링크
{url}

---
*수집일: {datetime.now().strftime('%Y-%m-%d')} (온통청년 API)*
""".strip()

        safe = re.sub(r'[\\/:*?"<>|]', "", name)[:40]
        path = DATA_DIR / f"{safe}.md"
        path.write_text(md, encoding="utf-8")

        docs.append({
            "title":    name,
            "content":  md,
            "source":   path.name,
            "category": _guess_category(summary + benefit + qualify),
        })

    print(f"[youthcenter] {len(docs)}개 MD 파일 저장 → {DATA_DIR}")
    return docs


def _guess_category(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["취업", "일자리", "고용", "채용", "인턴"]): return "취업"
    if any(k in t for k in ["주거", "월세", "전세", "청약", "주택"]):   return "주거"
    if any(k in t for k in ["장학", "학자금", "등록금", "교육"]):       return "장학금"
    if any(k in t for k in ["적금", "계좌", "금융", "대출"]):           return "금융"
    return "복지"


def get_saved_docs() -> list[dict]:
    """저장된 문서 로드."""
    if not DATA_DIR.exists():
        return []
    docs, seen = [], set()
    for f in sorted(DATA_DIR.glob("*.md")):
        try:
            content = f.read_text(encoding="utf-8")
            title   = next(
                (l[2:].strip() for l in content.splitlines() if l.startswith("# ")),
                f.stem,
            )
            if title not in seen:
                seen.add(title)
                docs.append({
                    "title": title, "content": content,
                    "source": f.name, "category": _guess_category(content),
                })
        except Exception:
            continue
    return docs


# ── 직접 실행 테스트 ─────────────────────────────────────────────
if __name__ == "__main__":
    raw  = fetch_policies(query="청년", max_count=500)
    docs = save_as_docs(raw)
    print(f"\n저장 완료: {len(docs)}개")
    if docs:
        print(f"첫 번째: {docs[0]['title']}")
