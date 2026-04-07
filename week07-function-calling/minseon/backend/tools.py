"""
Function Calling 도구 정의 및 구현

도구 목록:
1. search_policy       - RAG 기반 정책 검색
2. list_policies       - 전체 정책 목록 조회
3. search_and_validate - 자가 보정 검색 (관련성 낮으면 쿼리 재작성 후 최대 3회 재시도)
4. compare_policies    - 두 정책 동시 비교 검색
"""
import os
import sys

# week06 services 재사용
_WEEK06 = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "week06-streamlit-ui", "minseon"))
sys.path.insert(0, _WEEK06)

from openai import OpenAI
from services.embedding_service import embed_texts
from services.vector_store import VectorStore

_DB_PATH = os.path.join(_WEEK06, "chroma_db")
_store: VectorStore | None = None


def get_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore(_DB_PATH)
    return _store


# ── OpenAI Function Calling 도구 스키마 ──────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_policy",
            "description": "청년 정책 문서에서 관련 정보를 검색합니다. 특정 정책의 조건, 금액, 신청 방법 등을 찾을 때 사용하세요.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "검색할 질문 또는 키워드 (예: '청년도약계좌 가입 조건')"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "반환할 최대 문서 수 (기본값: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_policies",
            "description": "현재 데이터베이스에 저장된 모든 청년 정책 목록을 반환합니다. 어떤 정책 정보가 있는지 물어볼 때 사용하세요.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_and_validate",
            "description": (
                "검색 후 결과의 관련성을 자동 검증합니다. "
                "유사도가 낮으면 쿼리를 재작성하여 최대 3번 재시도합니다. "
                "복잡한 질문이나 정확한 정보가 필요할 때 사용하세요."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "원본 질문"
                    },
                    "min_similarity": {
                        "type": "number",
                        "description": "최소 유사도 임계값 0.0~1.0 (기본값: 0.3)",
                        "default": 0.3
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_policies",
            "description": "두 청년 정책을 각각 검색하여 비교 가능한 형태로 반환합니다. 'A랑 B 중 뭐가 나아?' 같은 비교 질문에 사용하세요.",
            "parameters": {
                "type": "object",
                "properties": {
                    "policy_a": {
                        "type": "string",
                        "description": "첫 번째 정책 이름 또는 키워드"
                    },
                    "policy_b": {
                        "type": "string",
                        "description": "두 번째 정책 이름 또는 키워드"
                    }
                },
                "required": ["policy_a", "policy_b"]
            }
        }
    }
]


# ── 도구 실행 디스패처 ────────────────────────────────────────

def execute_tool(name: str, args: dict) -> dict:
    if name == "search_policy":
        return _search_policy(**args)
    elif name == "list_policies":
        return _list_policies()
    elif name == "search_and_validate":
        return _search_and_validate(**args)
    elif name == "compare_policies":
        return _compare_policies(**args)
    return {"error": f"알 수 없는 도구: {name}"}


# ── 도구 구현 ─────────────────────────────────────────────────

def _search_policy(query: str, top_k: int = 5) -> dict:
    try:
        store = get_store()
        query_vector = embed_texts([query])[0]
        hits = store.hybrid_search(
            query=query,
            query_vector=query_vector,
            top_k=top_k,
            threshold=0.2,
            max_per_source=2,
        )
    except Exception as e:
        return {"found": False, "error": str(e)}

    if not hits:
        return {"found": False, "message": "관련 문서를 찾지 못했습니다."}

    return {
        "found": True,
        "count": len(hits),
        "results": [
            {
                "source": h["metadata"]["source"],
                "similarity": round(h["similarity"], 3),
                "content": h["content"][:600],
            }
            for h in hits
        ],
    }


def _list_policies() -> dict:
    try:
        sources = get_store().get_sources()
        return {
            "count": len(sources),
            "policies": [
                {"name": s["source"].replace(".md", ""), "chunks": s["chunks"]}
                for s in sources
            ],
        }
    except Exception as e:
        return {"error": str(e)}


def _search_and_validate(query: str, min_similarity: float = 0.3) -> dict:
    """
    자가 보정 검색:
    1. 검색 실행
    2. 유사도가 min_similarity 미만이면 LLM으로 쿼리 재작성
    3. 최대 MAX_RETRIES 회 반복
    """
    MAX_RETRIES = 3
    history = []
    current_query = query

    for attempt in range(MAX_RETRIES):
        result = _search_policy(current_query, top_k=7)
        history.append({"attempt": attempt + 1, "query": current_query})

        if not result.get("found"):
            if attempt < MAX_RETRIES - 1:
                current_query = _rephrase_query(query, current_query, attempt)
            continue

        best_sim = max(r["similarity"] for r in result["results"])
        history[-1]["best_similarity"] = round(best_sim, 3)

        if best_sim >= min_similarity:
            result["self_correction"] = {
                "attempts": attempt + 1,
                "final_query": current_query,
                "history": history,
                "corrected": attempt > 0,
            }
            return result

        # 유사도 낮음 → 쿼리 재작성
        if attempt < MAX_RETRIES - 1:
            current_query = _rephrase_query(query, current_query, attempt)

    # 최대 재시도 후 최선의 결과 반환
    result["self_correction"] = {
        "attempts": MAX_RETRIES,
        "final_query": current_query,
        "history": history,
        "corrected": True,
        "warning": "최대 재시도 횟수 도달. 관련성이 낮을 수 있습니다.",
    }
    return result


def _rephrase_query(original: str, current: str, attempt: int) -> str:
    """LLM으로 검색 쿼리 재작성 (자가 보정 핵심 로직)"""
    prompts = [
        f"다음 질문을 청년 정책 검색에 적합한 키워드 중심으로 재작성해줘 (한 줄만): {current}",
        f"다음 질문의 핵심 단어만 추출해서 검색어로 만들어줘 (한 줄만): {original}",
        f"다음 질문과 관련된 청년 정책 이름을 포함한 검색어를 만들어줘 (한 줄만): {original}",
    ]
    try:
        resp = OpenAI().chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompts[attempt % len(prompts)]}],
            max_tokens=60,
            temperature=0,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return current


def _compare_policies(policy_a: str, policy_b: str) -> dict:
    """두 정책 각각 검색 후 비교용 결과 반환"""
    return {
        "policy_a": {"query": policy_a, **_search_policy(policy_a, top_k=4)},
        "policy_b": {"query": policy_b, **_search_policy(policy_b, top_k=4)},
    }
