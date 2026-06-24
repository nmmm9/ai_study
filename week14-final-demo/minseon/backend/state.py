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
    answer:             str    # 최종 답변
    retry_count:        int    # 재시도 횟수 (무한루프 방지)
    execution_trace:    list   # [{"node": str, "summary": str}]
