"""
2주차 과제: 청년 정책/장학금 매칭 RAG 챗봇
Chunking된 데이터에서 키워드 기반 검색 후 Claude에게 답변 생성 요청
(벡터 DB 없이 간단한 키워드 매칭 — 3주차 임베딩 전 단계)
"""

import json
import os

from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

client = Anthropic()

# ── 설정 ──────────────────────────────────────────────
MODEL = "claude-sonnet-4-5-20250929"
MAX_TOKENS = 1024
CHUNKS_FILE = os.path.join(os.path.dirname(__file__), "chunks.json")

SYSTEM_PROMPT = """당신은 청년 정책 및 장학금 전문 상담 챗봇입니다.

역할:
- 사용자의 조건(나이, 소득, 취업상태 등)에 맞는 청년 정책과 장학금을 추천합니다.
- 정책 간 중복 수혜 가능 여부를 안내합니다.
- 신청 방법과 주의사항을 친절하게 설명합니다.

규칙:
- 제공된 데이터에 기반해서만 답변하세요. 데이터에 없는 내용은 "해당 정보는 제가 가진 데이터에 없습니다"라고 안내하세요.
- 한국어로 답변합니다.
- 금액, 조건 등 수치 정보는 정확하게 전달하세요.
"""

# ── 데이터 로딩 ───────────────────────────────────────

def load_chunks() -> list[dict]:
    """chunks.json에서 청크 데이터 로드"""
    if not os.path.exists(CHUNKS_FILE):
        print(f"  [경고] {CHUNKS_FILE} 파일이 없습니다.")
        print(f"  먼저 'python chunk_all.py'를 실행하세요.\n")
        return []

    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"  {len(chunks)}개 청크 로드 완료")
    return chunks


# ── 키워드 기반 검색 ──────────────────────────────────

def search_chunks(query: str, chunks: list[dict], top_k: int = 5) -> list[dict]:
    """
    간단한 키워드 매칭으로 관련 청크 검색
    (3주차 임베딩 도입 전 단계)
    """
    query_tokens = set(query.lower().replace(",", " ").split())

    scored = []
    for chunk in chunks:
        content_lower = chunk["content"].lower()
        title_lower = chunk["title"].lower()

        # 키워드 매칭 점수: 제목 매칭(가중치 3) + 본문 매칭(가중치 1)
        score = 0
        for token in query_tokens:
            if len(token) < 2:
                continue
            if token in title_lower:
                score += 3
            if token in content_lower:
                score += content_lower.count(token)

        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in scored[:top_k]]


def format_context(results: list[dict]) -> str:
    """검색 결과를 LLM 컨텍스트 문자열로 변환"""
    if not results:
        return "관련 데이터를 찾지 못했습니다."

    parts = []
    for r in results:
        parts.append(f"[{r['category']}/{r['title']}]\n{r['content']}")
    return "\n\n---\n\n".join(parts)


# ── 채팅 ──────────────────────────────────────────────

conversation: list[dict] = []


def chat(user_input: str, chunks: list[dict]) -> str:
    """RAG: 검색 → 컨텍스트 주입 → Claude 응답"""

    # 1) 관련 청크 검색
    results = search_chunks(user_input, chunks)
    context = format_context(results)

    # 2) 사용자 메시지에 컨텍스트 주입
    augmented_message = f"""사용자 질문: {user_input}

참고 데이터:
{context}

위 데이터를 바탕으로 사용자 질문에 답변해주세요."""

    conversation.append({"role": "user", "content": augmented_message})

    # 최근 10개 메시지만 유지
    if len(conversation) > 10:
        conversation[:] = conversation[-10:]

    # 3) Claude API 호출 (Streaming)
    full_response = ""
    with client.messages.stream(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=conversation,
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            full_response += text

    print()

    usage = stream.get_final_message().usage
    print(f"  [검색: {len(results)}건 | 입력: {usage.input_tokens} / 출력: {usage.output_tokens} 토큰]")

    conversation.append({"role": "assistant", "content": full_response})
    return full_response


# ── 메인 ──────────────────────────────────────────────

def main():
    print("╔══════════════════════════════════════════╗")
    print("║  청년 정책/장학금 매칭 RAG 챗봇          ║")
    print("╠══════════════════════════════════════════╣")
    print("║  명령어:                                 ║")
    print("║    quit   - 종료                         ║")
    print("║    reset  - 대화 초기화                  ║")
    print("║    search [키워드] - 데이터 직접 검색     ║")
    print("╚══════════════════════════════════════════╝")
    print()

    # 청크 데이터 로딩
    print("── 데이터 로딩 ──")
    chunks = load_chunks()
    if not chunks:
        return
    print()

    while True:
        try:
            user_input = input("[나] ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n종료합니다.")
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("종료합니다.")
            break

        if user_input.lower() == "reset":
            conversation.clear()
            print("대화가 초기화되었습니다.\n")
            continue

        # 직접 검색 모드
        if user_input.lower().startswith("search "):
            keyword = user_input[7:].strip()
            results = search_chunks(keyword, chunks, top_k=3)
            if not results:
                print("  검색 결과 없음\n")
            else:
                for r in results:
                    preview = r["content"][:100].replace("\n", " ")
                    print(f"  [{r['category']}/{r['title']}] {preview}...")
                print()
            continue

        print("[AI] ", end="")
        chat(user_input, chunks)
        print()


if __name__ == "__main__":
    main()
