"""
youth_crawler.py
────────────────
온통청년 (youthcenter.go.kr) 정책 크롤러

실행:
    python tools/youth_crawler.py
"""

import time
import json
import re
from pathlib import Path
from datetime import datetime

import requests
from bs4 import BeautifulSoup

DATA_DIR = Path(__file__).parent / "data" / "crawled"
HEADERS  = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    )
}

# 온통청년 정책 목록 API (내부 JSON API)
LIST_API  = "https://www.youthcenter.go.kr/go/idsvc/mobileApi/getPolicyList.json"
# 또는 서버사이드 렌더링 목록 페이지
LIST_PAGE = "https://www.youthcenter.go.kr/youngMain.do"


def crawl_policy_list(max_page: int = 5) -> list[dict]:
    """
    정책 목록 페이지를 크롤링합니다.
    JSON API → HTML 파싱 순으로 시도합니다.
    """
    policies = []

    # ── 방법 1: JSON API 시도 ────────────────────────────────
    print("[crawler] JSON API 시도 중...")
    for page in range(1, max_page + 1):
        try:
            resp = requests.get(
                LIST_API,
                params={"pageIndex": page, "pageSize": 10, "srchType": ""},
                headers=HEADERS,
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                items = (
                    data.get("result")
                    or data.get("list")
                    or data.get("policyList")
                    or data.get("data")
                    or []
                )
                if not items:
                    break
                policies.extend(items)
                print(f"  페이지 {page}: {len(items)}개")
                time.sleep(0.5)
            else:
                break
        except Exception:
            break

    if policies:
        print(f"[crawler] JSON API 성공: 총 {len(policies)}개")
        return policies

    # ── 방법 2: HTML 파싱 ────────────────────────────────────
    print("[crawler] HTML 파싱 시도 중...")
    try:
        resp = requests.get(LIST_PAGE, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        # 가능한 정책 카드 셀렉터들 시도
        selectors = [
            "li.policy-item", "div.policy-card", "ul.policy-list li",
            "div.list-item", "li.lst_item", "div.card-item",
            "li.item", "div.policy_item", "div.policy-wrap li",
        ]
        items_found = []
        for sel in selectors:
            items_found = soup.select(sel)
            if items_found:
                print(f"  '{sel}' 으로 {len(items_found)}개 발견")
                break

        for item in items_found:
            title_tag = (
                item.select_one("strong, h3, h4, .title, .tit, .name")
                or item.select_one("a")
            )
            desc_tag  = item.select_one("p, .desc, .summary, .con")
            link_tag  = item.select_one("a[href]")

            policies.append({
                "title":   title_tag.get_text(strip=True) if title_tag else "",
                "summary": desc_tag.get_text(strip=True)  if desc_tag  else "",
                "url":     link_tag["href"]                if link_tag  else "",
            })

    except Exception as e:
        print(f"[crawler] HTML 파싱 실패: {e}")

    return policies


def save_as_docs(raw_policies: list[dict]) -> list[dict]:
    """크롤링 결과를 RAG용 MD 파일로 저장합니다."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    docs = []

    for p in raw_policies:
        # 다양한 키 이름 대응
        name = (
            p.get("polyNm") or p.get("title") or
            p.get("name")   or p.get("policyName") or ""
        ).strip()
        summary = (
            p.get("polyItcnCn") or p.get("summary") or
            p.get("description") or ""
        ).strip()
        benefit = (p.get("sporScls") or p.get("benefit") or "").strip()
        qualify = (p.get("prcpCn")   or p.get("qualify") or "").strip()
        age     = (p.get("ageInfo")  or p.get("age")     or "").strip()
        region  = (p.get("sporCnCd") or p.get("region")  or "").strip()
        url     = (p.get("polyUrl")  or p.get("url")     or "").strip()

        if not name:
            continue

        md = f"""# {name}

## 개요
{summary}

## 지원 내용
{benefit}

## 신청 자격
- 연령: {age}
- 지역: {region}
{qualify}

## 참고 링크
{url}

---
*수집일: {datetime.now().strftime('%Y-%m-%d')} (온통청년 크롤링)*
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

    print(f"[crawler] {len(docs)}개 MD 파일 저장 → {DATA_DIR}")
    return docs


def _guess_category(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["취업", "일자리", "고용", "채용", "인턴"]):  return "취업"
    if any(k in t for k in ["주거", "월세", "전세", "청약", "주택"]):     return "주거"
    if any(k in t for k in ["장학", "학자금", "등록금", "교육"]):         return "장학금"
    if any(k in t for k in ["적금", "계좌", "금융", "대출"]):             return "금융"
    return "복지"


def get_crawled_docs() -> list[dict]:
    """저장된 크롤링 문서 로드."""
    if not DATA_DIR.exists():
        return []
    docs, seen = [], set()
    for f in sorted(DATA_DIR.glob("*.md")):
        try:
            content = f.read_text(encoding="utf-8")
            title   = next(
                (l[2:].strip() for l in content.splitlines() if l.startswith("# ")),
                f.stem
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


# ── 직접 실행 시 테스트 ─────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("온통청년 크롤러 테스트")
    print("=" * 50)

    raw = crawl_policy_list(max_page=3)
    print(f"\n수집된 raw 데이터: {len(raw)}개")

    if raw:
        print("\n--- 첫 번째 항목 미리보기 ---")
        first = raw[0]
        for k, v in list(first.items())[:6]:
            print(f"  {k}: {str(v)[:60]}")

        docs = save_as_docs(raw)
        print(f"\n최종 저장: {len(docs)}개 MD 파일")
    else:
        print("\n⚠ 크롤링 결과 없음")
        print("사이트가 JavaScript 렌더링 방식이라 requests로는 접근 불가")
        print("→ Selenium 또는 Tavily API 사용 권장")
