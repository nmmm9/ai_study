"""
nodes.py
────────
청년정책 에이전트 — LangGraph 노드 & 조건부 라우터 정의

그래프 흐름:
  parse_query_node
    ↓ [route_by_query_type]
    ├─ general → profile_node → search_node
    └─ specific →              search_node
                                ↓ [route_by_results]
                                ├─ 결과 있음 → recommend_node
                                └─ 결과 없음 → search_node (전체 재검색)
                 recommend_node → END
"""

import json
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from openai import OpenAI

from state import YouthPolicyState
from tools.policy_loader import (
    search_policies,
    search_all_policies,
    get_all_policy_titles,
    CATEGORY_KEYWORDS,
)

_client = OpenAI()

# ANSI 색상
_CYAN    = "\033[96m"
_YELLOW  = "\033[93m"
_GREEN   = "\033[92m"
_MAGENTA = "\033[95m"
_BOLD    = "\033[1m"
_DIM     = "\033[2m"
_RESET   = "\033[0m"


def _log(icon: str, node: str, msg: str, color: str = _CYAN) -> None:
    print(f"\n{color}{_BOLD}[{node}]{_RESET} {icon}  {msg}")


def _add_trace(state: YouthPolicyState, node: str, summary: str) -> list:
    trace = list(state.get("execution_trace", []))
    trace.append({"node": node, "summary": summary})
    return trace


def _parse_json(raw: str, fallback: dict) -> dict:
    """LLM 응답에서 JSON을 추출합니다."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        return fallback


# ════════════════════════════════════════════════════════════════
# NODE 1: parse_query_node
# ════════════════════════════════════════════════════════════════

_PARSE_SYSTEM = """\
사용자의 청년정책 관련 질문을 분석하여 JSON으로만 응답하세요.

출력 형식:
{
  "query_type": "specific" | "general",
  "query_category": "장학금" | "취업" | "주거" | "금융" | "기타",
  "keywords": ["키워드1", "키워드2", ...],
  "user_age": null | 숫자,
  "user_income": null | "저소득" | "중위소득" | "일반",
  "user_employment": null | "재학중" | "졸업" | "구직중" | "취업중"
}

query_type 판단 기준:
- specific: 특정 정책 이름이 언급되거나 정책 상세 내용을 묻는 질문
- general : "추천해줘", "어떤 게 있어?", "내가 받을 수 있는 거" 등 맞춤 추천 요청
"""


def parse_query_node(state: YouthPolicyState) -> dict:
    """사용자 질문을 분석하여 query_type, category, keywords를 추출합니다."""
    query = state.get("user_query", "")
    _log("🔍", "parse_query_node", f"질문 분석 중: '{query}'", _CYAN)

    response = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": _PARSE_SYSTEM},
            {"role": "user",   "content": query},
        ],
        max_tokens=256,
    )

    parsed = _parse_json(
        response.choices[0].message.content or "{}",
        {"query_type": "general", "query_category": "기타", "keywords": [query]},
    )

    q_type   = parsed.get("query_type", "general")
    category = parsed.get("query_category", "기타")
    keywords = parsed.get("keywords", [query])

    _log("✅", "parse_query_node",
         f"type={q_type} / category={category} / keywords={keywords}", _CYAN)

    profile = {
        "age":        parsed.get("user_age"),
        "income":     parsed.get("user_income"),
        "employment": parsed.get("user_employment"),
    }

    return {
        "query_type":      q_type,
        "query_category":  category,
        "keywords":        keywords,
        "user_profile":    profile,
        "execution_trace": _add_trace(state, "parse_query_node",
                                      f"{q_type} / {category} / {keywords}"),
    }


# ════════════════════════════════════════════════════════════════
# NODE 2: profile_node  (general 타입일 때만 실행)
# ════════════════════════════════════════════════════════════════

_PROFILE_SYSTEM = """\
사용자 질문에서 청년정책 자격 조건과 관련된 정보를 추출하여 JSON으로만 응답하세요.

출력 형식:
{
  "age": null | 숫자,
  "income": null | "저소득" | "중위소득" | "일반",
  "employment": null | "재학중" | "졸업" | "구직중" | "취업중",
  "region": null | "지역명",
  "extra_conditions": []
}

정보가 없으면 null로 표시하세요. 추론하지 마세요.
"""


def profile_node(state: YouthPolicyState) -> dict:
    """일반 추천 요청 시 사용자 프로필 조건을 정리합니다."""
    query   = state.get("user_query", "")
    profile = state.get("user_profile", {})

    _log("👤", "profile_node", "사용자 조건 정리 중...", _YELLOW)

    if not any(v for v in profile.values()):
        response = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _PROFILE_SYSTEM},
                {"role": "user",   "content": query},
            ],
            max_tokens=256,
        )
        profile = _parse_json(
            response.choices[0].message.content or "{}",
            {},
        )

    # 프로필 기반 키워드 보강
    keywords = list(state.get("keywords", []))
    if profile.get("employment") == "재학중":
        keywords += ["대학생", "재학생", "학자금"]
    elif profile.get("employment") == "구직중":
        keywords += ["구직", "취업준비", "청년"]
    if profile.get("income") in ("저소득", "중위소득"):
        keywords += ["소득분위", "저소득"]

    summary_parts = [f"{k}={v}" for k, v in profile.items() if v]
    summary = ", ".join(summary_parts) if summary_parts else "조건 없음"
    _log("✅", "profile_node", f"프로필: {summary}", _YELLOW)

    return {
        "user_profile":    profile,
        "keywords":        list(set(keywords)),
        "execution_trace": _add_trace(state, "profile_node", summary),
    }


# ════════════════════════════════════════════════════════════════
# NODE 3: search_node
# ════════════════════════════════════════════════════════════════

def search_node(state: YouthPolicyState) -> dict:
    """키워드·카테고리로 정책 문서를 검색합니다.

    retry_count == 0: 카테고리 필터 + 키워드 검색
    retry_count >= 1: 전체 DB에서 키워드만으로 재검색
    """
    keywords    = state.get("keywords", [])
    category    = state.get("query_category", "")
    retry_count = state.get("search_retry_count", 0)

    if retry_count == 0:
        _log("📄", "search_node",
             f"검색 중: keywords={keywords}, category={category}", _MAGENTA)
        results = search_policies(keywords=keywords, category=category, top_k=5)
    else:
        _log("🔄", "search_node",
             f"전체 재검색 중 (retry={retry_count}): keywords={keywords}", _YELLOW)
        results = search_all_policies(keywords=keywords, top_k=5)

    _log("✅", "search_node", f"{len(results)}개 정책 문서 검색됨", _MAGENTA)

    return {
        "search_results":     results,
        "search_retry_count": retry_count + 1,
        "execution_trace":    _add_trace(
            state, "search_node",
            f"{len(results)}개 검색 (retry={retry_count})"
        ),
    }


# ════════════════════════════════════════════════════════════════
# NODE 4: recommend_node
# ════════════════════════════════════════════════════════════════

_RECOMMEND_SYSTEM = """\
당신은 청년정책 전문 AI 챗봇입니다.
제공된 정책 문서와 사용자 정보를 바탕으로 맞춤형 답변을 작성하세요.

## 응답 형식 (마크다운)

### 📋 관련 정책 요약
(검색된 정책들의 핵심 내용을 간략히 정리)

### ✅ 맞춤 추천
(사용자 상황에 가장 적합한 정책과 그 이유)

### 📌 신청 방법
(신청 절차, 기간, 필요 서류 등 실용적 정보)

### 💡 추가 정보
(관련 정책이나 주의사항, 함께 검토할 정책)

## 원칙
- 문서에 있는 내용만 사용 (추측 금지)
- 금액·나이·소득 기준 등 수치는 그대로 전달
- 정보 출처를 **[출처: 파일명]** 형태로 표시
- 해당 정책이 없으면 유사한 정책을 안내
"""


def recommend_node(state: YouthPolicyState) -> dict:
    """검색된 정책 문서를 바탕으로 GPT-4o가 맞춤 추천을 생성합니다."""
    _log("✨", "recommend_node", "GPT-4o가 맞춤 추천을 생성합니다...", _GREEN)

    query   = state.get("user_query", "")
    profile = state.get("user_profile", {})
    results = state.get("search_results", [])

    context_parts = [f"## 사용자 질문\n{query}"]

    profile_desc = ", ".join(f"{k}: {v}" for k, v in profile.items() if v)
    if profile_desc:
        context_parts.append(f"## 사용자 조건\n{profile_desc}")

    if results:
        context_parts.append(f"\n## 검색된 정책 문서 ({len(results)}개)")
        for doc in results:
            context_parts.append(
                f"\n### {doc['title']} [출처: {doc['source']}]\n{doc['content'][:2000]}"
            )
    else:
        titles = get_all_policy_titles()
        context_parts.append(
            "\n## 참고: 보유 정책 목록\n" + "\n".join(f"- {t}" for t in titles)
        )
        context_parts.append("\n검색 결과가 없습니다. 보유 정책 중 관련된 내용으로 안내해주세요.")

    prompt = "\n".join(context_parts) + "\n\n위 정보를 바탕으로 사용자에게 맞춤 정책을 안내해주세요."

    print(f"\n{_GREEN}{'─'*60}{_RESET}")
    recommendation = ""
    stream = _client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": _RECOMMEND_SYSTEM},
            {"role": "user",   "content": prompt},
        ],
        max_tokens=2048,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            print(delta, end="", flush=True)
            recommendation += delta
    print(f"\n{_GREEN}{'─'*60}{_RESET}")

    return {
        "recommendation":  recommendation,
        "execution_trace": _add_trace(state, "recommend_node", "맞춤 추천 생성 완료"),
    }


# ════════════════════════════════════════════════════════════════
# 조건부 라우터
# ════════════════════════════════════════════════════════════════

def route_by_query_type(state: YouthPolicyState) -> str:
    """질문 유형에 따라 분기합니다."""
    q_type = state.get("query_type", "general")

    if q_type == "general":
        print(f"\n{_YELLOW}🔀 [route_by_query_type] → profile_node (일반 추천 요청){_RESET}")
        return "need_profile"

    print(f"\n{_CYAN}🔀 [route_by_query_type] → search_node (특정 정책 문의){_RESET}")
    return "skip_profile"


def route_by_results(state: YouthPolicyState) -> str:
    """검색 결과 수에 따라 분기합니다."""
    results     = state.get("search_results", [])
    retry_count = state.get("search_retry_count", 0)

    if len(results) == 0 and retry_count <= 1:
        print(f"\n{_YELLOW}🔀 [route_by_results] → search_node (결과 없음, 전체 재검색){_RESET}")
        return "retry"

    print(f"\n{_CYAN}🔀 [route_by_results] → recommend_node ({len(results)}개 결과){_RESET}")
    return "proceed"
