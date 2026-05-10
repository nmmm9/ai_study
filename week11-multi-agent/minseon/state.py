"""
state.py
────────
week11 멀티에이전트 공유 상태

흐름:
  conversation_node → orchestrator_node
  → [scholarship/employment/housing/finance]_node
  → synthesizer_node
"""

from typing_extensions import TypedDict


class MultiAgentState(TypedDict, total=False):
    # ── 의도 라우터 ───────────────────────────────────────────
    intent: str             # "explore" | "qa"
    user_query: str         # 현재 사용자 질문 (라우터용)

    # ── 경로 A: 탐색 모드 (대화 → 오케스트레이터 → 전문 에이전트) ──
    messages: list          # [{"role": "user"|"assistant", "content": str}]
    user_profile: dict      # {"age": int, "region": str, "employment": str, "interests": list}
    profile_complete: bool  # 프로필 수집 완료 여부
    selected_agents: list   # ["scholarship", "employment", "housing", "finance"]
    agent_reasons: dict     # {"scholarship": "이유", ...}
    scholarship_result: str
    employment_result:  str
    housing_result:     str
    finance_result:     str
    final_answer: str       # 최종 통합 답변

    # ── 경로 B: 직접 Q&A 모드 (RAG 검색 → 즉시 답변) ────────
    qa_search_results: list  # RAG 검색 결과
    qa_answer: str           # 직접 답변

    # ── 실행 추적 ─────────────────────────────────────────────
    execution_trace: list    # [{"node": str, "summary": str}]
