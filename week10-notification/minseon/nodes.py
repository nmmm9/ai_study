"""
nodes.py
────────
week10 에이전트 노드 모음

[챗봇 모드 — chat_graph]
  chat_parse_node    질문 분석 (query_type / category / keywords)
  chat_profile_node  프로필 주입 (로그인 사용자 → DB값, 비로그인 → LLM 추출)
  chat_search_node   정책 검색
  chat_recommend_node GPT 맞춤 답변

[알림 모드 — notify_graph]
  profile_build_node 나이·지역 → 키워드
  search_node        정책 검색
  match_node         GPT 조건 매칭 + HTML 생성
  notify_node        Gmail 이메일 발송
"""

import json
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from openai import OpenAI

from state import NotifyState
from tools.policy_loader import (
    search_policies,
    search_all_policies,
    get_all_policy_titles,
    CATEGORY_KEYWORDS,
)
from notifier import send_email, build_email_html
from user_db import mark_notified, log_notification

_client = OpenAI()

_REGION_ALIASES: dict[str, list[str]] = {
    "서울": ["서울", "서울시", "수도권"],
    "경기": ["경기", "경기도", "수도권"],
    "인천": ["인천", "수도권"],
    "부산": ["부산", "부산시"],
    "대구": ["대구"],  "광주": ["광주"],
    "대전": ["대전"],  "울산": ["울산"],
    "세종": ["세종"],  "강원": ["강원"],
    "충북": ["충북", "충청북도"], "충남": ["충남", "충청남도"],
    "전북": ["전북", "전라북도"], "전남": ["전남", "전라남도"],
    "경북": ["경북", "경상북도"], "경남": ["경남", "경상남도"],
    "제주": ["제주", "제주도"],
}


def _add_trace(state: NotifyState, node: str, summary: str) -> list:
    trace = list(state.get("execution_trace", []))
    trace.append({"node": node, "summary": summary})
    return trace


def _parse_json(raw: str, fallback) -> dict | list:
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
# CHAT NODES — 챗봇 답변용
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

query_type:
- specific: 특정 정책 이름이 나오거나 상세 내용 질문
- general : "추천해줘", "어떤 게 있어?", "받을 수 있는 거" 등
"""


def chat_parse_node(state: NotifyState) -> dict:
    """사용자 질문을 분석합니다."""
    query = state.get("user_query", "")

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

    # 로그인된 사용자 프로필에서 정보 보강
    existing_profile = state.get("user_profile", {})
    llm_profile = {
        "age":        parsed.get("user_age") or existing_profile.get("age"),
        "income":     parsed.get("user_income") or existing_profile.get("income"),
        "employment": parsed.get("user_employment") or existing_profile.get("employment"),
        "region":     existing_profile.get("region"),
    }

    summary = f"{q_type} / {category} / {keywords[:3]}"
    print(f"[chat_parse_node] {summary}")

    return {
        "query_type":      q_type,
        "query_category":  category,
        "keywords":        keywords,
        "user_profile":    llm_profile,
        "execution_trace": _add_trace(state, "chat_parse_node", summary),
    }


_PROFILE_SYSTEM = """\
사용자 질문에서 청년정책 자격 조건 관련 정보를 JSON으로만 추출하세요.

출력 형식:
{
  "age": null | 숫자,
  "income": null | "저소득" | "중위소득" | "일반",
  "employment": null | "재학중" | "졸업" | "구직중" | "취업중",
  "region": null | "지역명",
  "extra_conditions": []
}
정보가 없으면 null. 추론 금지.
"""


def chat_profile_node(state: NotifyState) -> dict:
    """
    로그인된 사용자면 DB 프로필을 그대로 사용.
    비로그인이면 LLM으로 질문에서 조건 추출.
    """
    query   = state.get("user_query", "")
    profile = state.get("user_profile", {})

    # 로그인된 사용자는 age/region이 이미 있음 → LLM 추출 생략
    if not profile.get("age") and not profile.get("region"):
        response = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _PROFILE_SYSTEM},
                {"role": "user",   "content": query},
            ],
            max_tokens=256,
        )
        profile = _parse_json(response.choices[0].message.content or "{}", {})

    # 프로필 기반 키워드 보강
    keywords = list(state.get("keywords", []))
    age = profile.get("age") or state.get("user_age", 0)
    region = profile.get("region") or state.get("user_region", "")

    if age:
        if age <= 24:
            keywords += ["대학생", "장학금", "학자금"]
        elif age <= 29:
            keywords += ["취업", "청년", "구직"]
        else:
            keywords += ["청년", "주거", "금융"]
    if region:
        keywords += _REGION_ALIASES.get(region, [region])
    if profile.get("employment") == "재학중":
        keywords += ["재학생", "학자금"]
    elif profile.get("employment") == "구직중":
        keywords += ["구직", "취업준비"]

    summary_parts = [f"{k}={v}" for k, v in profile.items() if v]
    summary = ", ".join(summary_parts) if summary_parts else "조건 없음"
    print(f"[chat_profile_node] {summary}")

    return {
        "user_profile":    profile,
        "keywords":        list(dict.fromkeys(keywords)),
        "execution_trace": _add_trace(state, "chat_profile_node", summary),
    }


def chat_search_node(state: NotifyState) -> dict:
    """키워드·카테고리로 정책 문서를 검색합니다."""
    keywords    = state.get("keywords", [])
    category    = state.get("query_category", "")
    retry_count = state.get("search_retry_count", 0)

    if retry_count == 0:
        results = search_policies(keywords=keywords, category=category, top_k=5)
    else:
        results = search_all_policies(keywords=keywords, top_k=5)

    summary = f"{len(results)}개 검색 (retry={retry_count})"
    print(f"[chat_search_node] {summary}")

    return {
        "search_results":     results,
        "search_retry_count": retry_count + 1,
        "execution_trace":    _add_trace(state, "chat_search_node", summary),
    }


_CHAT_RECOMMEND_SYSTEM = """\
당신은 청년정책 전문 AI 상담사입니다.
사용자의 프로필(나이, 지역 등)과 검색된 정책 문서를 바탕으로 맞춤형 답변을 작성하세요.

## 응답 형식 (마크다운)

### 📋 관련 정책 요약
(검색된 정책들의 핵심 내용 요약)

### ✅ 맞춤 추천
(사용자 나이·지역·상황에 가장 적합한 정책과 이유)

### 📌 신청 방법
(신청 절차, 기간, 필요 서류)

### 💡 추가 정보
(주의사항, 함께 신청하면 좋은 정책)

## 원칙
- 문서에 있는 내용만 사용 (추측 금지)
- 사용자 나이·지역 조건을 반드시 언급
- 금액·나이·소득 수치는 그대로 전달
- 출처: **[출처: 파일명]** 형태로 표시
"""


def chat_recommend_node(state: NotifyState) -> dict:
    """GPT-4o가 맞춤 추천 답변을 생성합니다."""
    query   = state.get("user_query", "")
    profile = state.get("user_profile", {})
    results = state.get("search_results", [])

    # 사용자 컨텍스트 구성
    context_parts = [f"## 사용자 질문\n{query}"]

    # 로그인 사용자 정보 추가
    name   = state.get("user_name", "")
    age    = state.get("user_age") or profile.get("age")
    region = state.get("user_region") or profile.get("region")

    profile_lines = []
    if name:   profile_lines.append(f"이름: {name}")
    if age:    profile_lines.append(f"나이: {age}세")
    if region: profile_lines.append(f"지역: {region}")
    for k, v in profile.items():
        if v and k not in ("age", "region"):
            profile_lines.append(f"{k}: {v}")

    if profile_lines:
        context_parts.append("## 사용자 조건\n" + "\n".join(profile_lines))

    if results:
        context_parts.append(f"\n## 검색된 정책 문서 ({len(results)}개)")
        for doc in results:
            context_parts.append(f"\n### {doc['title']} [출처: {doc['source']}]\n{doc['content'][:2000]}")
    else:
        titles = get_all_policy_titles()
        context_parts.append("\n## 보유 정책 목록\n" + "\n".join(f"- {t}" for t in titles))
        context_parts.append("\n검색 결과가 없습니다. 위 정책 중 관련 내용을 안내해주세요.")

    prompt = "\n".join(context_parts) + "\n\n위 정보를 바탕으로 사용자에게 맞춤 정책을 안내해주세요."

    recommendation = ""
    stream = _client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": _CHAT_RECOMMEND_SYSTEM},
            {"role": "user",   "content": prompt},
        ],
        max_tokens=2048,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            recommendation += delta

    print(f"[chat_recommend_node] 답변 생성 완료 ({len(recommendation)}자)")

    return {
        "recommendation":  recommendation,
        "execution_trace": _add_trace(state, "chat_recommend_node", "맞춤 답변 생성 완료"),
    }


# ── 챗봇 라우터 ────────────────────────────────────────────────

def chat_route_by_type(state: NotifyState) -> str:
    return "need_profile" if state.get("query_type") == "general" else "skip_profile"


def chat_route_by_results(state: NotifyState) -> str:
    results     = state.get("search_results", [])
    retry_count = state.get("search_retry_count", 0)
    if not results and retry_count <= 1:
        return "retry"
    return "proceed"


# ════════════════════════════════════════════════════════════════
# NOTIFY NODES — 자동 이메일 알림용
# ════════════════════════════════════════════════════════════════

def profile_build_node(state: NotifyState) -> dict:
    """나이·지역 조건으로 검색 키워드를 구성합니다."""
    age    = state.get("user_age", 0)
    region = state.get("user_region", "")

    keywords = ["청년"]
    if age <= 24:
        keywords += ["대학생", "학자금", "장학금"]
    elif age <= 29:
        keywords += ["취업", "청년", "구직", "주거"]
    else:
        keywords += ["청년", "중소기업", "주거", "금융"]

    if region:
        keywords += _REGION_ALIASES.get(region, [region])

    all_cat_kws = [kw for kws in CATEGORY_KEYWORDS.values() for kw in kws]
    keywords += all_cat_kws[:8]
    keywords = list(dict.fromkeys(keywords))

    summary = f"나이={age}세, 지역={region}, 키워드 {len(keywords)}개"
    print(f"[profile_build_node] {summary}")

    return {
        "keywords":        keywords,
        "execution_trace": _add_trace(state, "profile_build_node", summary),
    }


def search_node(state: NotifyState) -> dict:
    """키워드로 정책 문서를 검색합니다."""
    keywords    = state.get("keywords", [])
    retry_count = state.get("search_retry_count", 0)

    results = (search_policies(keywords=keywords, category="", top_k=8)
               if retry_count == 0
               else search_all_policies(keywords=keywords, top_k=8))

    summary = f"{len(results)}개 검색 (retry={retry_count})"
    print(f"[search_node] {summary}")

    return {
        "search_results":     results,
        "search_retry_count": retry_count + 1,
        "execution_trace":    _add_trace(state, "search_node", summary),
    }


def route_by_results(state: NotifyState) -> str:
    results     = state.get("search_results", [])
    retry_count = state.get("search_retry_count", 0)
    return "retry" if not results and retry_count <= 1 else "proceed"


_MATCH_SYSTEM = """\
당신은 청년정책 전문 AI입니다.
사용자의 나이·지역 조건에 실제로 해당하는 정책만 골라 HTML 형식으로 안내하세요.

## 응답 형식 (HTML만, 마크다운 사용 금지)
<h3>📋 맞춤 정책 목록</h3>
<ul>
  <li><b>정책명</b>: 신청 자격 / 혜택 / 신청 방법 (2줄 이내 요약)</li>
</ul>
<h3>✅ 우선 추천</h3>
<p>가장 먼저 신청하면 좋은 정책과 이유</p>
<h3>📌 주의사항</h3>
<p>나이·지역 제한, 신청 기간 등 유의사항</p>

## 원칙
- 문서에 없는 내용은 절대 추가 금지
- 나이 범위와 지역 조건을 반드시 확인
- 조건 불명확하면 "조건 확인 필요" 표시
- 적합한 정책이 없으면 "현재 조건에 맞는 정책이 없습니다" 명시
"""


def match_node(state: NotifyState) -> dict:
    """GPT-4o가 나이·지역에 맞는 정책을 선별하고 HTML 추천을 생성합니다."""
    age     = state.get("user_age", 0)
    region  = state.get("user_region", "")
    results = state.get("search_results", [])

    context = f"사용자 조건: 나이={age}세, 지역={region}\n\n"
    if results:
        context += f"검색된 정책 ({len(results)}개):\n"
        for doc in results:
            context += f"\n### {doc['title']}\n{doc['content'][:1500]}\n"
    else:
        titles = get_all_policy_titles()
        context += "검색 결과 없음. 참고 정책 목록:\n" + "\n".join(f"- {t}" for t in titles)

    response = _client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": _MATCH_SYSTEM},
            {"role": "user",   "content": context},
        ],
        max_tokens=2000,
    )

    recommendation = response.choices[0].message.content or ""
    matched_titles = [doc["title"] for doc in results
                      if doc["title"].lower() in recommendation.lower()]

    summary = f"{len(matched_titles)}개 정책 매칭"
    print(f"[match_node] {summary}")

    return {
        "matched_policies": matched_titles,
        "recommendation":   recommendation,
        "execution_trace":  _add_trace(state, "match_node", summary),
    }


def route_by_match(state: NotifyState) -> str:
    if state.get("user_email") and state.get("recommendation"):
        return "send"
    return "skip"


def notify_node(state: NotifyState) -> dict:
    """이메일을 발송하고 DB 기록을 갱신합니다."""
    name           = state.get("user_name", "회원")
    email          = state.get("user_email", "")
    age            = state.get("user_age", 0)
    region         = state.get("user_region", "")
    recommendation = state.get("recommendation", "")
    matched        = state.get("matched_policies", [])

    html_body = build_email_html(
        name=name, age=age, region=region, recommendation=recommendation,
    )
    sent = send_email(
        to_email=email,
        subject=f"[청년정책 알림] {name}님께 맞는 정책 {len(matched)}건",
        html_body=html_body,
    )

    if sent and email:
        mark_notified(email)
        log_notification(email, matched)

    summary = f"{'발송 완료' if sent else '발송 실패'} → {email}"
    print(f"[notify_node] {summary}")

    return {
        "email_sent":      sent,
        "execution_trace": _add_trace(state, "notify_node", summary),
    }
