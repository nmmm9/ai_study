"""
web_searcher.py
───────────────
Tavily 실시간 웹 검색 → GPT가 정책 문서로 정리 → RAG에 추가

흐름:
  1. Tavily로 "청년 정책 2025 2026" 등 검색
  2. GPT-4o-mini가 검색 결과를 정책 문서 형식으로 변환
  3. tools/data/web/ 에 MD 파일로 저장
  4. RAG 재빌드 시 자동 포함

API 키 발급 (무료):
  https://tavily.com → 회원가입 → API Keys → 복사
  .env에 TAVILY_API_KEY=tvly-... 입력
  무료 플랜: 1,000 searches/month
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path

from openai import OpenAI

DATA_DIR = Path(__file__).parent / "data" / "web"

# 검색 쿼리 템플릿 — 나이·지역·연도 조합
_QUERY_TEMPLATES = [
    "{year} 청년 정책 지원 신청",
    "{year} 청년 취업 지원금 자격",
    "{year} 청년 주거 월세 지원",
    "{year} 청년 장학금 소득분위",
    "{year} 청년 금융 적금 혜택",
    "{region} {year} 청년 정책",
]

_client = OpenAI()


def _has_tavily() -> bool:
    return bool(os.getenv("TAVILY_API_KEY", "").strip())


def _tavily_search(query: str, max_results: int = 5) -> list[dict]:
    """Tavily API로 웹 검색 후 결과 반환."""
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        resp = client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_raw_content=True,
        )
        return resp.get("results", [])
    except ImportError:
        print("[web_searcher] tavily-python 미설치: pip install tavily-python")
        return []
    except Exception as e:
        print(f"[web_searcher] Tavily 오류: {e}")
        return []


_GPT_SYSTEM = """\
당신은 정부 청년정책 문서를 정리하는 AI입니다.
주어진 웹 검색 결과에서 실제 청년 지원 정책 정보만 추출하여
아래 JSON 배열 형식으로만 응답하세요.

[
  {
    "name": "정책 이름",
    "category": "취업|주거|장학금|금융|복지 중 하나",
    "summary": "1-2줄 요약",
    "benefit": "지원 내용 (금액, 기간 등)",
    "qualify": "신청 자격 (나이, 소득, 지역 조건)",
    "how": "신청 방법",
    "period": "신청 기간",
    "dept": "주관 기관",
    "url": "관련 URL (있으면)"
  }
]

규칙:
- 중복 정책은 하나로 합치세요
- 정보가 불분명한 항목은 빈 문자열로 두세요
- 광고·홍보 글은 제외하세요
- 종료된 정책은 제외하세요
- 결과가 없으면 빈 배열 [] 반환
"""


def _gpt_extract(search_results: list[dict]) -> list[dict]:
    """GPT로 검색 결과에서 정책 정보를 추출."""
    if not search_results:
        return []

    context = "\n\n".join(
        f"[출처: {r.get('url', '')}]\n{r.get('content') or r.get('raw_content', '')[:1500]}"
        for r in search_results
    )

    try:
        resp = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _GPT_SYSTEM},
                {"role": "user",   "content": context},
            ],
            max_tokens=2000,
        )
        raw = resp.choices[0].message.content or "[]"
        # JSON 파싱
        raw = re.sub(r"```json|```", "", raw).strip()
        return json.loads(raw)
    except Exception as e:
        print(f"[web_searcher] GPT 추출 오류: {e}")
        return []


def _policy_to_md(policy: dict) -> str:
    """정책 dict → 마크다운 문서 생성."""
    return f"""# {policy.get('name', '정책명 없음')}

## 개요
{policy.get('summary', '')}

## 지원 내용
{policy.get('benefit', '')}

## 신청 자격
{policy.get('qualify', '')}

## 신청 방법
{policy.get('how', '')}

## 신청 기간
{policy.get('period', '')}

## 주관 기관
{policy.get('dept', '')}

## 참고 링크
{policy.get('url', '')}

---
*수집일: {datetime.now().strftime('%Y-%m-%d')} (Tavily 웹 검색)*
""".strip()


def fetch_latest_policies(
    age: int | None = None,
    region: str | None = None,
) -> list[dict]:
    """
    Tavily로 최신 정책을 검색하고 GPT로 정리하여 저장합니다.

    Returns:
        저장된 정책 doc dict 목록
    """
    if not _has_tavily():
        print("[web_searcher] TAVILY_API_KEY 없음")
        return []

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    year = datetime.now().year
    saved: list[dict] = []
    seen_names: set[str] = set()

    queries = [
        t.format(year=year, region=region or "전국")
        for t in _QUERY_TEMPLATES
    ]
    if age:
        queries.append(f"{year} {age}세 청년 지원 정책")

    print(f"[web_searcher] {len(queries)}개 쿼리로 검색 시작")

    all_results: list[dict] = []
    for query in queries:
        print(f"  검색: {query}")
        results = _tavily_search(query, max_results=4)
        all_results.extend(results)

    # GPT로 전체 결과에서 정책 추출
    print(f"[web_searcher] GPT로 {len(all_results)}개 결과 분석 중...")
    policies = _gpt_extract(all_results)
    print(f"[web_searcher] {len(policies)}개 정책 추출됨")

    for policy in policies:
        name = policy.get("name", "").strip()
        if not name or name in seen_names:
            continue
        seen_names.add(name)

        md_content = _policy_to_md(policy)
        safe_name  = re.sub(r'[\\/:*?"<>|]', "", name)[:40]
        md_path    = DATA_DIR / f"{safe_name}.md"
        md_path.write_text(md_content, encoding="utf-8")

        saved.append({
            "title":    name,
            "content":  md_content,
            "source":   md_path.name,
            "category": policy.get("category", "기타"),
        })

    # 메타 저장
    meta = {
        "fetched_at": datetime.now().isoformat(),
        "count":      len(saved),
        "age":        age,
        "region":     region,
        "queries":    queries,
    }
    (DATA_DIR / "_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"[web_searcher] 완료: {len(saved)}개 저장 → {DATA_DIR}")
    return saved


def get_web_docs() -> list[dict]:
    """저장된 웹 검색 기반 정책 문서 로드."""
    if not DATA_DIR.exists():
        return []

    docs: list[dict] = []
    seen: set[str]   = set()

    for md_file in sorted(DATA_DIR.glob("*.md")):
        try:
            content = md_file.read_text(encoding="utf-8")
            title   = ""
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
                "category": "기타",
            })
        except Exception:
            continue

    return docs


def get_web_meta() -> dict | None:
    meta_path = DATA_DIR / "_meta.json"
    if not meta_path.exists():
        return None
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def has_tavily_key() -> bool:
    return _has_tavily()
