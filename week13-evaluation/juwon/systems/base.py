"""
base.py - 3개 시스템 공통 유틸리티

Supabase pgvector 연결 + 임베딩 + 컨텍스트 조립
week12와 동일한 Supabase를 공유해서 공정한 비교 가능
"""
import os
from openai import OpenAI
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
_supabase: Client | None = None


def get_supabase() -> Client:
    global _supabase
    if _supabase is None:
        _supabase = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_KEY"],
        )
    return _supabase


def embed(text: str) -> list[float]:
    resp = _openai.embeddings.create(
        model="text-embedding-3-small",
        input=text[:8000],
    )
    return resp.data[0].embedding


def vector_search(query: str, limit: int = 3) -> list[dict]:
    """pgvector 코사인 유사도 검색"""
    vector = embed(query)
    result = get_supabase().rpc("search_trend_reports", {
        "query_embedding": vector,
        "match_count": limit,
    }).execute()
    return result.data or []


def build_context(reports: list[dict]) -> str:
    """검색 결과를 LLM 컨텍스트 텍스트로 변환"""
    parts = []
    for r in reports:
        date      = r.get("created_at", "")[:10]
        lang      = r.get("language") or "전체"
        repos     = r.get("repos", [])
        top_repos = ", ".join(rp["name"] for rp in repos[:5])
        judge     = r.get("judge_decision", "")[:400]
        parts.append(f"[{date} | {lang}]\n상위 레포: {top_repos}\n분석: {judge}")
    return "\n\n---\n\n".join(parts)


def llm_answer(context: str, question: str) -> str:
    """컨텍스트 기반 LLM 답변 생성"""
    resp = _openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "당신은 GitHub 기술 트렌드 전문 어시스턴트입니다. 제공된 데이터를 바탕으로 한국어로 답변하세요."},
            {"role": "user",   "content": f"[참고 데이터]\n{context}\n\n질문: {question}"},
        ],
        max_tokens=512,
    )
    return resp.choices[0].message.content or ""


def expand_queries(question: str, n: int = 3) -> list[str]:
    """Multi-Query: 질문을 여러 표현으로 확장"""
    import json
    try:
        resp = _openai.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=200,
            messages=[
                {"role": "system", "content": "주어진 질문을 다른 표현으로 변형해서 JSON 배열로만 응답하세요. 예: [\"쿼리1\", \"쿼리2\"]"},
                {"role": "user",   "content": f"질문: {question}\n{n}가지 다른 표현으로 변형해주세요."},
            ],
        )
        raw = resp.choices[0].message.content or "[]"
        queries = json.loads(raw)
        return [question] + [q for q in queries if isinstance(q, str)][:n]
    except Exception:
        return [question]
