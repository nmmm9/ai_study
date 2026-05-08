"""
재순위화 서비스 - GPT로 검색 결과 재순위화

초기 검색(top_k * 3 후보)에서 더 많은 청크를 가져온 뒤,
GPT에게 질문과 각 청크의 관련성을 점수화하도록 요청해
실제 top_k개를 선별합니다.

[사용 시나리오]
  - 벡터 유사도만으로는 의미 파악이 부족할 때 (예: 짧은 질문, 동음이의어)
  - GPT가 질문 의도를 더 정확히 파악해 관련성 높은 청크를 우선 선택
"""

import json

from openai import OpenAI

RERANK_MODEL = "gpt-4o-mini"


def rerank(query: str, hits: list[dict], top_k: int) -> list[dict]:
    """
    GPT를 사용해 검색 결과를 재순위화

    Args:
        query: 사용자 원본 질문
        hits:  초기 검색 결과 목록 (각 항목: {content, metadata, similarity})
        top_k: 최종 반환할 개수

    Returns:
        GPT 관련성 점수 기준으로 재정렬된 상위 top_k 결과
        실패 시 원래 유사도 순서대로 top_k 반환 (fallback)
    """
    if len(hits) <= top_k:
        return hits

    candidates = [
        {"id": i, "content": h["content"][:400]}  # 토큰 절약: 앞 400자만
        for i, h in enumerate(hits)
    ]

    prompt = (
        f"다음 질문에 대해 각 문서 청크의 관련성을 0~10 점수로 평가하세요.\n\n"
        f"질문: {query}\n\n"
        f"문서 청크 목록 (JSON):\n{json.dumps(candidates, ensure_ascii=False)}\n\n"
        f"각 청크의 id와 score를 JSON 배열로만 반환하세요. "
        f'예시: [{{"id": 0, "score": 8}}, {{"id": 1, "score": 3}}]'
    )

    try:
        client = OpenAI()
        response = client.chat.completions.create(
            model=RERANK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=300,
        )
        raw = response.choices[0].message.content.strip()

        # GPT가 배열 또는 {"scores": [...]} 형태로 반환할 수 있음
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            scores_list = next(
                (v for v in parsed.values() if isinstance(v, list)),
                []
            )
        else:
            scores_list = parsed

        score_map = {
            item["id"]: item["score"]
            for item in scores_list
            if isinstance(item, dict) and "id" in item and "score" in item
        }

        ranked = sorted(range(len(hits)), key=lambda i: score_map.get(i, 0), reverse=True)
        return [hits[i] for i in ranked[:top_k]]

    except Exception:
        # API 오류 또는 파싱 실패 시 원래 유사도 순서 유지
        return hits[:top_k]
