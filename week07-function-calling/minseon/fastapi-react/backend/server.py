"""
7주차: Function Calling + Advanced RAG 백엔드

[Function Calling 흐름]
  사용자 질문
    → GPT에게 질문 + tools(JSON 스키마) 전달
    → GPT가 의도 파악 → 함수 선택
    → 함수 실행 (RAG 파이프라인 or 목록 조회)
    → 결과를 GPT에게 전달 → 최종 답변 스트리밍
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

# ── 경로 설정 ──────────────────────────────────────────
_BACKEND = os.path.dirname(__file__)
_WEEK06  = os.path.join(_BACKEND, "..", "..", "..", "..", "week06-streamlit-ui", "minseon")
sys.path.insert(0, _WEEK06)

from rag_pipeline import AdvancedRagPipeline
from services.cost_tracker import CostTracker

load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

app = FastAPI(title="청년도우미 Function Calling API v3")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── RAG 초기화 ─────────────────────────────────────────
try:
    _rag = AdvancedRagPipeline()
    _rag.auto_index_data_dir()
    print("[OK] RAG 파이프라인 초기화 완료")
except Exception as e:
    print(f"[WARN] RAG 초기화 실패: {e}")
    _rag = None

# ── 대화 이력 설정 ────────────────────────────────────
# 저장 위치: backend/conversation.json
CONV_FILE = Path(__file__).parent / "conversation.json"
MAX_TURNS = 10  # 최근 10턴만 유지 (= 20개 메시지)
               # 이유: 오래된 대화는 현재 질문과 관련성이 낮고 토큰만 낭비

def _load_conversation() -> list[dict]:
    """서버 시작 시 파일에서 대화 이력 불러오기"""
    if CONV_FILE.exists():
        try:
            return json.loads(CONV_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def _save_conversation(conv: list[dict]):
    """
    대화 이력을 파일에 저장
    저장 내용: 사용자 질문 + AI 최종 답변만
    저장 안 함: RAG 컨텍스트, 함수 결과 (매번 새로 검색하므로 불필요)
    → 이것이 핵심 토큰 절약 전략
    """
    CONV_FILE.write_text(json.dumps(conv, ensure_ascii=False, indent=2), encoding="utf-8")

_conversation: list[dict] = _load_conversation()


# ════════════════════════════════════════════════════════
# 함수 정의 (GPT가 선택해서 호출할 실제 함수들)
# ════════════════════════════════════════════════════════

def search_youth_policy(query: str, top_k: int = 5) -> dict:
    """
    Advanced RAG 파이프라인으로 청년 정책 검색
    Pre-retrieval → Retrieval → Post-retrieval → 컨텍스트 반환
    """
    if _rag is None:
        return {"error": "RAG 파이프라인이 초기화되지 않았습니다."}

    tracker = CostTracker()

    # Pre-retrieval: 쿼리 확장
    tracker.start_stage("pre")
    queries = _rag._generate_queries(query, tracker)
    tracker.end_stage("pre")

    # Retrieval: 하이브리드 검색
    tracker.start_stage("retrieval")
    candidates = _rag._hybrid_search_all(queries, top_k, 0.2, 2, tracker)
    tracker.end_stage("retrieval")

    # Post-retrieval: 리랭킹
    tracker.start_stage("post")
    final_hits = _rag._post_process(query, candidates, top_k, False, tracker)
    tracker.end_stage("post")

    # 컨텍스트 구성
    context = "\n\n".join([
        f"[{h['metadata']['source']}]\n{h['content']}"
        for h in final_hits
    ])

    cost = tracker.get_summary()

    return {
        "query": query,
        "query_type": _rag._last_query_type,
        "queries_generated": queries,
        "hits_count": len(final_hits),
        "context": context,
        "hits": [
            {
                "source": h["metadata"]["source"],
                "content": h["content"][:200],
                "similarity": round(h["similarity"], 3),
            }
            for h in final_hits
        ],
        "cost_summary": cost,
    }


def list_policies() -> dict:
    """보유한 청년 정책 문서 목록 반환"""
    if _rag is None:
        return {"error": "RAG 파이프라인이 초기화되지 않았습니다."}
    sources = _rag.get_indexed_sources()
    return {
        "count": len(sources),
        "policies": [s["source"].replace(".md", "").replace(".txt", "") for s in sources],
    }


# ════════════════════════════════════════════════════════
# JSON 스키마 정의 (GPT에게 전달할 tools)
# ════════════════════════════════════════════════════════

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_youth_policy",
            "description": (
                "청년 지원 정책(주거·취업·금융·교육·복지 등) 관련 질문에 답하기 위해 "
                "Advanced RAG 파이프라인으로 정책 문서를 검색합니다. "
                "청년 정책에 관한 모든 질문에 반드시 이 함수를 사용하세요."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "검색할 청년 정책 관련 질문 또는 키워드",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "검색 결과 최대 개수 (기본값: 5)",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_policies",
            "description": (
                "현재 시스템에 인덱싱된 청년 정책 문서 목록을 조회합니다. "
                "'어떤 정책을 알고 있어?', '무슨 정보가 있어?' 같은 질문에 사용하세요."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]

FUNCTION_MAP = {
    "search_youth_policy": search_youth_policy,
    "list_policies":       list_policies,
}


# ════════════════════════════════════════════════════════
# 요청 모델
# ════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"


# ════════════════════════════════════════════════════════
# 채팅 API (Function Calling + SSE 스트리밍)
# ════════════════════════════════════════════════════════

@app.post("/chat")
async def chat(req: ChatRequest):
    async def generate():
        global _conversation

        # GPT에게 전달할 messages (대화 이력 포함)
        messages = [
            {
                "role": "system",
                "content": (
                    "당신은 청년 정책 전문 AI 상담사 '청년도우미'입니다.\n"
                    "청년 정책(주거·취업·금융·교육·복지) 관련 질문에는 반드시 "
                    "search_youth_policy 함수를 호출해 정확한 문서 기반 답변을 제공하세요.\n"
                    "보유 정책 목록 질문에는 list_policies 함수를 사용하세요.\n"
                    "청년 정책과 관련 없는 질문에는 함수를 사용하지 말고 "
                    "'청년 정책 관련 질문을 해주세요.'라고 안내하세요.\n"
                    "한국어로 친절하게 답변하세요."
                ),
            },
        ] + _conversation + [
            {"role": "user", "content": req.message}
        ]

        # ── 1단계: GPT가 함수 호출 여부 결정 ──
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )
        msg = response.choices[0].message
        rag_result = None

        # ── 2단계: 함수 호출 ──
        if msg.tool_calls:
            messages.append(msg)

            for tc in msg.tool_calls:
                name = tc.function.name
                args = json.loads(tc.function.arguments)

                # 함수 호출 시작 이벤트
                yield f"data: {json.dumps({'type':'tool_call','name':name,'args':args}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0)

                # 실제 함수 실행
                func = FUNCTION_MAP.get(name)
                result = func(**args) if func else {"error": "알 수 없는 함수"}

                if name == "search_youth_policy":
                    rag_result = result
                    # 파이프라인 단계 이벤트
                    yield f"data: {json.dumps({'type':'pipeline','query_type':result.get('query_type','single'),'queries':result.get('queries_generated',[]),'hits_count':result.get('hits_count',0)}, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0)

                # 함수 결과 이벤트
                yield f"data: {json.dumps({'type':'tool_result','name':name,'hits':result.get('hits',[])}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0)

                # GPT에게 전달할 결과 (context만 전달, 나머지는 UI용)
                gpt_result = {k: v for k, v in result.items() if k != "hits"}
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(gpt_result, ensure_ascii=False),
                })

            # ── 3단계: 최종 답변 스트리밍 ──
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                stream=True,
            )
            full_response = ""
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    full_response += delta
                    yield f"data: {json.dumps({'type':'text','content':delta}, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0)

        else:
            # 함수 없이 직접 답변
            yield f"data: {json.dumps({'type':'tool_call','name':None,'args':{}}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0)

            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                stream=True,
            )
            full_response = ""
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    full_response += delta
                    yield f"data: {json.dumps({'type':'text','content':delta}, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0)

        # 대화 이력 업데이트 (질문 + 최종 답변만 저장, RAG 컨텍스트 제외)
        _conversation.append({"role": "user",      "content": req.message})
        _conversation.append({"role": "assistant",  "content": full_response})

        # 최근 MAX_TURNS턴만 유지 (오래된 대화 자동 삭제)
        if len(_conversation) > MAX_TURNS * 2:
            _conversation[:] = _conversation[-(MAX_TURNS * 2):]

        # 파일에 저장 (서버 재시작해도 유지)
        _save_conversation(_conversation)

        yield f"data: {json.dumps({'type':'done'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/conversation")
def get_conversation():
    """저장된 대화 이력 반환 (프론트엔드 새로고침 시 복원용)"""
    return _conversation

@app.delete("/conversation")
def clear_conversation():
    """대화 이력 초기화 (메모리 + 파일 모두)"""
    global _conversation
    _conversation = []
    _save_conversation(_conversation)
    return {"ok": True}


@app.get("/policies")
def get_policies():
    return list_policies()


@app.get("/health")
def health():
    return {"status": "ok", "rag": _rag is not None}
