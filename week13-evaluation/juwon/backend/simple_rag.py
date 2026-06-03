"""
simple_rag.py - 비교용 Simple RAG (Week 13 평가)
RAG 없이 현재 분석 결과만으로 GPT가 답변 (베이스라인)
"""
import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

_llm = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY", ""))


def answer(question: str, current_report: dict) -> dict:
    repos = current_report.get("repos", [])[:10]
    repo_summary = "\n".join([
        f"- {r['name']} (⭐{r.get('stars', 0):,}): {r.get('description', '')[:80]}"
        for r in repos
    ])
    context = f"""[현재 GitHub 트렌딩 분석]
트렌딩 레포: {repo_summary}

Judge 결론: {current_report.get('judge_decision', '')[:500]}
"""
    response = _llm.invoke(f"""{context}

위 정보를 바탕으로 다음 질문에 한국어로 답해주세요.
질문: {question}
""")
    return {
        "answer":   response.content,
        "contexts": [repo_summary[:500]],
    }
