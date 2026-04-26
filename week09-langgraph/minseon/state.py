"""
state.py
────────
LangGraph 노드 간 공유 상태 — 청년정책 에이전트 버전
"""

from typing_extensions import TypedDict


class YouthPolicyState(TypedDict, total=False):
    # ── 입력 ─────────────────────────────────────────────────
    user_query: str          # 사용자 질문

    # ── parse_query_node 결과 ─────────────────────────────────
    query_type: str          # "specific" | "general"
                             #   specific: 특정 정책 문의 ("청년도약계좌가 뭐야?")
                             #   general : 맞춤 추천 요청 ("나한테 맞는 정책 알려줘")
    query_category: str      # 장학금 / 취업 / 주거 / 금융 / 기타
    keywords: list           # 검색에 사용할 핵심 키워드 목록

    # ── profile_node 결과 (general 타입일 때만 실행) ──────────
    user_profile: dict       # {"age": int, "income": str, "employment": str, ...}

    # ── search_node 결과 ─────────────────────────────────────
    search_results: list     # [{"title": str, "content": str, "source": str}, ...]
    search_retry_count: int  # 재시도 횟수 (0 → 엄격 검색, 1 → 전체 검색)

    # ── recommend_node 결과 ──────────────────────────────────
    recommendation: str      # 최종 답변

    # ── 실행 추적 ─────────────────────────────────────────────
    execution_trace: list    # [{"node": str, "summary": str}, ...]
