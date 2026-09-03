"""
state.py — LangGraph 공유 상태 정의
"""
from typing_extensions import TypedDict


class FinalRAGState(TypedDict, total=False):
    question:           str    # 사용자 원본 질문
    rewritten_question: str    # 재작성된 검색 쿼리 (self-correction)
    tool_calls:         list   # LLM이 요청한 tool call 정보
    tool_name:          str    # 실행된 도구 이름
    tool_args:          dict   # 도구에 전달된 인수 (자격 검증, 추천 등 추가 컨텍스트)
    documents:          list   # 검색된 정책 문서 목록
    grade:              str    # "relevant" | "not_relevant"
    grade_score:        int    # 0~100 관련성 점수
    early_exit:         bool   # True = 유사도 미달로 즉시 web_search 전환
    max_similarity:     float  # 1차 검색 문서들의 최고 코사인 유사도
    tool_history:       list   # 회차별 tool call 이력 [{tool_name, args, docs_count, max_sim, grade}]
    answer:             str    # 최종 답변
    retry_count:        int    # 재시도 횟수 (무한루프 방지)
    execution_trace:    list   # [{"node": str, "summary": str}]
    user_profile:       dict   # 로그인 사용자 프로필 {email, age, region, employment_status, annual_income}
    conversation_history: list  # 같은 세션의 이전 대화 턴 [{role: "user"|"assistant", content: str}]
