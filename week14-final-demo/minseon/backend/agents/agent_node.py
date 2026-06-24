"""
agent_node.py — LLM이 3가지 도구 중 하나를 선택하는 에이전트 (BACKEND 계층)
"""

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from openai import OpenAI
from backend.state    import FinalRAGState
from backend.tools.rag_tool import ALL_TOOLS

_client = OpenAI()

_SYSTEM = """\
당신은 약 620개 청년정책 데이터베이스를 활용하는 청년정책 전문 AI입니다.
사용자의 질문 유형에 따라 아래 8가지 도구 중 가장 적합한 것을 선택하세요.

## 도구 선택 기준

| 질문 유형 | 사용 도구 |
|----------|---------|
| 특정 정책의 조건·금액·기간 질문 | search_policies |
| "자세히 알려줘", "상세 정보" | get_policy_details |
| "신청 자격 돼?", "나 가능해?" | check_eligibility |
| "나한테 맞는 정책 추천해줘" | recommend_policies |
| "어떻게 신청해?", "필요 서류" | get_application_method |
| "곧 마감되는 정책", "이번 달 신청" | get_upcoming_deadlines |
| "A랑 B 비교해줘", "둘 중 뭐가 나아" | compare_policies |
| "목록", "어떤 게 있어", "종류 알려줘" | list_by_category |
| 인사, 간단한 질문 | 도구 없이 직접 답변 |

## 카테고리 가이드
취업/일자리/채용/인턴 → "일자리"
진로/자격증/직업훈련/일경험 → "진로"
창업/스타트업/벤처 → "창업"
월세/전세/주택/청약 → "주거"
적금/계좌/대출/금융 → "금융"
장학금/학자금/등록금/교육비 → "교육"
심리/마음건강/상담/우울 → "마음건강"
건강검진/의료비/신체건강 → "신체건강"
문화/도서/예술/여가/공연 → "문화/예술"
기타 복지·생활지원 → "생활지원"
"""


def agent_node(state: FinalRAGState) -> dict:
    question  = state.get("rewritten_question") or state.get("question", "")
    documents = state.get("documents", [])
    retry     = state.get("retry_count", 0)

    messages = [{"role": "system", "content": _SYSTEM}]

    if documents:
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
    print(f"[agent_node] retry={retry} | {tc_summary}")

    trace = list(state.get("execution_trace", []))
    trace.append({"node": "agent_node", "summary": tc_summary})

    return {
        "tool_calls":      [tc.model_dump() for tc in tool_calls],
        "retry_count":     retry,
        "execution_trace": trace,
    }


def route_agent(state: FinalRAGState) -> str:
    return "tool" if state.get("tool_calls") else "generate"
