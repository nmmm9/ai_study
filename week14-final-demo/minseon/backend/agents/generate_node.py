"""
generate_node.py — 최종 답변 생성 (BACKEND 계층)

도구별 출력 형식:
  search_policy     → 정책 상세 정보
  compare_policies  → 두 정책 비교표
  list_by_category  → 정책 목록 요약
"""

from datetime import datetime

from openai import OpenAI, AsyncOpenAI
from backend.config import settings
from backend.logging_config import get_logger
from backend.prompts.generate import (
    SYSTEM_SEARCH      as _SYSTEM_SEARCH,
    SYSTEM_COMPARE      as _SYSTEM_COMPARE,
    SYSTEM_LIST         as _SYSTEM_LIST,
    SYSTEM_ELIGIBILITY  as _SYSTEM_ELIGIBILITY,
    SYSTEM_RECOMMEND    as _SYSTEM_RECOMMEND,
    SYSTEM_APPLICATION  as _SYSTEM_APPLICATION,
    SYSTEM_REALTIME     as _SYSTEM_REALTIME,
    SYSTEM_NEWS         as _SYSTEM_NEWS,
    SYSTEM_DEADLINES    as _SYSTEM_DEADLINES,
)
from backend.state import FinalRAGState

logger = get_logger(__name__)

_client       = OpenAI(api_key=settings.openai_api_key)
_async_client = AsyncOpenAI(api_key=settings.openai_api_key)


def _select_system(tool_name: str) -> str:
    if tool_name == "compare_policies":
        return _SYSTEM_COMPARE
    elif tool_name == "list_by_category":
        return _SYSTEM_LIST
    elif tool_name == "check_eligibility":
        return _SYSTEM_ELIGIBILITY
    elif tool_name == "recommend_policies":
        return _SYSTEM_RECOMMEND
    elif tool_name == "get_application_method":
        return _SYSTEM_APPLICATION
    elif tool_name == "get_upcoming_deadlines":
        return _SYSTEM_DEADLINES
    elif tool_name in ("search_realtime_policies", "web_search"):
        return _SYSTEM_REALTIME
    elif tool_name == "search_youth_news":
        return _SYSTEM_NEWS
    return _SYSTEM_SEARCH


def _build_context(question: str, tool_args: dict, documents: list,
                   tool_name: str = "", user_profile: dict | None = None) -> str:
    today = datetime.now()
    context = f"## 오늘 날짜\n{today.strftime('%Y년 %m월 %d일')} ({today.strftime('%Y-%m')})\n\n"
    context += f"## 질문\n{question}\n\n"

    # 사용자 프로필이 있으면 답변에 개인화 반영 지시
    if user_profile:
        profile_lines = []
        if user_profile.get("age"):
            profile_lines.append(f"나이: 만 {user_profile['age']}세")
        if user_profile.get("region"):
            profile_lines.append(f"거주 지역: {user_profile['region']}")
        if user_profile.get("employment_status"):
            status_map = {"employed": "재직자", "unemployed": "미취업자",
                          "student": "재학생", "freelancer": "프리랜서"}
            s = status_map.get(user_profile["employment_status"], user_profile["employment_status"])
            profile_lines.append(f"취업 상태: {s}")
        if user_profile.get("annual_income"):
            profile_lines.append(f"연소득: {user_profile['annual_income']:,}만원")
        if profile_lines:
            context += "## 사용자 프로필 (이 조건에 맞춰 개인화된 답변 작성)\n"
            context += "\n".join(f"- {p}" for p in profile_lines) + "\n\n"

    if tool_args:
        relevant = {k: v for k, v in tool_args.items() if v and k not in ("top_k", "keywords", "query")}
        if relevant:
            context += f"## 사용자 입력 조건\n{relevant}\n\n"

    is_web  = tool_name in ("web_search", "search_realtime_policies")
    is_news = tool_name == "search_youth_news"
    real_docs = [d for d in documents if d.get("source") != "fallback"]

    if real_docs:
        label = "청년 뉴스 기사" if is_news else ("실시간 웹검색 결과" if is_web else "검색된 정책 문서")
        context += f"## {label} ({len(real_docs)}개) — 이 내용만 바탕으로 답변하세요\n"
        context += "※ 답변 마지막에 반드시 '## 출처' 섹션을 추가하고 문서 제목과 URL을 나열하세요.\n"
        for i, doc in enumerate(real_docs, 1):
            context += f"\n### [문서{i}] {doc['title']}\n출처URL: {doc.get('url','')}\n{doc['content'][:1500]}\n"
    else:
        context += (
            "## 참고\n"
            "실시간 웹검색 결과를 가져오지 못했습니다.\n"
            "알고 있는 지식으로 최선을 다해 답변하되, 금리·신청 현황처럼 매일 바뀌는 수치는\n"
            "반드시 '(실제 수치는 변동될 수 있으니 공식 사이트 확인 필요)' 라고 명시하세요.\n"
        )
    return context


async def stream_answer(state: FinalRAGState):
    """FastAPI 스트리밍 엔드포인트에서 호출 — 청크 단위로 yield."""
    question     = state.get("rewritten_question") or state.get("question", "")
    documents    = state.get("documents", [])
    tool_name    = state.get("tool_name", "")
    tool_args    = state.get("tool_args", {})
    user_profile = state.get("user_profile", {})
    history      = state.get("conversation_history", [])

    system  = _select_system(tool_name)
    context = _build_context(question, tool_args, documents, tool_name, user_profile)

    messages = [{"role": "system", "content": system}]
    messages.extend(history[-10:])
    messages.append({"role": "user", "content": context})

    stream = await _async_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=1500,
        stream=True,
    )
    async for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            yield content


def generate_node(state: FinalRAGState) -> dict:
    question     = state.get("rewritten_question") or state.get("question", "")
    documents    = state.get("documents", [])
    tool_name    = state.get("tool_name", "")
    tool_args    = state.get("tool_args", {})
    retry        = state.get("retry_count", 0)
    user_profile = state.get("user_profile", {})
    history      = state.get("conversation_history", [])

    system  = _select_system(tool_name)
    context = _build_context(question, tool_args, documents, tool_name, user_profile)

    messages = [{"role": "system", "content": system}]
    messages.extend(history[-10:])
    messages.append({"role": "user", "content": context})

    resp = _client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=1500,
    )
    answer = resp.choices[0].message.content or ""
    logger.info(f"[generate_node] {len(answer)}자 | 도구={tool_name} | 재시도={retry}회")

    trace = list(state.get("execution_trace", []))
    trace.append({
        "node":    "generate_node",
        "summary": f"답변 생성 완료 (문서 {len(documents)}개 활용, 재검색 {retry}회)",
    })
    return {"answer": answer, "execution_trace": trace}
