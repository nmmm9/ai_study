"""OOTD 에이전트 - 날씨, 옷장, 색상 조합을 고려한 코디 추천 AI"""

import json
import anthropic
from anthropic import beta_tool

from tools.weather import fetch_weather
from tools.wardrobe import filter_wardrobe, get_wardrobe_summary
from tools.colors import get_color_combinations, get_seasonal_palette

# Anthropic 클라이언트 초기화
client = anthropic.Anthropic()

# ─────────────────────────────────────────────
# 도구 정의 (beta_tool 데코레이터 사용)
# ─────────────────────────────────────────────

@beta_tool
def get_weather(location: str) -> str:
    """현재 날씨 정보를 가져옵니다.

    Args:
        location: 날씨를 조회할 도시 또는 지역 이름 (예: 서울, 부산, Seoul, Busan).
    """
    result = fetch_weather(location)
    return json.dumps(result, ensure_ascii=False, indent=2)


@beta_tool
def get_wardrobe_items(
    category: str = "",
    season: str = "",
    weather_condition: str = "",
) -> str:
    """옷장에 있는 아이템 목록을 조회합니다.

    Args:
        category: 카테고리 필터. 가능한 값: 상의, 하의, 아우터, 신발, 액세서리. 빈 문자열이면 전체 조회.
        season: 계절 필터. 가능한 값: 봄, 여름, 가을, 겨울. 빈 문자열이면 전체 조회.
        weather_condition: 날씨 조건 필터. 가능한 값: 맑음, 흐림, 비, 눈. 빈 문자열이면 전체 조회.
    """
    items = filter_wardrobe(
        category=category if category else None,
        season=season if season else None,
        weather=weather_condition if weather_condition else None,
    )
    result = {
        "items": items,
        "count": len(items),
        "filters_applied": {
            "category": category or "전체",
            "season": season or "전체",
            "weather_condition": weather_condition or "전체",
        },
    }
    return json.dumps(result, ensure_ascii=False, indent=2)


@beta_tool
def get_wardrobe_overview() -> str:
    """옷장 전체 구성 요약을 가져옵니다. 어떤 카테고리와 색상의 아이템이 있는지 파악할 때 사용하세요."""
    summary = get_wardrobe_summary()
    return json.dumps(summary, ensure_ascii=False, indent=2)


@beta_tool
def get_color_pairings(color: str) -> str:
    """특정 색상과 잘 어울리는 색상 조합을 가져옵니다.

    Args:
        color: 기준 색상 이름 (영문). 예: white, black, navy, beige, gray, blue, camel, burgundy, khaki, sage.
    """
    result = get_color_combinations(color)
    return json.dumps(result, ensure_ascii=False, indent=2)


@beta_tool
def get_season_palette(season: str) -> str:
    """계절별 추천 색상 팔레트를 가져옵니다.

    Args:
        season: 계절 이름. 가능한 값: 봄, 여름, 가을, 겨울, 봄/가을.
    """
    result = get_seasonal_palette(season)
    return json.dumps(result, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────
# 에이전트 시스템 프롬프트
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """당신은 전문 패션 스타일리스트 AI입니다.
사용자의 현재 날씨와 실제 옷장 아이템을 분석하여 최적의 OOTD(오늘의 코디)를 추천해드립니다.

## 추천 프로세스
1. **날씨 확인**: get_weather 도구로 현재 날씨와 기온을 확인합니다.
2. **옷장 파악**: get_wardrobe_overview로 전체 구성을 파악하고, get_wardrobe_items로 날씨/계절에 맞는 아이템을 필터링합니다.
3. **색상 분석**: get_color_pairings를 활용해 어울리는 색상 조합을 확인합니다.
4. **코디 완성**: 수집한 정보를 바탕으로 완성된 코디를 제안합니다.

## 추천 원칙
- **실용성 우선**: 날씨(기온, 날씨 조건)에 적합한 옷차림을 최우선으로 고려합니다.
- **실제 보유 아이템만**: 옷장에 있는 아이템만을 사용하여 코디를 구성합니다.
- **색상 조화**: 색채학 기반의 어울리는 색상 조합을 적용합니다.
- **레이어링**: 일교차가 큰 날씨에는 레이어링 방법을 제안합니다.

## 응답 형식
코디 추천 시 다음 내용을 포함하세요:
1. 📍 **날씨 요약**: 현재 날씨와 코디 포인트
2. 👗 **추천 코디**: 상의 → 하의 → 아우터 → 신발 → 액세서리 순으로 구체적인 아이템
3. 🎨 **색상 분석**: 선택한 색상 조합과 그 이유
4. 💡 **스타일링 팁**: 추가 연출 방법이나 주의사항"""


# ─────────────────────────────────────────────
# 에이전트 실행 함수
# ─────────────────────────────────────────────

def run_ootd_agent(
    location: str,
    user_request: str = "",
    verbose: bool = True,
) -> str:
    """OOTD 에이전트를 실행하여 코디를 추천합니다.

    Args:
        location: 현재 위치 (날씨 조회에 사용)
        user_request: 추가 요청사항 (예: "오늘 회사 면접이 있어요", "데이트 코디 추천해줘")
        verbose: True이면 도구 사용 과정을 출력합니다

    Returns:
        최종 코디 추천 텍스트
    """
    # 초기 메시지 구성
    initial_message = f"위치: {location}\n"
    if user_request:
        initial_message += f"요청사항: {user_request}\n"
    initial_message += "\n오늘 날씨에 맞는 OOTD 코디를 추천해주세요."

    if verbose:
        print(f"\n{'='*50}")
        print(f"📍 위치: {location}")
        if user_request:
            print(f"📝 요청: {user_request}")
        print(f"{'='*50}")
        print("🤖 에이전트가 분석을 시작합니다...\n")

    # 도구 목록
    tools = [
        get_weather,
        get_wardrobe_items,
        get_wardrobe_overview,
        get_color_pairings,
        get_season_palette,
    ]

    # Tool Runner로 에이전트 실행
    runner = client.beta.messages.tool_runner(
        model="claude-opus-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        tools=tools,
        messages=[{"role": "user", "content": initial_message}],
    )

    final_response = ""

    for message in runner:
        if verbose:
            # 도구 사용 현황 출력
            for block in message.content:
                if hasattr(block, "type") and block.type == "tool_use":
                    tool_icons = {
                        "get_weather": "🌤️",
                        "get_wardrobe_items": "👗",
                        "get_wardrobe_overview": "📦",
                        "get_color_pairings": "🎨",
                        "get_season_palette": "🍂",
                    }
                    icon = tool_icons.get(block.name, "🔧")
                    print(f"{icon} {block.name} 호출 중...")

        # 텍스트 응답 수집
        for block in message.content:
            if hasattr(block, "type") and block.type == "text" and block.text:
                final_response = block.text

    return final_response


def run_interactive_session(location: str) -> None:
    """대화형 OOTD 세션을 실행합니다."""
    print(f"\n{'='*50}")
    print("👗 OOTD 스타일리스트 AI에 오신 것을 환영합니다!")
    print(f"{'='*50}")
    print("종료하려면 'quit' 또는 'exit'를 입력하세요.\n")

    while True:
        user_input = input("💬 요청사항 (없으면 엔터): ").strip()

        if user_input.lower() in ("quit", "exit", "종료"):
            print("\n👋 이용해 주셔서 감사합니다!")
            break

        result = run_ootd_agent(location=location, user_request=user_input)

        print(f"\n{'─'*50}")
        print(result)
        print(f"{'─'*50}\n")

        cont = input("다른 코디도 추천받으시겠어요? (y/n): ").strip().lower()
        if cont != "y":
            print("\n👋 스타일리시한 하루 되세요!")
            break
