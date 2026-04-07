"""
AI Agent - Function Calling 기반 지능형 RAG 에이전트

[동작 흐름]
  1. 사용자 질문 입력
  2. LLM이 질문 분석 → 적절한 도구 자동 선택 (지능형 라우팅)
     - 단순 질문  → search_policy
     - 정확성 필요 → search_and_validate (자가 보정 포함)
     - 비교 질문  → compare_policies
     - 목록 조회  → list_policies
  3. 도구 실행 → 결과를 LLM에 전달
  4. LLM이 결과를 종합해 최종 답변 생성 (스트리밍)
  5. 필요 시 추가 도구 호출 반복 (최대 MAX_ITERATIONS 회)
"""
import json
import os
import sys

_BACKEND = os.path.dirname(__file__)
_WEEK06  = os.path.normpath(os.path.join(_BACKEND, "..", "..", "..", "week06-streamlit-ui", "minseon"))
sys.path.insert(0, _WEEK06)

from openai import OpenAI
from tools import TOOLS, execute_tool

CHAT_MODEL     = "gpt-4o-mini"
MAX_ITERATIONS = 5

SYSTEM_PROMPT = """당신은 청년 정책 전문 AI 상담사 '청년도우미'입니다.

## 사용 가능한 도구 (지능형 라우팅)
| 도구 | 언제 사용 |
|------|-----------|
| search_policy | 단순 사실 질문 (조건, 금액, 신청 방법) |
| search_and_validate | 복잡하거나 정확성이 중요한 질문 |
| compare_policies | "A랑 B 중 뭐가 나아?" 비교 질문 |
| list_policies | 어떤 정책이 있는지 물어볼 때 |

## 답변 규칙
1. 반드시 도구 검색 결과에 있는 내용만 사용하세요.
2. 금액·나이·소득 기준 등 수치는 문서 그대로 전달하세요.
3. 문서에 없는 내용은 "확인되지 않습니다"라고 답하세요.
4. 각 정보 뒤에 **[출처: 파일명]** 을 표시하세요.
5. 여러 정책이 해당되면 표(markdown table)로 비교하세요.
6. 답변 마지막에 관련 추가 질문 1~2개를 제안하세요.
7. 항상 한국어로 답변하세요.
8. 청년 정책과 관련 없는 질문은 정중히 거절하세요."""


class PolicyAgent:
    def __init__(self):
        self.client = OpenAI()
        self.conversation: list[dict] = []
        self._last_tool_calls: list[dict] = []
        self._last_hits: list[dict] = []

    def chat_stream(self, user_message: str):
        """
        Function Calling 기반 스트리밍 응답

        Yields dict:
          {"type": "tool_start", "tool": str, "args": dict}
          {"type": "tool_done",  "tool": str, "summary": str, "correction": dict|None}
          {"type": "text",       "content": str}
          {"type": "hits",       "hits": list}
          {"type": "tool_calls", "calls": list}
          {"type": "done"}
        """
        self._last_tool_calls = []
        self._last_hits = []

        self.conversation.append({"role": "user", "content": user_message})
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + self.conversation

        for _ in range(MAX_ITERATIONS):
            response = self.client.chat.completions.create(
                model=CHAT_MODEL,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )

            msg           = response.choices[0].message
            finish_reason = response.choices[0].finish_reason

            # ── 최종 답변 (도구 호출 없음) ───────────────────────
            if finish_reason == "stop" or not msg.tool_calls:
                answer = msg.content or ""
                self.conversation.append({"role": "assistant", "content": answer})

                # 문자 단위 스트리밍
                for char in answer:
                    yield {"type": "text", "content": char}

                yield {"type": "tool_calls", "calls": self._last_tool_calls}
                yield {"type": "hits",       "hits":  self._last_hits}
                yield {"type": "done"}
                return

            # ── 도구 호출 처리 ───────────────────────────────────
            messages.append(msg)

            for tc in msg.tool_calls:
                name = tc.function.name
                args = json.loads(tc.function.arguments)

                yield {"type": "tool_start", "tool": name, "args": args}

                result     = execute_tool(name, args)
                correction = result.get("self_correction")

                self._extract_hits(name, result)

                summary = self._summarize(name, result)
                self._last_tool_calls.append({
                    "tool":       name,
                    "args":       args,
                    "summary":    summary,
                    "correction": correction,
                })

                yield {
                    "type":       "tool_done",
                    "tool":       name,
                    "summary":    summary,
                    "correction": correction,
                }

                messages.append({
                    "role":         "tool",
                    "tool_call_id": tc.id,
                    "content":      json.dumps(result, ensure_ascii=False),
                })

        # MAX_ITERATIONS 초과
        yield {"type": "text",    "content": "처리 중 문제가 발생했습니다. 다시 질문해 주세요."}
        yield {"type": "done"}

    # ── 내부 헬퍼 ─────────────────────────────────────────────

    def _extract_hits(self, tool_name: str, result: dict):
        """도구 결과에서 검색 문서 추출"""
        if tool_name in ("search_policy", "search_and_validate"):
            for r in result.get("results", []):
                self._last_hits.append({
                    "source":     r["source"],
                    "similarity": r["similarity"],
                    "content":    r["content"],
                })
        elif tool_name == "compare_policies":
            for key in ("policy_a", "policy_b"):
                for r in result.get(key, {}).get("results", []):
                    self._last_hits.append({
                        "source":     r["source"],
                        "similarity": r["similarity"],
                        "content":    r["content"],
                    })

    def _summarize(self, tool_name: str, result: dict) -> str:
        if tool_name == "search_policy":
            return f"{result['count']}개 문서 검색됨" if result.get("found") else "관련 문서 없음"
        if tool_name == "list_policies":
            names = [p["name"] for p in result.get("policies", [])]
            return f"{len(names)}개 정책: {', '.join(names)}"
        if tool_name == "search_and_validate":
            sc   = result.get("self_correction", {})
            base = f"{result.get('count', 0)}개 문서 검색됨"
            if sc.get("corrected"):
                base += f" (쿼리 {sc['attempts']}회 자동 보정)"
            return base
        if tool_name == "compare_policies":
            a = result.get("policy_a", {}).get("count", 0)
            b = result.get("policy_b", {}).get("count", 0)
            return f"비교 검색 완료 (A:{a}개, B:{b}개)"
        return "완료"

    def reset(self):
        self.conversation.clear()
        self._last_tool_calls = []
        self._last_hits = []
