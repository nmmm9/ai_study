"""
LLM 서비스 - OpenAI GPT 설정 및 대화 관리 유틸

[관심사 분리 역할]
  이 파일: OpenAI 클라이언트 설정, 토큰 추정, 대화 히스토리 관리 유틸
  chat.py:  터미널 CLI (출력, 명령어 처리, 상태 관리)
  app.py:   Streamlit UI (세션 상태, 화면 렌더링)
"""

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ── 설정 ──────────────────────────────────────────────
MODEL = "gpt-4o"
MAX_TOKENS = 1024
MAX_MESSAGES = 20
MAX_TOTAL_CHARS = 8000
SYSTEM_PROMPT = "당신은 친절한 AI 어시스턴트입니다. 한국어로 답변합니다."

client = OpenAI()


# ── 토큰 유틸 ──────────────────────────────────────────
def estimate_tokens(text: str) -> int:
    """한국어 기준 토큰 수 추정 (글자수 × 1.5 근사치)"""
    return int(len(text) * 1.5)


def get_conversation_chars(conversation: list[dict]) -> int:
    """현재 대화 히스토리의 총 글자 수"""
    return sum(len(msg["content"]) for msg in conversation)


# ── 대화 히스토리 관리 ─────────────────────────────────
def trim_conversation(conversation: list[dict]) -> None:
    """
    Sliding Window 토큰 관리 (in-place 수정)

    1) 메시지 개수 제한 (MAX_MESSAGES)
    2) 글자 수 기반 제한 (MAX_TOTAL_CHARS)
    """
    if len(conversation) > MAX_MESSAGES:
        del conversation[:-MAX_MESSAGES]

    while get_conversation_chars(conversation) > MAX_TOTAL_CHARS and len(conversation) > 2:
        conversation.pop(0)
