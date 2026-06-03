"""
advanced_rag.py - 비교용 Advanced RAG (Week 13 평가)
벡터 검색으로 과거 데이터를 가져와서 컨텍스트에 추가 (항상 검색)
"""
import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from storage import search_reports

load_dotenv()

_llm = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY", ""))


def answer(question: str, current_report: dict) -> dict:
    # 항상 벡터 검색 실행
    past_results = search_reports(question, limit=3)
    past_context = ""
    retrieved_contexts = []
    for r in past_results:
        date  = r.get("created_at", "")[:10]
        judge = r.get("judge_decision", "")[:300]
        repos = r.get("repos", [])
        top   = ", ".join(rp["name"] for rp in repos[:5])
        chunk = f"[{date}] 상위 레포: {top}\n분석: {judge}"
        past_context += chunk + "\n\n"
        retrieved_contexts.append(chunk)

    repos = current_report.get("repos", [])[:10]
    repo_summary = "\n".join([
        f"- {r['name']} (⭐{r.get('stars', 0):,}): {r.get('description', '')[:80]}"
        for r in repos
    ])

    context = f"""[현재 GitHub 트렌딩 분석]
트렌딩 레포: {repo_summary}
Judge 결론: {current_report.get('judge_decision', '')[:400]}

[과거 분석 데이터]
{past_context}
"""
    response = _llm.invoke(f"""{context}

현재 데이터와 과거 데이터를 함께 참고해서 다음 질문에 한국어로 답해주세요.
질문: {question}
""")
    return {
        "answer":   response.content,
        "contexts": retrieved_contexts if retrieved_contexts else [repo_summary[:500]],
    }
