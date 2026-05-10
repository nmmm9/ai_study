from openai import OpenAI

from retriever import retrieve_relevant_chunks


client = OpenAI()


def build_context(chunks: list[dict]) -> str:
    context_parts = []

    for index, chunk in enumerate(chunks, start=1):
        metadata = chunk["metadata"]

        source = metadata.get("source", "unknown")
        document_type = metadata.get("document_type", "unknown")
        page = metadata.get("page")
        section = metadata.get("section")

        source_info = f"출처 {index}: {source}, 문서 유형: {document_type}"

        if page is not None:
            source_info += f", 페이지: {page}"

        if section is not None:
            source_info += f", 섹션: {section}"

        context_parts.append(
            f"[{source_info}]\n{chunk['text']}"
        )

    return "\n\n".join(context_parts)


def answer_question(user_question: str) -> str:
    relevant_chunks = retrieve_relevant_chunks(user_question, top_k=3)

    if not relevant_chunks:
        return "관련 문서를 찾지 못했습니다. 질문에 포함된 핵심 단어를 조금 더 구체적으로 입력해 주세요."

    context = build_context(relevant_chunks)

    prompt = f"""
아래 참고 문서를 바탕으로 사용자의 질문에 답변하세요.

규칙:
1. 참고 문서에 있는 내용만 사용하세요.
2. 참고 문서에 없는 내용은 추측하지 말고 모른다고 답하세요.
3. 답변 마지막에 사용한 출처를 간단히 표시하세요.
4. 한국어로 답변하세요.

[참고 문서]
{context}

[사용자 질문]
{user_question}
"""

    response = client.responses.create(
        model="gpt-5.2",
        input=[
            {
                "role": "system",
                "content": "너는 회사 내부 문서를 기반으로 답변하는 사내 업무 도우미야.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    return response.output_text


if __name__ == "__main__":
    print("RAG 사내 문서 챗봇입니다.")
    print("종료하려면 exit 또는 quit을 입력하세요.")
    print("=" * 50)

    while True:
        user_question = input("\n질문: ").strip()

        if user_question.lower() in ["exit", "quit"]:
            print("종료합니다.")
            break

        answer = answer_question(user_question)

        print("\n답변:")
        print(answer)