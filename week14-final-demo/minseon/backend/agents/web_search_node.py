"""
web_search_node.py — RAG 실패 시 Tavily 웹검색 fallback

RAG 재시도 2회 후에도 관련 문서를 못 찾으면 이 노드가 실행됩니다.
Tavily → RSS 캐시 → 빈 결과 순으로 시도합니다.
빈 결과여도 generate_node가 GPT 일반 지식으로 반드시 답변합니다.
"""

from backend.logging_config import get_logger
from backend.state import FinalRAGState
from backend.tools.realtime_fetcher import tavily_search, search_rss_cache

logger = get_logger(__name__)


def web_search_node(state: FinalRAGState) -> dict:
    original  = state.get("question", "")
    rewritten = state.get("rewritten_question") or original

    # 검색 쿼리: 재작성 질문 우선, 없으면 원본
    query = rewritten if rewritten != original else f"{original} 청년 정책 지원"

    docs: list[dict] = []

    # 1순위: Tavily (realtime_fetcher의 지능형 도메인 필터 적용)
    try:
        docs = tavily_search(query=query, max_results=5)
    except Exception as e:
        logger.error(f"[web_search_node] Tavily 오류: {e}")

    # 2순위: RSS 캐시
    if not docs:
        try:
            docs = search_rss_cache(query=original, top_k=5)
        except Exception as e:
            logger.error(f"[web_search_node] RSS 캐시 오류: {e}")

    # 3순위: 빈 결과여도 generate_node에서 GPT 지식으로 답변하도록 플래그 전달
    if not docs:
        docs = [{
            "title":    "웹검색 결과 없음",
            "content":  f"'{original}'에 대한 웹검색 결과를 가져오지 못했습니다. GPT 일반 지식으로 답변하세요.",
            "source":   "fallback",
            "category": "기타",
        }]

    trace = list(state.get("execution_trace", []))
    trace.append({
        "node":    "web_search_node",
        "summary": f"웹검색 → {len(docs)}건 (쿼리: {query[:30]})",
    })
    logger.info(f"[web_search_node] '{query[:40]}' → {len(docs)}건")

    return {
        "documents":       docs,
        "tool_name":       "web_search",
        "execution_trace": trace,
    }
