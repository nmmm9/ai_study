"""
1주차 과제: OpenAI API 연동 - RAG 터미널 챗봇
RAG (Retrieval-Augmented Generation)를 활용한 문서 기반 질의응답 시스템
"""

import os
from dotenv import load_dotenv
from openai import OpenAI
from document_processor import DocumentProcessor

load_dotenv()

# ── 설정 ──────────────────────────────────────────────
MODEL = "gpt-4o-mini"
SYSTEM_PROMPT = """당신은 제공된 문서를 기반으로 답변하는 AI 어시스턴트입니다.
다음 규칙을 따라주세요:
1. 제공된 컨텍스트(문서 내용)를 기반으로 답변합니다.
2. 컨텍스트에 없는 내용은 "제공된 문서에서 해당 정보를 찾을 수 없습니다"라고 답변합니다.
3. 답변은 한국어로 명확하고 간결하게 작성합니다.
4. 가능한 경우 문서의 원문을 인용하여 답변합니다."""

EMBEDDING_CACHE_FILE = "embeddings_cache.pkl"
PDF_FILE = "스터디_1주차_rag의_개념.pdf"

# ── 상태 ──────────────────────────────────────────────
client = OpenAI()
doc_processor = DocumentProcessor(client)
conversation: list[dict] = []
total_input_tokens = 0
total_output_tokens = 0


def initialize_rag_system():
    """RAG 시스템 초기화 (문서 로드 및 임베딩 생성)"""
    global doc_processor

    print("╔══════════════════════════════════════════════╗")
    print("║        RAG 시스템 초기화 중...              ║")
    print("╚══════════════════════════════════════════════╝\n")

    # 캐시된 임베딩이 있으면 로드
    if os.path.exists(EMBEDDING_CACHE_FILE):
        print("📦 캐시된 임베딩 데이터를 로드합니다...\n")
        doc_processor.load_embeddings(EMBEDDING_CACHE_FILE)
    else:
        # 없으면 PDF 로드하고 임베딩 생성
        if not os.path.exists(PDF_FILE):
            print(f"❌ 오류: PDF 파일을 찾을 수 없습니다: {PDF_FILE}")
            print("현재 디렉토리에 PDF 파일을 배치해주세요.\n")
            return False

        doc_processor.load_pdf(PDF_FILE, chunk_size=500)
        doc_processor.create_embeddings()
        doc_processor.save_embeddings(EMBEDDING_CACHE_FILE)

    print("✅ RAG 시스템 초기화 완료!\n")
    return True


def chat_with_rag(user_input: str) -> str:
    """RAG 기반 대화 처리"""
    global total_input_tokens, total_output_tokens

    # 1. 관련 문서 청크 검색
    print("\n🔍 관련 문서 검색 중...")
    similar_chunks = doc_processor.search_similar_chunks(user_input, top_k=3)

    # 검색 결과 출력
    print("\n📚 찾은 관련 문서:")
    for i, (chunk, score) in enumerate(similar_chunks, 1):
        preview = chunk[:100] + "..." if len(chunk) > 100 else chunk
        print(f"  [{i}] (유사도: {score:.3f}) {preview}")

    # 2. 컨텍스트 구성
    context = "\n\n".join([f"[문서 {i}]\n{chunk}"
                           for i, (chunk, _) in enumerate(similar_chunks, 1)])

    # 3. 프롬프트 생성
    prompt = f"""다음은 참고할 문서 내용입니다:

{context}

사용자 질문: {user_input}

위 문서를 바탕으로 질문에 답변해주세요."""

    # 4. GPT API 호출
    conversation.append({"role": "user", "content": prompt})

    print("\n💭 AI 답변 생성 중...\n")
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            *conversation
        ],
        temperature=0.7,
        stream=True
    )

    # 5. 스트리밍 응답 처리
    full_response = ""
    print("[AI] ", end="", flush=True)
    for chunk in response:
        if chunk.choices[0].delta.content:
            text = chunk.choices[0].delta.content
            print(text, end="", flush=True)
            full_response += text

    print("\n")

    # 6. 대화 기록 저장
    conversation.append({"role": "assistant", "content": full_response})

    # 토큰 사용량 추정 (정확한 계산을 위해서는 tiktoken 라이브러리 필요)
    input_tokens = len(prompt.split()) * 1.3
    output_tokens = len(full_response.split()) * 1.3
    total_input_tokens += int(input_tokens)
    total_output_tokens += int(output_tokens)

    print(f"💡 [예상 토큰: 입력 ~{int(input_tokens)} / 출력 ~{int(output_tokens)}]\n")

    return full_response


def show_usage():
    """토큰 사용량 출력"""
    print("\n── 토큰 사용량 (추정치) ──")
    print(f"  누적 입력: ~{total_input_tokens} 토큰")
    print(f"  누적 출력: ~{total_output_tokens} 토큰")
    print(f"  총 합계:   ~{total_input_tokens + total_output_tokens} 토큰")
    print(f"  대화 메시지 수: {len(conversation)//2}개\n")


def main():
    """메인 실행 함수"""
    # RAG 시스템 초기화
    if not initialize_rag_system():
        return

    print("╔══════════════════════════════════════════════╗")
    print("║     RAG 기반 문서 질의응답 챗봇             ║")
    print("╠══════════════════════════════════════════════╣")
    print("║  명령어:                                     ║")
    print("║    quit   - 종료                             ║")
    print("║    reset  - 대화 초기화                      ║")
    print("║    usage  - 토큰 사용량 확인                 ║")
    print("║    reload - 문서 재로드                      ║")
    print("╚══════════════════════════════════════════════╝")
    print()

    while True:
        try:
            user_input = input("💬 [질문] ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n종료합니다.")
            show_usage()
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            show_usage()
            print("종료합니다.")
            break

        if user_input.lower() == "reset":
            conversation.clear()
            print("✅ 대화가 초기화되었습니다.\n")
            continue

        if user_input.lower() == "usage":
            show_usage()
            continue

        if user_input.lower() == "reload":
            print("\n📂 문서를 재로드합니다...\n")
            if os.path.exists(EMBEDDING_CACHE_FILE):
                os.remove(EMBEDDING_CACHE_FILE)
            initialize_rag_system()
            continue

        # RAG 기반 대화 실행
        chat_with_rag(user_input)


if __name__ == "__main__":
    main()
