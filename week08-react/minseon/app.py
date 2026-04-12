"""
app.py
──────
OOTD 스타일리스트 AI — Streamlit 웹 UI

실행:
  streamlit run app.py
"""

import base64
import json
import os
from pathlib import Path

import streamlit as st

# .env 자동 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── 페이지 설정 ──────────────────────────────────────────────────
st.set_page_config(
    page_title="OOTD 스타일리스트 AI",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS 스타일 ───────────────────────────────────────────────────
st.markdown("""
<style>
/* 전체 배경 */
.stApp {
    background: #f7f7f7;
}

/* 사이드바 */
[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #e0e0e0;
}
[data-testid="stSidebar"] * {
    color: #1a1a1a !important;
}
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] .stTextInput label,
[data-testid="stSidebar"] .stTextArea label,
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div {
    color: #1a1a1a !important;
}

/* 헤더 */
.ootd-header {
    text-align: center;
    padding: 2rem 0 1rem 0;
}
.ootd-header h1 {
    font-size: 2.4rem;
    color: #1a1a1a;
    font-weight: 700;
    letter-spacing: -0.5px;
    margin-bottom: 0.3rem;
}
.ootd-header p {
    color: #666;
    font-size: 0.95rem;
    letter-spacing: 0.3px;
}

/* 배지 */
.weather-badge {
    display: inline-block;
    background: #1a1a1a;
    color: #ffffff;
    border-radius: 3px;
    padding: 0.25rem 0.7rem;
    font-size: 0.8rem;
    margin: 0.2rem;
    letter-spacing: 0.3px;
}

/* 버튼 기본 (secondary) — 흰 배경 + 검정 텍스트 */
.stButton > button {
    background: #ffffff !important;
    color: #1a1a1a !important;
    border: 1px solid #cccccc !important;
    border-radius: 3px !important;
    padding: 0.5rem 1.5rem !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    transition: background 0.2s, color 0.2s !important;
    box-shadow: none !important;
    letter-spacing: 0.3px !important;
}
.stButton > button:hover {
    background: #f0f0f0 !important;
    border-color: #999 !important;
    transform: none !important;
    box-shadow: none !important;
}

/* primary 버튼 — 검정 배경 + 흰 텍스트 */
.stButton > button[data-testid="baseButton-primary"] {
    background: #1a1a1a !important;
    color: #ffffff !important;
    border: 1px solid #1a1a1a !important;
}
.stButton > button[data-testid="baseButton-primary"]:hover {
    background: #444 !important;
    border-color: #444 !important;
}

/* 입력 필드 */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    border-radius: 3px !important;
    border: 1px solid #cccccc !important;
    background: #ffffff !important;
    color: #1a1a1a !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #1a1a1a !important;
    box-shadow: none !important;
}

/* 셀렉트박스 */
.stSelectbox > div > div {
    border-radius: 3px !important;
    border: 1px solid #cccccc !important;
}

/* 라디오 버튼 */
.stRadio > div {
    flex-direction: row !important;
    gap: 1rem !important;
}

/* 구분선 */
hr {
    border-color: #e0e0e0 !important;
}

/* 익스팬더 */
.streamlit-expanderHeader {
    background: #f2f2f2 !important;
    border-radius: 3px !important;
}

/* 메트릭 */
[data-testid="stMetricValue"] {
    color: #1a1a1a !important;
    font-weight: 700 !important;
}

/* 탭 */
.stTabs [data-baseweb="tab-list"] {
    border-bottom: 2px solid #1a1a1a !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 0 !important;
    color: #666 !important;
    font-weight: 500 !important;
    padding: 0.5rem 1.5rem !important;
}
.stTabs [aria-selected="true"] {
    background: #1a1a1a !important;
    color: #ffffff !important;
}

/* info / success / warning 박스 */
.stAlert {
    border-radius: 3px !important;
    border-left: 3px solid #1a1a1a !important;
}
</style>
""", unsafe_allow_html=True)


# ── 에이전트 임포트 ──────────────────────────────────────────────
@st.cache_resource
def load_agent_module():
    """에이전트 모듈을 한 번만 로드합니다."""
    try:
        import importlib
        spec = importlib.util.spec_from_file_location("react_agent", "react_agent.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod, None
    except Exception as e:
        return None, str(e)


# ── 스트리밍 에이전트 래퍼 ─────────────────────────────────────────
def run_agent_streaming(mode: str, location: str, user_request: str):
    """
    에이전트를 실행하고 단계별 이벤트를 yield합니다.
    이벤트 형식: {"type": ..., "content": ...}
    """
    import json
    from openai import OpenAI
    try:
        from function_calling import TOOL_SCHEMAS, execute_tool
    except ImportError as e:
        yield {"type": "error", "content": f"모듈 로드 실패: {e}"}
        return

    client = OpenAI()

    REACT_SYSTEM = """\
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
### 오늘의 날씨 요약
### 우산 알림          ← 비/눈/고습도 시 반드시 포함
### 추천 코디           ← 상의 → 하의 → 아우터 → 신발 → 액세서리
### 색상 포인트
### 스타일링 팁

## 핵심 원칙
- 비·눈이 오거나 습도 ≥ 80 % 이면 반드시 우산 알림 강조
- 옷장에 실제로 있는 아이템만 사용
- 일교차가 크면 레이어링 방법 제안
"""

    PLAN_SYSTEM = """\
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
- get_weather, check_rain_and_umbrella, get_wardrobe_overview
- get_wardrobe_items, get_color_pairings, get_season_palette

계획 원칙:
1. 날씨 확인 → 우산 확인 → 옷장 파악 → 아이템 필터링 → 색상 조합 순서로 구성
2. 비·눈 예보가 예상되면 check_rain_and_umbrella를 반드시 포함
3. 최소 4단계, 최대 7단계
"""

    SYNTHESIZE_SYSTEM = """\
당신은 OOTD 전문 스타일리스트 AI입니다.
수집된 날씨·옷장·색상 데이터를 바탕으로 완성된 코디 추천을 작성하세요.

응답 형식 (마크다운):
## 오늘의 날씨 요약
## 우산 알림
## 오늘의 OOTD 추천
## 색상 포인트
## 스타일링 팁
"""

    def summarize_result(tool_name: str, result: dict) -> str:
        if "error" in result:
            return f"오류: {result['error']}"
        if tool_name == "get_weather":
            return f"기온 {result.get('temperature')}°C / {result.get('category')} / 습도 {result.get('humidity')}%"
        if tool_name == "check_rain_and_umbrella":
            return f"{result.get('rain_status')} → {result.get('umbrella_advice')}"
        if tool_name == "get_wardrobe_items":
            return f"{result.get('count')}개 아이템 조회됨"
        if tool_name == "get_wardrobe_overview":
            cats = result.get("by_category", {})
            return "카테고리별: " + ", ".join(f"{k} {v}개" for k, v in cats.items())
        if tool_name == "get_color_pairings":
            combos = result.get("combinations", [])[:4]
            return f"어울리는 색상: {', '.join(combos)}"
        return json.dumps(result, ensure_ascii=False)[:100]

    # ── ReAct 모드 ──────────────────────────────────────────────
    if mode == "react":
        query_parts = [f"위치: {location}"]
        if user_request:
            query_parts.append(f"요청사항: {user_request}")
        query_parts.append("오늘 날씨에 맞는 OOTD와 우산 필요 여부를 추천해 주세요.")
        query = "\n".join(query_parts)

        messages = [
            {"role": "system", "content": REACT_SYSTEM},
            {"role": "user", "content": query},
        ]
        step = 0
        MAX_STEPS = 10

        while step < MAX_STEPS:
            step += 1
            yield {"type": "step_start", "content": f"Step {step}"}

            response = client.chat.completions.create(
                model="gpt-4o",
                tools=TOOL_SCHEMAS,
                messages=messages,
            )

            msg = response.choices[0].message
            finish_reason = response.choices[0].finish_reason

            if msg.content and msg.content.strip():
                text = msg.content.strip()
                if "[Final Answer]" in text:
                    clean = text.replace("**[Final Answer]**", "").strip()
                    yield {"type": "final_answer", "content": clean}
                elif "[Thought]" in text:
                    clean = text.replace("**[Thought]**", "").strip()
                    yield {"type": "thought", "content": clean}
                elif "[Observation]" in text:
                    clean = text.replace("**[Observation]**", "").strip()
                    yield {"type": "observation", "content": clean}
                else:
                    yield {"type": "text", "content": text}

            if finish_reason == "stop":
                break

            if finish_reason == "tool_calls":
                tool_calls = msg.tool_calls or []
                messages.append({
                    "role": "assistant",
                    "content": msg.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in tool_calls
                    ],
                })

                for tc in tool_calls:
                    tool_name = tc.function.name
                    inputs = json.loads(tc.function.arguments)
                    yield {
                        "type": "action",
                        "content": f"**{tool_name}**\n입력: {tc.function.arguments}",
                    }
                    result_str = execute_tool(tool_name, inputs)
                    result_obj = json.loads(result_str)
                    summary = summarize_result(tool_name, result_obj)
                    yield {"type": "tool_result", "content": summary}

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result_str,
                    })
            else:
                break

    # ── Plan-and-Execute 모드 ────────────────────────────────────
    else:
        # Phase 1: Plan
        yield {"type": "phase", "content": "Phase 1 — 실행 계획 수립 중..."}

        prompt = (
            f"위치: {location}\n"
            + (f"요청: {user_request}\n" if user_request else "")
            + "이 요청에 맞는 OOTD 추천 실행 계획을 수립해 주세요."
        )

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": PLAN_SYSTEM},
                {"role": "user", "content": prompt},
            ],
        )

        raw_text = response.choices[0].message.content or "{}"
        raw_text = raw_text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        try:
            plan = json.loads(raw_text)
        except json.JSONDecodeError:
            plan = {
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

        yield {"type": "plan", "content": plan}

        # Phase 2: Execute
        yield {"type": "phase", "content": "Phase 2 — 계획 실행 중..."}

        collected_results = []
        for step_info in plan.get("steps", []):
            step_num = step_info.get("step", "?")
            step_name = step_info.get("name", "")
            tool_name = step_info.get("tool", "")
            inputs = step_info.get("inputs", {})
            purpose = step_info.get("purpose", "")

            if "location" in inputs and not inputs["location"]:
                inputs["location"] = location

            yield {
                "type": "action",
                "content": f"**Step {step_num}: {step_name}**\n{purpose}\n→ {tool_name}({json.dumps(inputs, ensure_ascii=False)})",
            }

            result_str = execute_tool(tool_name, inputs)
            result_obj = json.loads(result_str)
            summary = summarize_result(tool_name, result_obj)
            yield {"type": "tool_result", "content": summary}

            collected_results.append({
                "step": step_num,
                "name": step_name,
                "tool": tool_name,
                "result": result_obj,
            })

        # Phase 3: Synthesize (streaming)
        yield {"type": "phase", "content": "Phase 3 — 최종 추천 생성 중..."}

        context_parts = [
            f"목표: {plan.get('goal', '')}",
            f"합성 가이드: {plan.get('synthesis_guide', '')}",
            "",
            "## 수집된 데이터",
        ]
        for r in collected_results:
            context_parts.append(f"\n### Step {r['step']}: {r['name']} ({r['tool']})")
            context_parts.append(json.dumps(r["result"], ensure_ascii=False, indent=2))

        context = "\n".join(context_parts)
        synth_prompt = context + "\n\n위 데이터를 바탕으로 오늘의 OOTD를 추천해 주세요."

        final_text = ""
        stream = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYNTHESIZE_SYSTEM},
                {"role": "user", "content": synth_prompt},
            ],
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                final_text += delta
                yield {"type": "stream_chunk", "content": delta}

        yield {"type": "final_answer", "content": final_text}


# ── 비전 에이전트 (멀티모달) ──────────────────────────────────────
def run_vision_agent_streaming(
    image_bytes: bytes,
    media_type: str,
    location: str,
    occasion: str = "",
    extra_request: str = "",
):
    """
    업로드된 의류 사진을 분석하고 옷장 기반 코디를 추천합니다.
    이벤트 형식: {"type": ..., "content": ...}
    """
    from openai import OpenAI
    from function_calling import execute_tool

    client = OpenAI()

    # 날씨 조회
    yield {"type": "status", "content": "날씨 정보 조회 중..."}
    weather_raw = execute_tool("get_weather", {"location": location})
    weather = json.loads(weather_raw)
    rain_raw = execute_tool("check_rain_and_umbrella", {"location": location})
    rain = json.loads(rain_raw)

    # 옷장 전체 데이터
    yield {"type": "status", "content": "옷장 데이터 로드 중..."}
    wardrobe_raw = execute_tool("get_wardrobe_items", {})
    wardrobe = json.loads(wardrobe_raw)

    yield {"type": "status", "content": "사진 분석 및 코디 추천 생성 중..."}

    # 날씨 요약
    weather_summary = (
        f"기온: {weather.get('temperature')}°C, "
        f"날씨: {weather.get('category')}, "
        f"습도: {weather.get('humidity')}%, "
        f"우산 필요: {'예' if rain.get('umbrella_needed') else '아니오'}"
    )

    # 상황 + 스타일
    occasion_text = f"\n상황: {occasion}" if occasion and occasion != "없음" else ""

    # 추가 요청
    extra_text = f"\n추가 요청: {extra_request}" if extra_request.strip() else ""

    # 옷장 아이템 목록 텍스트
    items = wardrobe.get("items", [])
    wardrobe_text = "\n".join(
        f"- [{item['category']}] {item['name']} | 색상: {item['color']} | "
        f"시즌: {', '.join(item.get('season', []))} | 스타일: {', '.join(item.get('style', []))}"
        for item in items
    )

    system_prompt = """\
당신은 OOTD 전문 스타일리스트 AI입니다.
사용자가 업로드한 사진 속 의류 아이템을 분석하고,
제공된 옷장 데이터와 날씨 정보를 바탕으로 완성된 코디를 추천하세요.

응답 형식 (마크다운):
## 사진 속 아이템 분석
(색상, 카테고리, 스타일, 소재 등 파악된 정보)

## 오늘의 날씨
(기온, 날씨 상태, 우산 필요 여부)

## 추천 코디
(사진 속 아이템을 포함한 전체 코디 — 상의 → 하의 → 아우터 → 신발 → 액세서리 순)
각 아이템은 옷장에 있는 것을 우선 사용하고, 아이템 이름과 선택 이유를 함께 작성.

## 색상 포인트
(사진 속 아이템 색상과 어울리는 색상 조합 이유)

## 스타일링 팁
(TPO, 레이어링, 주의사항 등 2~3가지 실용적 팁)

원칙:
- 사진 속 아이템의 색상·스타일을 정확히 파악하여 매칭
- 옷장에 없는 아이템은 "(옷장 없음 — 추가 구매 추천)"으로 표시
- 날씨가 비/눈이면 우산 알림 강조
"""

    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    user_message = {
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{media_type};base64,{image_b64}",
                },
            },
            {
                "type": "text",
                "text": (
                    f"위치: {location}\n"
                    f"날씨: {weather_summary}"
                    f"{occasion_text}"
                    f"{extra_text}\n\n"
                    f"## 내 옷장 아이템 목록\n{wardrobe_text}\n\n"
                    "위 사진의 의류 아이템을 분석하고, 내 옷장 아이템들과 날씨를 고려하여 "
                    "오늘의 완성된 코디를 추천해주세요."
                ),
            },
        ],
    }

    final_text = ""
    stream = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            user_message,
        ],
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            final_text += delta
            yield {"type": "stream_chunk", "content": delta}

    yield {"type": "final_answer", "content": final_text}


def detect_media_type(file_bytes: bytes, filename: str = "") -> str:
    """파일 바이트에서 미디어 타입을 감지합니다."""
    ext = Path(filename).suffix.lower()
    ext_map = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".gif": "image/gif",
        ".webp": "image/webp",
    }
    if ext in ext_map:
        return ext_map[ext]
    # 매직 바이트로 판별
    if file_bytes[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if file_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if file_bytes[:4] == b"RIFF" and file_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"  # 기본값


# ── 옷장 데이터 로드 ─────────────────────────────────────────────
@st.cache_data
def load_wardrobe_items():
    path = Path("wardrobe.json")
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    result = {}
    for item in data.get("items", []):
        cat = item.get("category", "기타")
        result.setdefault(cat, []).append(item)
    return result

WARDROBE = load_wardrobe_items()

def item_label(item: dict) -> str:
    """아이템 선택지 표시용 라벨"""
    return f"{item['name']} ({item['color']})"

# ── 상황 (TPO) ──────────────────────────────────────────────────
SITUATIONS = {
    "없음":   ("", "자유롭게"),
    "데이트룩": ("", "로맨틱·세련"),
    "하객룩":  ("", "우아·격식"),
    "면접룩":  ("", "단정·프로"),
    "비즈니스": ("", "비즈니스캐주얼"),
    "등산룩":  ("", "기능성 아웃도어"),
    "운동룩":  ("", "스포티·활동적"),
    "파티룩":  ("", "화려·트렌디"),
    "여행룩":  ("", "실용·편한"),
}

# ── 패션 스타일 (아이콘, 한줄요약, AI에게 전달할 상세 설명) ──────
STYLES: dict[str, tuple[str, str, str]] = {
    "없음": (
        "", "자유롭게", "",
    ),
    "모리룩": (
        "", "숲속 소녀",
        "목표: 숲속 자연의 포근함과 여유로운 핏을 강조하는 레이어드 룩. "
        "컬러: 베이지·브라운·카키·아이보리 어스톤, 톤다운된 그린. "
        "상의: 린넨 셔츠·루즈핏 니트 조끼·면/마 소재 블라우스. "
        "하의: 펑퍼짐한 롱스커트·통 넓은 면바지. 원피스: A라인 롱 원피스. "
        "액세서리: 에코백·밀짚모자·둥근 코 단화. "
        "추천 로직: 롱스커트+니트 레이어드를 우선 제안. 천연 소재 강조.",
    ),
    "서브컬쳐": (
        "", "스트릿·펑크·애니 감성",
        "목표: 스트릿·펑크·일본 애니메이션 감성이 섞인 힙하고 반항적인 무드. "
        "컬러: 블랙·화이트·다크그레이 베이스, 강렬한 레드/블루 포인트. "
        "상의: 오버사이즈 그래픽 후드티·프린팅 반팔티·디스트로이드 니트. "
        "하의: 와이드 카고팬츠·파라슈트 팬츠·체인 달린 바지. "
        "신발: 통굽 워커·청키 스니커즈. 액세서리: 실버 체인 목걸이·볼드한 피어싱·비니. "
        "추천 로직: 핏을 무조건 오버사이즈로, 실버 액세서리 추가를 반드시 제안.",
    ),
    "고스룩": (
        "", "고딕·다크·신비",
        "목표: 다크하고 신비로운 기괴한 분위기를 우아하거나 강렬하게 표현. "
        "컬러: 올블랙 기본, 딥버건디 포인트. 블랙이 아닌 아이템은 배제 또는 무채색 매칭 유도. "
        "소재: 가죽·벨벳·레이스·망사(메쉬). "
        "아이템: 가죽자켓·코르셋탑·레이스스커트·슬릿 롱스커트. "
        "신발/액세서리: 롱부츠·컴뱃부츠·십자가 초커목걸이·스터드 장식. "
        "추천 로직: 색상이 블랙이 아니면 코디에서 배제하거나 무채색 매칭으로 유도.",
    ),
    "아메카지": (
        "", "아메리칸 빈티지 캐주얼",
        "목표: 빈티지 아메리칸 워크웨어를 캐주얼하고 실용적으로 조합. "
        "컬러: 인디고(데님)·올리브그린·카멜·베이지·네이비. "
        "상의: 샴브레이(청)셔츠·체크 플란넬셔츠·포켓 디테일 워크자켓. "
        "하의: 생지 데님(셀비지진)·카키 치노팬츠·퍼티그 팬츠. "
        "신발/액세서리: 캔버스화(컨버스)·가죽부츠(레드윙 스타일)·뉴스보이캡·캔버스 토트백. "
        "추천 로직: 데님·치노 베이스 + 아우터(자켓류) 레이어드, 단정한 코디 제안.",
    ),
    "포엣코어": (
        "", "중세 낭만주의·서정적",
        "목표: 중세 낭만주의 문학가처럼 서정적이고 감성적이며 우아한 핏 연출. "
        "컬러: 화이트·크림·앤틱골드·더스티핑크·페일블루. "
        "상의: 프릴/러플 디테일 실크 블라우스·퍼프소매 셔츠·코르셋. "
        "하의: 핀턱 슬랙스·하늘하늘한 미디스커트. "
        "액세서리: 앤틱 펜던트 목걸이·리본·베레모·가죽 사첼백. "
        "추천 로직: 장식 있는 블라우스 위주 매칭, 딱 떨어지는 핏보다 흐르는 실루엣 강조.",
    ),
    "미니멀룩": (
        "", "장식 없는 핏·소재 중심",
        "목표: 장식·디테일을 최소화하고 핏과 소재 고급스러움으로 승부. "
        "컬러: 무채색 중심 — 블랙·화이트·네이비·그레이·차콜. "
        "상의: 로고 없는 무지 티셔츠·핏 좋은 셔츠·캐시미어 니트. "
        "하의: 스트레이트핏 슬랙스·생지 데님·깔끔한 면바지. "
        "신발/액세서리: 더비슈즈·화이트 스니커즈·로고 없는 심플 토트백/크로스백. "
        "추천 로직: 화려한 패턴·튀는 로고 아이템 완전 배제. 동일 색상 계열 내 톤온톤 조합 제안.",
    ),
    "보헤미안": (
        "", "자유·에스닉·패턴",
        "목표: 얽매이지 않는 자유로움과 에스닉(민속적) 무드를 패턴·디테일로 표현. "
        "컬러: 딥레드·머스터드옐로우·터키석블루·브릭(벽돌색)·브라운. "
        "상의: 페이즐리/에스닉 패턴 블라우스·크로셰 니트·프린지 장식 조끼. "
        "하의/원피스: 화려한 패턴 맥시원피스·나팔바지(플레어팬츠)·롱 티어드 스커트. "
        "신발/액세서리: 스웨이드 앵클부츠·레이어드 비즈/은 목걸이·깃털 장식·넓은 챙 모자(페도라). "
        "추천 로직: 에스닉 패턴·프린지 디테일 아이템을 메인으로, 다중 액세서리 자유 레이어드 제안.",
    ),
    "고프코어": (
        "", "아웃도어·기능성·실용",
        "목표: 아웃도어 기능성 아이템을 데일리에 세련되게 믹스. "
        "컬러: 올리브·카키·네이비·블랙·오렌지 포인트. "
        "핵심 아이템: 나일론 바람막이·카고팬츠·등산화(트레킹화)·백팩·드로스트링 디테일. "
        "추천 로직: 기능성 소재 우선, 아웃도어 브랜드 감성의 실용적 레이어링 제안.",
    ),
    "올드머니룩": (
        "", "콰이어트 럭셔리·클래식",
        "목표: 로고 없는 절제된 고품질로 상류층 클래식 감성 연출. "
        "컬러: 카멜·크림·네이비·버건디·그레이 뉴트럴 팔레트. "
        "핵심 아이템: 캐시미어 니트·실크 스카프·트위드 자켓·테일러드 코트·로고 없는 고품질 가죽 가방. "
        "추천 로직: 로고·화려한 디테일 배제. 소재 퀄리티와 테일러링으로 럭셔리 표현.",
    ),
    "코켓코어": (
        "", "페미닌·로맨틱·귀여움",
        "목표: 달콤하고 여성스러운 페미닌·로맨틱 무드 연출. "
        "컬러: 파스텔핑크·화이트·크림·베이비블루·라벤더. "
        "핵심 아이템: 리본 장식·레이스 원피스·파스텔톤 가디건·니삭스(반스타킹)·메리제인 슈즈. "
        "추천 로직: 리본·레이스·파스텔 조합. 귀엽고 로맨틱한 페미닌 실루엣 우선.",
    ),
    "테크웨어": (
        "", "사이버펑크·미래지향",
        "목표: 기능성 극대화 + 사이버펑크 미래지향적 무드. "
        "컬러: 올블랙 베이스, 다크그레이·차콜 포인트. "
        "핵심 아이템: 방수 자켓(고어텍스)·다포켓 조거팬츠·테크니컬 스트랩·모듈 벨트·러기드 스니커즈. "
        "추천 로직: 올블랙 컬러 엄수. 기능성 디테일(스트랩·포켓·지퍼) 강조. 레이어링으로 볼륨감 연출.",
    ),
    "Y2K": (
        "", "세기말·레트로·키치",
        "목표: 2000년대 초반 세기말 팝 컬처의 레트로·키치한 무드. "
        "컬러: 실버 메탈릭·홀로그램·비비드 컬러(핫핑크·민트·퍼플). "
        "핵심 아이템: 로우라이즈 데님·크롭 티셔츠·벨벳 트레이닝 셋업·청청패션·실버 메탈릭 아이템. "
        "추천 로직: 배꼽 노출 크롭 실루엣 권장. 버터플라이·별·하트 디테일 우선. 틴트 선글라스·미니백 추가 제안.",
    ),
}

# ── 세션 상태 초기화 ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "running" not in st.session_state:
    st.session_state.running = False
if "situation" not in st.session_state:
    st.session_state.situation = "없음"
if "style" not in st.session_state:
    st.session_state.style = "없음"

# 하위호환 (이전 세션)
OCCASIONS = SITUATIONS  # build_request 등에서 참조


# ── 사이드바 ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 설정")
    st.markdown("---")

    location = st.text_input("위치", value="서울", placeholder="예: 서울, 부산, 제주")

    mode = st.radio(
        "에이전트 모드",
        options=["ReAct", "Plan & Execute"],
        index=0,
        help="ReAct: 실시간 추론 / Plan: 계획 후 실행",
    )
    mode_key = "react" if mode == "ReAct" else "plan"

    st.markdown("---")

    # ── 상황 선택 (TPO) ────────────────────────────────────────
    st.markdown("#### 상황 (TPO)")
    sit_cols = st.columns(3)
    for i, (name, (icon, desc)) in enumerate(SITUATIONS.items()):
        with sit_cols[i % 3]:
            is_sel = st.session_state.situation == name
            label = f"{'자유' if name == '없음' else name}"
            if st.button(label, key=f"sit_{name}", use_container_width=True,
                         type="primary" if is_sel else "secondary"):
                st.session_state.situation = name
                st.rerun()

    selected_situation = st.session_state.situation
    if selected_situation != "없음":
        ic, dc = SITUATIONS[selected_situation]
        st.success(f"**{selected_situation}** — {dc}")

    st.markdown("---")

    # ── 스타일 선택 ────────────────────────────────────────────
    st.markdown("#### 패션 스타일")

    style_names = list(STYLES.keys())
    selected_style = st.selectbox(
        "",
        style_names,
        index=style_names.index(st.session_state.style),
        format_func=lambda n: f"{n}  —  {STYLES[n][1]}" if n != "없음" else "스타일 선택 안 함",
        label_visibility="collapsed",
        key="style_select",
    )
    if selected_style != st.session_state.style:
        st.session_state.style = selected_style
        st.rerun()

    if selected_style != "없음":
        sicon, ssummary, sdesc = STYLES[selected_style]
        with st.expander(f"{selected_style} 스타일 가이드", expanded=False):
            st.caption(sdesc)

    # 하위호환용 (build_request에서 occasion 참조)
    selected_occasion = selected_situation

    st.markdown("---")

    # ── 오늘 입을 아이템 고정 ──────────────────────────────────
    st.markdown("#### 고정 아이템 선택")
    st.caption("이미 입을 아이템이 있다면 직접 입력하세요")

    selected_top_text = st.text_input(
        "상의", placeholder="예: 흰색 티셔츠, 네이비 셔츠", key="top_item"
    )
    selected_bottom_text = st.text_input(
        "하의", placeholder="예: 블루 청바지, 베이지 슬랙스", key="bottom_item"
    )
    selected_outer_text = st.text_input(
        "아우터", placeholder="예: 베이지 트렌치코트, 데님 재킷", key="outer_item"
    )

    st.markdown("---")

    # ── 색상으로만 지정 ────────────────────────────────────────
    st.markdown("#### 색상으로 지정")
    st.caption("아이템 대신 색상만 알고 있을 때")

    COLOR_KO_EN = {
        "선택 안 함": None,
        "화이트": "white", "블랙": "black", "네이비": "navy",
        "그레이": "gray", "베이지": "beige", "블루": "blue",
        "하늘색": "light_blue", "브라운": "brown", "카멜": "camel",
        "크림": "cream", "버건디": "burgundy", "카키": "khaki",
        "세이지": "sage", "탄": "tan", "민트": "mint",
        "핑크": "pink", "코랄": "coral", "머스타드": "mustard",
        "라벤더": "lavender", "레드": "red",
    }
    color_options = list(COLOR_KO_EN.keys())

    top_color_label = st.selectbox("상의 색상", color_options, index=0, key="top_color")
    bottom_color_label = st.selectbox("하의 색상", color_options, index=0, key="bottom_color")

    top_color_en = COLOR_KO_EN.get(top_color_label)
    bottom_color_en = COLOR_KO_EN.get(bottom_color_label)

    st.markdown("---")

    # ── 추가 요청사항 ──────────────────────────────────────────
    st.markdown("#### 추가 요청사항")
    extra_request = st.text_area(
        "",
        placeholder="예: 키가 작아서 롱스커트는 피하고 싶어요\n밝은 색상 위주로 추천해줘",
        height=80,
        label_visibility="collapsed",
    )

    st.markdown("---")

    # 대화 초기화
    if st.button("대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.session_state.situation = "없음"
        st.session_state.style = "없음"
        st.rerun()


# ── 요청 문자열 조합 ─────────────────────────────────────────────
def build_request() -> str:
    parts = []

    # 상황
    if selected_situation != "없음":
        parts.append(f"오늘 상황: {selected_situation}")

    # 패션 스타일
    if selected_style != "없음":
        _, ssummary, sdesc = STYLES[selected_style]
        parts.append(f"원하는 패션 스타일: {selected_style} ({ssummary})")
        if sdesc:
            parts.append(f"스타일 가이드: {sdesc}")

    # 고정 아이템 (텍스트 입력)
    fixed_items = []
    if selected_top_text.strip():
        fixed_items.append(f"상의는 '{selected_top_text.strip()}' 으로 이미 결정")
    if selected_bottom_text.strip():
        fixed_items.append(f"하의는 '{selected_bottom_text.strip()}' 으로 이미 결정")
    if selected_outer_text.strip():
        fixed_items.append(f"아우터는 '{selected_outer_text.strip()}' 으로 이미 결정")
    if fixed_items:
        parts.append("고정 아이템: " + ", ".join(fixed_items))
        parts.append("나머지 아이템(신발·액세서리 등)을 옷장에서 어울리게 추천해줘")

    # 색상 지정
    color_hints = []
    if top_color_en and not selected_top_text.strip():
        color_hints.append(f"상의 색상: {top_color_label}({top_color_en})")
    if bottom_color_en and not selected_bottom_text.strip():
        color_hints.append(f"하의 색상: {bottom_color_label}({bottom_color_en})")
    if color_hints:
        parts.append("색상 조건: " + ", ".join(color_hints))
        parts.append("이 색상에 어울리는 전체 코디를 옷장에서 추천해줘")

    # 추가 요청
    if extra_request.strip():
        parts.append(extra_request.strip())

    return "\n".join(parts)


# ── 메인 영역 ────────────────────────────────────────────────────
st.markdown("""
<div class="ootd-header">
    <h1>OOTD 스타일리스트 AI</h1>
    <p>날씨 · 옷장 · 색상을 분석한 맞춤 코디 추천</p>
</div>
""", unsafe_allow_html=True)

# 현재 선택 요약 배지
badge_parts = []
if selected_situation != "없음":
    badge_parts.append(selected_situation)
if selected_style != "없음":
    _, ssummary, _ = STYLES[selected_style]
    badge_parts.append(selected_style)
if selected_top_text.strip():
    badge_parts.append(f"상의: {selected_top_text.strip()}")
elif top_color_en:
    badge_parts.append(f"상의 색상: {top_color_label}")
if selected_bottom_text.strip():
    badge_parts.append(f"하의: {selected_bottom_text.strip()}")
elif bottom_color_en:
    badge_parts.append(f"하의 색상: {bottom_color_label}")
if selected_outer_text.strip():
    badge_parts.append(f"아우터: {selected_outer_text.strip()}")

if badge_parts:
    badges_html = " &nbsp;|&nbsp; ".join(
        f'<span class="weather-badge">{b}</span>' for b in badge_parts
    )
    st.markdown(f'<div style="text-align:center;margin-bottom:0.5rem">{badges_html}</div>',
                unsafe_allow_html=True)

st.markdown("---")

tab_chat, tab_photo = st.tabs(["코디 추천", "사진으로 추천"])


# ════════════════════════════════════════════════════════════════
# TAB 1 — 채팅 코디 추천
# ════════════════════════════════════════════════════════════════
with tab_chat:

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant"):
                if "steps" in msg:
                    for s in msg["steps"]:
                        stype, scontent = s["type"], s["content"]
                        if stype == "thought":
                            with st.expander("Thought", expanded=False):
                                st.markdown(scontent)
                        elif stype == "action":
                            with st.expander("Action", expanded=False):
                                st.markdown(scontent)
                        elif stype == "tool_result":
                            with st.expander("Result", expanded=False):
                                st.success(scontent)
                        elif stype == "observation":
                            with st.expander("Observation", expanded=False):
                                st.markdown(scontent)
                        elif stype == "phase":
                            st.markdown(f"**{scontent}**")
                        elif stype == "plan":
                            st.markdown(f"**목표:** {scontent.get('goal', '')}")
                            for step in scontent.get("steps", []):
                                st.markdown(
                                    f"- **Step {step['step']}** {step['name']}"
                                    f" → `{step['tool']}`"
                                )
                if "final_answer" in msg:
                    st.markdown(msg["final_answer"])

    _, center_col, _ = st.columns([2, 3, 2])
    with center_col:
        btn_recommend = st.button(
            "OOTD 추천 받기",
            use_container_width=True,
            type="primary",
            disabled=st.session_state.running,
        )

    prompt = st.chat_input(
        "직접 입력하거나 위 버튼을 눌러 추천받으세요",
        disabled=st.session_state.running,
    )

    if btn_recommend:
        prompt = "추천해줘"

    if prompt and not st.session_state.running:
        st.session_state.running = True

        combined_request = build_request()
        if prompt.strip() and prompt.strip() != "추천해줘":
            combined_request = (combined_request + "\n" + prompt.strip()).strip()

        display_parts = [f"{location} | {mode}"]
        if selected_situation != "없음":
            display_parts.append(f"상황: **{selected_situation}**")
        if selected_style != "없음":
            display_parts.append(f"스타일: **{selected_style}**")
        if selected_top_text.strip():
            display_parts.append(f"상의: {selected_top_text.strip()}")
        elif top_color_en:
            display_parts.append(f"상의 색상: {top_color_label}")
        if selected_bottom_text.strip():
            display_parts.append(f"하의: {selected_bottom_text.strip()}")
        elif bottom_color_en:
            display_parts.append(f"하의 색상: {bottom_color_label}")
        if selected_outer_text.strip():
            display_parts.append(f"아우터: {selected_outer_text.strip()}")
        if extra_request.strip():
            display_parts.append(extra_request.strip())
        if prompt.strip() and prompt.strip() != "추천해줘":
            display_parts.append(prompt.strip())
        user_msg = "\n\n".join(display_parts)

        st.session_state.messages.append({"role": "user", "content": user_msg})

        with st.chat_message("user"):
            st.markdown(user_msg)

        with st.chat_message("assistant"):
            steps_log = []
            final_answer = ""
            stream_placeholder = None
            status_container = st.empty()
            steps_container = st.container()

            with st.spinner("스타일리스트 AI가 분석 중입니다..."):
                try:
                    for event in run_agent_streaming(mode_key, location or "서울", combined_request):
                        etype, econtent = event["type"], event["content"]
                        if etype == "error":
                            st.error(f"오류: {econtent}"); break
                        elif etype == "phase":
                            status_container.info(econtent)
                            steps_log.append({"type": "phase", "content": econtent})
                        elif etype == "plan":
                            steps_log.append({"type": "plan", "content": econtent})
                            with steps_container:
                                st.markdown(f"**목표:** {econtent.get('goal', '')}")
                                for step in econtent.get("steps", []):
                                    st.markdown(
                                        f"- **Step {step['step']}** {step['name']}"
                                        f" → `{step['tool']}`"
                                    )
                        elif etype == "thought":
                            steps_log.append({"type": "thought", "content": econtent})
                            with steps_container:
                                with st.expander("Thought", expanded=True):
                                    st.markdown(econtent)
                        elif etype == "action":
                            steps_log.append({"type": "action", "content": econtent})
                            with steps_container:
                                with st.expander("Action", expanded=True):
                                    st.markdown(econtent)
                        elif etype == "tool_result":
                            steps_log.append({"type": "tool_result", "content": econtent})
                            with steps_container:
                                with st.expander("Result", expanded=True):
                                    st.success(econtent)
                        elif etype == "observation":
                            steps_log.append({"type": "observation", "content": econtent})
                            with steps_container:
                                with st.expander("Observation", expanded=True):
                                    st.markdown(econtent)
                        elif etype == "stream_chunk":
                            final_answer += econtent
                            if stream_placeholder is None:
                                status_container.empty()
                                stream_placeholder = st.empty()
                            stream_placeholder.markdown(final_answer + "▌")
                        elif etype == "final_answer":
                            final_answer = econtent
                except Exception as e:
                    import traceback
                    st.error(f"오류: {e}")
                    st.code(traceback.format_exc())

            status_container.empty()
            if stream_placeholder and final_answer:
                stream_placeholder.markdown(final_answer)
            elif final_answer:
                st.markdown(final_answer)

        st.session_state.messages.append({
            "role": "assistant",
            "steps": steps_log,
            "final_answer": final_answer,
        })
        st.session_state.running = False

    if not st.session_state.messages:
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown("**상황 선택**\n- 데이트·면접·하객 등\n- 9가지 상황 지원")
        with c2:
            st.markdown("**아이템 직접 입력**\n- 상의·하의·아우터 입력\n- 나머지 자동 매칭")
        with c3:
            st.markdown("**색상으로 지정**\n- 20가지 한국어 색상\n- 색상만 알아도 OK")
        with c4:
            st.markdown("**날씨 자동 반영**\n- 실시간 기온·날씨\n- 우산 여부 포함")


# ════════════════════════════════════════════════════════════════
# TAB 2 — 사진으로 추천 (멀티모달)
# ════════════════════════════════════════════════════════════════
with tab_photo:

    st.markdown("### 사진으로 코디 추천받기")
    st.caption("옷 사진을 찍거나 업로드하면 AI가 분석하여 어울리는 코디를 추천합니다.")
    st.markdown("")

    img_col, result_col = st.columns([1, 1], gap="large")

    with img_col:
        photo_source = st.radio(
            "입력 방식",
            ["카메라로 찍기", "파일 업로드"],
            horizontal=True,
            label_visibility="collapsed",
        )

        image_bytes = None
        media_type = "image/jpeg"

        if photo_source == "카메라로 찍기":
            camera_img = st.camera_input(
                "카메라로 의류 아이템을 촬영하세요",
                label_visibility="collapsed",
            )
            if camera_img:
                image_bytes = camera_img.getvalue()
                media_type = "image/jpeg"
        else:
            uploaded = st.file_uploader(
                "이미지 파일 선택 (jpg, png, webp)",
                type=["jpg", "jpeg", "png", "webp"],
                label_visibility="collapsed",
            )
            if uploaded:
                image_bytes = uploaded.getvalue()
                media_type = detect_media_type(image_bytes, uploaded.name)
                st.image(image_bytes, use_container_width=True)

        if image_bytes:
            st.markdown("---")
            photo_occasion = st.selectbox(
                "상황 선택",
                list(SITUATIONS.keys()),
                index=list(SITUATIONS.keys()).index(st.session_state.situation),
                key="photo_occasion",
            )
            photo_style = st.selectbox(
                "스타일 선택",
                list(STYLES.keys()),
                index=list(STYLES.keys()).index(st.session_state.style),
                format_func=lambda n: n if n != "없음" else "스타일 선택 안 함",
                key="photo_style",
            )
            photo_extra = st.text_input(
                "추가 요청",
                placeholder="예: 포멀하게, 캐주얼하게, 밝은 색 위주로",
                key="photo_extra",
            )
            if st.button("이 옷에 맞는 코디 추천받기", use_container_width=True, type="primary"):
                style_desc = STYLES[photo_style][2] if photo_style != "없음" else ""
                style_extra = f"스타일: {photo_style} — {style_desc}" if photo_style != "없음" else ""
                combined_extra = "\n".join(filter(None, [style_extra, photo_extra]))
                st.session_state["vision_trigger"] = {
                    "bytes": image_bytes,
                    "media_type": media_type,
                    "occasion": photo_occasion,
                    "extra": combined_extra,
                }
                st.rerun()

    with result_col:
        st.markdown("#### 추천 결과")

        if "vision_result" in st.session_state:
            st.markdown(st.session_state["vision_result"])
        elif not image_bytes:
            st.info(
                "왼쪽에서 의류 사진을 입력해주세요.\n\n"
                "**팁:** 단일 아이템이 선명하게 찍힌 사진일수록\n분석 정확도가 높습니다."
            )
        else:
            st.info("사진이 준비됐습니다.\n'코디 추천받기' 버튼을 눌러주세요.")

    # 비전 에이전트 실행
    if "vision_trigger" in st.session_state and not st.session_state.running:
        trigger = st.session_state.pop("vision_trigger")
        st.session_state.running = True
        st.session_state.pop("vision_result", None)

        with result_col:
            result_placeholder = st.empty()
            accumulated = ""

            with st.spinner("AI가 사진을 분석하고 코디를 추천하는 중..."):
                try:
                    for event in run_vision_agent_streaming(
                        image_bytes=trigger["bytes"],
                        media_type=trigger["media_type"],
                        location=location or "서울",
                        occasion=trigger["occasion"],
                        extra_request=trigger["extra"],
                    ):
                        etype, econtent = event["type"], event["content"]
                        if etype == "status":
                            result_placeholder.info(econtent)
                        elif etype == "stream_chunk":
                            accumulated += econtent
                            result_placeholder.markdown(accumulated + "▌")
                        elif etype == "final_answer":
                            accumulated = econtent
                except Exception as e:
                    import traceback
                    st.error(f"분석 오류: {e}")
                    st.code(traceback.format_exc())

            result_placeholder.empty()
            if accumulated:
                st.session_state["vision_result"] = accumulated

        st.session_state.running = False
        st.rerun()
