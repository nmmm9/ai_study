"""
agent_node.py — LLM이 3가지 도구 중 하나를 선택하는 에이전트 (BACKEND 계층)
"""

from openai import OpenAI
from backend.config   import settings
from backend.logging_config import get_logger
from backend.prompts.agent import SYSTEM_BASE as _SYSTEM_BASE
from backend.state    import FinalRAGState
from backend.tools.rag_tool import ALL_TOOLS

logger = get_logger(__name__)

_client = OpenAI(api_key=settings.openai_api_key)


def _build_profile_context(user_profile: dict) -> str:
    """사용자 프로필을 자연어 컨텍스트로 변환."""
    if not user_profile:
        return ""

    parts = []
    if user_profile.get("age"):
        parts.append(f"나이: 만 {user_profile['age']}세")
    if user_profile.get("region"):
        parts.append(f"거주 지역: {user_profile['region']}")
    if user_profile.get("employment_status"):
        status_map = {
            "employed":    "재직자",
            "unemployed":  "미취업자",
            "student":     "재학생",
            "freelancer":  "프리랜서",
        }
        s = status_map.get(user_profile["employment_status"], user_profile["employment_status"])
        parts.append(f"취업 상태: {s}")
    if user_profile.get("annual_income"):
        parts.append(f"연소득: {user_profile['annual_income']:,}만원")

    if not parts:
        return ""

    return (
        "\n\n## 현재 사용자 프로필 (도구 호출 시 이 정보를 args에 자동 반영)\n"
        + "\n".join(f"- {p}" for p in parts)
        + "\n\n이 프로필 정보를 search_policies, check_eligibility, recommend_policies 등의 "
        "region, age, employment_status 인수에 자동으로 포함하라."
    )


def _build_history_messages(tool_history: list) -> list[dict]:
    """
    이전 회차 tool call + 결과를 OpenAI 메시지 형식으로 변환.
    assistant(tool_call) → tool(result) 쌍으로 구성하여
    에이전트가 이전 시도를 인식하고 다른 전략을 선택하도록 유도합니다.
    """
    import json as _json
    messages = []
    for i, h in enumerate(tool_history):
        call_id = f"call_hist_{i}"
        # 이전 assistant가 호출했던 tool call
        messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id":       call_id,
                "type":     "function",
                "function": {
                    "name":      h["tool_name"],
                    "arguments": _json.dumps(h["args"], ensure_ascii=False),
                },
            }],
        })
        # tool 실행 결과 요약
        result_parts = [f"검색 결과: {h['docs_count']}건"]
        if h.get("max_sim", 1.0) < 1.0:
            result_parts.append(f"최고 유사도: {h['max_sim']:.2f}")
        if h.get("early_exit"):
            result_parts.append("⚡ 유사도 미달로 조기탈출")
        if h.get("grade"):
            result_parts.append(f"관련성 평가: {h['grade']}")
        if h["docs_count"] == 0:
            result_parts.append("→ 벡터 DB에 해당 정보 없음")
        messages.append({
            "role":         "tool",
            "tool_call_id": call_id,
            "content":      " | ".join(result_parts),
        })
    return messages


def agent_node(state: FinalRAGState) -> dict:
    question     = state.get("rewritten_question") or state.get("question", "")
    documents    = state.get("documents", [])
    retry        = state.get("retry_count", 0)
    tool_history = state.get("tool_history", [])
    user_profile = state.get("user_profile", {})
    history      = state.get("conversation_history", [])

    system_content = _SYSTEM_BASE + _build_profile_context(user_profile)
    messages = [{"role": "system", "content": system_content}]
    if history:
        messages.extend(history[-10:])

    if retry > 0 and tool_history:
        # 1차 질문 메시지
        messages.append({"role": "user", "content": state.get("question", question)})
        # 이전 회차 tool call 이력 주입
        messages.extend(_build_history_messages(tool_history))
        # 재시도 지시
        tried = [h["tool_name"] for h in tool_history]
        messages.append({
            "role": "user",
            "content": (
                f"위 검색 결과들이 관련성 기준을 충족하지 못했습니다.\n"
                f"이미 시도한 도구: {tried}\n"
                f"현재 질문: {question}\n\n"
                f"이번에는 다른 도구를 선택하거나, 더 포괄적인 키워드로 검색하세요. "
                f"예: 유사어·상위 카테고리·다른 도구명 활용."
            ),
        })
    elif documents:
        ctx = "\n\n".join(
            f"### {d['title']}\n{d['content'][:800]}" for d in documents
        )
        messages.append({
            "role": "user",
            "content": f"질문: {question}\n\n현재 검색된 문서:\n{ctx}",
        })
    else:
        messages.append({"role": "user", "content": question})

    resp = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=ALL_TOOLS,
        tool_choice="auto",
        max_tokens=500,
    )

    msg        = resp.choices[0].message
    tool_calls = msg.tool_calls or []
    tc_summary = (
        f"{tool_calls[0].function.name} 호출" if tool_calls
        else "직접 답변 선택"
    )
    logger.info(f"[agent_node] retry={retry} | {tc_summary}")

    trace = list(state.get("execution_trace", []))
    trace.append({"node": "agent_node", "summary": tc_summary})

    return {
        "tool_calls":      [tc.model_dump() for tc in tool_calls],
        "retry_count":     retry,
        "execution_trace": trace,
    }


def route_agent(state: FinalRAGState) -> str:
    return "tool" if state.get("tool_calls") else "generate"
