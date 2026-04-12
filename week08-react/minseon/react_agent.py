"""
react_agent.py
──────────────
두 가지 에이전트 패턴으로 OOTD를 추천합니다.

  1. ReActAgent         — Thought → Action → Observation 반복 루프
  2. PlanAndExecuteAgent — Plan(계획 수립) → Execute(단계별 실행) → Synthesize(종합)

두 패턴 모두 함수호출.py에 정의된 TOOL_SCHEMAS / execute_tool을 사용합니다.
"""

import json
import textwrap
import anthropic

from function_calling import TOOL_SCHEMAS, execute_tool

client = anthropic.Anthropic()

# ── ANSI 색상 (터미널 가독성) ───────────────────────────────
BOLD   = "\033[1m"
CYAN   = "\033[96m"
YELLOW = "\033[93m"
GREEN  = "\033[92m"
MAGENTA= "\033[95m"
RESET  = "\033[0m"
DIM    = "\033[2m"


def _print_divider(char: str = "─", width: int = 60) -> None:
    print(DIM + char * width + RESET)


def _print_step(icon: str, label: str, text: str, color: str = CYAN) -> None:
    print(f"\n{color}{BOLD}{icon} {label}{RESET}")
    for line in text.strip().splitlines():
        print(f"   {line}")


# ══════════════════════════════════════════════════════════════
# ① ReAct Agent
#    Thought → Action → Observation 을 stop_reason == "end_turn"
#    이 될 때까지 반복합니다.
# ══════════════════════════════════════════════════════════════

_REACT_SYSTEM = """\
당신은 매일 아침 날씨에 맞는 OOTD 코디를 추천하는 전문 스타일리스트 AI입니다.
ReAct (Reasoning + Acting) 방식으로 단계적으로 사고하며 문제를 해결합니다.

## 응답 규칙
1. 도구를 호출하기 **전에** 반드시 아래 형식으로 사고 과정을 작성하세요:
   **[Thought]** 지금 무엇을 알고 있고, 다음에 무엇을 확인해야 하는지 1~3문장으로 기술.

2. 도구 결과를 받은 후에는 반드시:
   **[Observation]** 결과를 해석하고 다음 행동에 어떤 영향을 주는지 기술.

3. 모든 정보가 갖춰지면:
   **[Final Answer]** 헤더 아래에 완성된 OOTD 추천을 작성하세요.

## 최종 추천 형식
**[Final Answer]**
### 📍 오늘의 날씨 요약
### ☂️ 우산 알림          ← 비/눈/고습도 시 반드시 포함
### 👗 추천 코디           ← 상의 → 하의 → 아우터 → 신발 → 액세서리
### 🎨 색상 포인트
### 💡 스타일링 팁

## 핵심 원칙
- 비·눈이 오거나 습도 ≥ 80 % 이면 반드시 우산 알림 강조
- 옷장에 실제로 있는 아이템만 사용
- 일교차가 크면 레이어링 방법 제안
"""


class ReActAgent:
    """
    ReAct 패턴 OOTD 에이전트

    루프:
      Claude 응답 → Thought 출력 → tool_use 블록 → execute_tool → tool_result 삽입
      → stop_reason == "end_turn" 이면 Final Answer 출력 후 종료
    """

    MAX_STEPS = 10  # 무한 루프 방지

    def run(self, location: str, user_request: str = "") -> str:
        """
        에이전트를 실행하고 최종 추천 텍스트를 반환합니다.
        실행 중 각 Thought / Action / Observation 단계를 터미널에 출력합니다.
        """
        query = self._build_query(location, user_request)

        print(f"\n{BOLD}{MAGENTA}{'━'*60}{RESET}")
        print(f"{BOLD}{MAGENTA}  🤖 ReAct 에이전트 시작{RESET}")
        print(f"{BOLD}{MAGENTA}{'━'*60}{RESET}")
        print(f"  📍 위치  : {location}")
        if user_request:
            print(f"  📝 요청  : {user_request}")

        messages: list[dict] = [{"role": "user", "content": query}]
        final_answer = ""
        step = 0

        while step < self.MAX_STEPS:
            step += 1
            _print_divider()
            print(f"{DIM}  [Step {step}]{RESET}")

            response = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=2048,
                system=_REACT_SYSTEM,
                tools=TOOL_SCHEMAS,
                messages=messages,
            )

            # ── 텍스트 블록 출력 (Thought / Observation / Final Answer) ──
            for block in response.content:
                if block.type == "text" and block.text.strip():
                    text = block.text.strip()
                    if "[Thought]" in text:
                        _print_step("💭", "Thought", text.replace("**[Thought]**", "").strip(), YELLOW)
                    elif "[Observation]" in text:
                        _print_step("👁", "Observation", text.replace("**[Observation]**", "").strip(), CYAN)
                    elif "[Final Answer]" in text:
                        _print_step("✨", "Final Answer", text.replace("**[Final Answer]**", "").strip(), GREEN)
                        final_answer = text
                    else:
                        print(f"\n{text}")

            # ── 종료 조건 ──────────────────────────────────────────────
            if response.stop_reason == "end_turn":
                break

            # ── 도구 실행 (Action + Observation) ──────────────────────
            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []

                for block in response.content:
                    if block.type == "tool_use":
                        # Action 출력
                        inputs_str = json.dumps(block.input, ensure_ascii=False)
                        _print_step(
                            "⚡", f"Action  →  {block.name}",
                            f"입력값: {inputs_str}",
                            MAGENTA,
                        )

                        # 도구 실행
                        result_str = execute_tool(block.name, block.input)
                        result_obj = json.loads(result_str)

                        # 간략 요약 출력
                        summary = self._summarize_result(block.name, result_obj)
                        _print_step("📋", "Result", summary, DIM)

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_str,
                        })

                messages.append({"role": "user", "content": tool_results})
            else:
                # 예상치 못한 stop_reason
                break

        _print_divider("═")
        return final_answer

    # ── 헬퍼 ──────────────────────────────────────────────────

    @staticmethod
    def _build_query(location: str, user_request: str) -> str:
        parts = [f"위치: {location}"]
        if user_request:
            parts.append(f"요청사항: {user_request}")
        parts.append("오늘 날씨에 맞는 OOTD와 우산 필요 여부를 추천해 주세요.")
        return "\n".join(parts)

    @staticmethod
    def _summarize_result(tool_name: str, result: dict) -> str:
        """도구 결과를 한 줄 요약으로 변환합니다."""
        if "error" in result:
            return f"⚠️  오류: {result['error']}"
        if tool_name == "get_weather":
            return (
                f"기온 {result.get('temperature')}°C "
                f"/ {result.get('category')} "
                f"/ 습도 {result.get('humidity')}%"
            )
        if tool_name == "check_rain_and_umbrella":
            return (
                f"{result.get('rain_status')} "
                f"→ {result.get('umbrella_advice')}"
            )
        if tool_name in ("get_wardrobe_items",):
            return f"{result.get('count')}개 아이템 조회됨"
        if tool_name == "get_wardrobe_overview":
            cats = result.get("by_category", {})
            return "카테고리별: " + ", ".join(f"{k} {v}개" for k, v in cats.items())
        if tool_name == "get_color_pairings":
            combos = result.get("combinations", [])[:4]
            return f"어울리는 색상: {', '.join(combos)}"
        return json.dumps(result, ensure_ascii=False)[:120]


# ══════════════════════════════════════════════════════════════
# ② Plan-and-Execute Agent
#    Phase 1: 계획 수립 (JSON 플랜 생성)
#    Phase 2: 계획 실행 (각 스텝을 순서대로 실행)
#    Phase 3: 종합 (수집된 결과로 최종 추천 생성)
# ══════════════════════════════════════════════════════════════

_PLAN_SYSTEM = """\
당신은 OOTD 추천을 위한 실행 계획을 수립하는 AI입니다.
주어진 요청을 분석하여 단계별 실행 계획을 **JSON 형식만** 출력하세요 (다른 텍스트 없이).

출력 JSON 스키마:
{
  "goal": "전체 목표 한 문장",
  "context_analysis": "요청 분석 내용",
  "steps": [
    {
      "step": 1,
      "name": "단계 이름",
      "tool": "도구 이름",
      "inputs": { "파라미터": "값" },
      "purpose": "이 단계가 필요한 이유"
    }
  ],
  "synthesis_guide": "수집된 정보를 최종 추천에 통합하는 방법"
}

사용 가능한 도구:
- get_weather              : 날씨·기온 조회
- check_rain_and_umbrella  : 비 예보 및 우산 필요 여부
- get_wardrobe_overview    : 옷장 전체 구성 파악
- get_wardrobe_items       : 필터링된 아이템 조회 (category/season/weather_condition)
- get_color_pairings       : 색상 조합 정보 (color 파라미터)
- get_season_palette       : 계절별 색상 팔레트 (season 파라미터)

계획 원칙:
1. 날씨 확인 → 우산 확인 → 옷장 파악 → 아이템 필터링 → 색상 조합 순서로 구성
2. 비·눈 예보가 예상되면 check_rain_and_umbrella를 반드시 포함
3. 불필요한 단계는 포함하지 않음 (최소 4단계, 최대 7단계)
"""

_SYNTHESIZE_SYSTEM = """\
당신은 OOTD 전문 스타일리스트 AI입니다.
수집된 날씨·옷장·색상 데이터를 바탕으로 완성된 코디 추천을 작성하세요.

응답 형식 (마크다운):
## 📍 오늘의 날씨 요약
(기온, 날씨 상태, 체감온도 간략 정리)

## ☂️ 우산 알림
(비·눈·고습도 여부에 따라 우산 필요/불필요 명시 — 항상 포함)

## 👗 오늘의 OOTD 추천
(상의 → 하의 → 아우터 → 신발 → 액세서리 순으로 아이템 이름과 선택 이유 작성)

## 🎨 색상 포인트
(선택한 색상 조합과 그 이유)

## 💡 스타일링 팁
(레이어링, TPO, 주의사항 등 실용적 팁 2~3가지)

원칙:
- 옷장에 실제 존재하는 아이템만 사용
- 기온과 날씨에 맞는 실용적 코디 우선
- 색상 조합 이유를 색채학 근거로 설명
"""


class PlanAndExecuteAgent:
    """
    Plan-and-Execute 패턴 OOTD 에이전트

    Phase 1 — Plan   : Claude가 JSON 실행 계획을 수립합니다.
    Phase 2 — Execute: 계획의 각 스텝을 순서대로 실행합니다.
    Phase 3 — Synth  : 수집된 모든 결과를 Claude에게 전달해 최종 추천을 생성합니다.
    """

    def run(self, location: str, user_request: str = "") -> str:
        print(f"\n{BOLD}{CYAN}{'━'*60}{RESET}")
        print(f"{BOLD}{CYAN}  📋 Plan-and-Execute 에이전트 시작{RESET}")
        print(f"{BOLD}{CYAN}{'━'*60}{RESET}")
        print(f"  📍 위치  : {location}")
        if user_request:
            print(f"  📝 요청  : {user_request}")

        # ── Phase 1: 계획 수립 ─────────────────────────────────
        plan = self._plan(location, user_request)
        self._print_plan(plan)

        # ── Phase 2: 단계별 실행 ───────────────────────────────
        collected_results = self._execute_plan(plan, location)

        # ── Phase 3: 종합 ──────────────────────────────────────
        return self._synthesize(plan, collected_results)

    # ── Phase 1 ───────────────────────────────────────────────

    def _plan(self, location: str, user_request: str) -> dict:
        """Claude에게 JSON 실행 계획을 요청합니다."""
        _print_divider()
        print(f"\n{BOLD}{YELLOW}🗺️  [Phase 1] 계획 수립 중...{RESET}")

        prompt = (
            f"위치: {location}\n"
            + (f"요청: {user_request}\n" if user_request else "")
            + "이 요청에 맞는 OOTD 추천 실행 계획을 수립해 주세요."
        )

        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            system=_PLAN_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )

        raw_text = next(
            (b.text for b in response.content if b.type == "text"), "{}"
        )

        # JSON 추출 (```json ... ``` 블록 처리)
        raw_text = raw_text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            # 파싱 실패 시 기본 계획 반환
            return self._default_plan(location)

    @staticmethod
    def _default_plan(location: str) -> dict:
        """JSON 파싱 실패 시 사용하는 기본 계획."""
        return {
            "goal": "날씨에 맞는 OOTD 추천",
            "steps": [
                {"step": 1, "name": "날씨 확인", "tool": "get_weather",
                 "inputs": {"location": location}, "purpose": "기온·날씨 파악"},
                {"step": 2, "name": "우산 확인", "tool": "check_rain_and_umbrella",
                 "inputs": {"location": location}, "purpose": "우산 필요 여부"},
                {"step": 3, "name": "옷장 개요", "tool": "get_wardrobe_overview",
                 "inputs": {}, "purpose": "보유 아이템 파악"},
                {"step": 4, "name": "아이템 조회", "tool": "get_wardrobe_items",
                 "inputs": {}, "purpose": "전체 아이템 목록"},
            ],
        }

    # ── Phase 2 ───────────────────────────────────────────────

    def _execute_plan(self, plan: dict, location: str) -> list[dict]:
        """계획의 각 스텝을 실행하고 결과 목록을 반환합니다."""
        _print_divider()
        print(f"\n{BOLD}{MAGENTA}⚡ [Phase 2] 계획 실행 중...{RESET}")

        steps = plan.get("steps", [])
        results: list[dict] = []

        for step_info in steps:
            step_num  = step_info.get("step", "?")
            step_name = step_info.get("name", "")
            tool_name = step_info.get("tool", "")
            inputs    = step_info.get("inputs", {})
            purpose   = step_info.get("purpose", "")

            # location 파라미터 자동 주입 (값이 비어있을 경우)
            if "location" in inputs and not inputs["location"]:
                inputs["location"] = location

            print(f"\n  {BOLD}Step {step_num}: {step_name}{RESET}")
            print(f"  {DIM}→ {purpose}{RESET}")
            print(f"  🔧 {tool_name}({json.dumps(inputs, ensure_ascii=False)})")

            result_str = execute_tool(tool_name, inputs)
            result_obj = json.loads(result_str)

            # 간략 요약 출력
            summary = ReActAgent._summarize_result(tool_name, result_obj)
            print(f"  ✅ {summary}")

            results.append({
                "step": step_num,
                "name": step_name,
                "tool": tool_name,
                "result": result_obj,
            })

        return results

    # ── Phase 3 ───────────────────────────────────────────────

    def _synthesize(self, plan: dict, results: list[dict]) -> str:
        """수집된 결과를 바탕으로 최종 추천을 생성합니다 (스트리밍)."""
        _print_divider()
        print(f"\n{BOLD}{GREEN}✨ [Phase 3] 최종 추천 생성 중...{RESET}\n")
        _print_divider("─")

        # 수집된 데이터를 하나의 컨텍스트로 묶기
        context_parts = [
            f"목표: {plan.get('goal', '')}",
            f"합성 가이드: {plan.get('synthesis_guide', '')}",
            "",
            "## 수집된 데이터",
        ]
        for r in results:
            context_parts.append(
                f"\n### Step {r['step']}: {r['name']} ({r['tool']})"
            )
            context_parts.append(json.dumps(r["result"], ensure_ascii=False, indent=2))

        context = "\n".join(context_parts)
        prompt = context + "\n\n위 데이터를 바탕으로 오늘의 OOTD를 추천해 주세요."

        # 스트리밍으로 최종 추천 출력
        final_text = ""
        with client.messages.stream(
            model="claude-opus-4-6",
            max_tokens=2048,
            system=_SYNTHESIZE_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            for text_chunk in stream.text_stream:
                print(text_chunk, end="", flush=True)
                final_text += text_chunk

        print()  # 줄바꿈
        _print_divider("═")
        return final_text

    # ── 헬퍼 ──────────────────────────────────────────────────

    @staticmethod
    def _print_plan(plan: dict) -> None:
        """계획을 터미널에 출력합니다."""
        _print_divider()
        print(f"\n{BOLD}{YELLOW}📋 수립된 실행 계획{RESET}")
        print(f"  목표: {plan.get('goal', '')}")
        if "context_analysis" in plan:
            print(f"  분석: {plan['context_analysis']}")
        print()
        for s in plan.get("steps", []):
            num     = s.get("step", "?")
            name    = s.get("name", "")
            tool    = s.get("tool", "")
            purpose = s.get("purpose", "")
            print(f"  {DIM}[{num}]{RESET} {BOLD}{name}{RESET}  ({tool})")
            print(f"       {DIM}{purpose}{RESET}")


# ══════════════════════════════════════════════════════════════
# 공개 API
# ══════════════════════════════════════════════════════════════

def run_agent(
    mode: str,
    location: str,
    user_request: str = "",
) -> str:
    """
    에이전트를 실행합니다.

    Args:
        mode         : "react" 또는 "plan"
        location     : 날씨 조회 위치
        user_request : 추가 요청사항 (선택)

    Returns:
        최종 추천 텍스트
    """
    if mode == "react":
        return ReActAgent().run(location, user_request)
    elif mode == "plan":
        return PlanAndExecuteAgent().run(location, user_request)
    else:
        raise ValueError(f"알 수 없는 모드: {mode!r}. 'react' 또는 'plan'을 사용하세요.")
