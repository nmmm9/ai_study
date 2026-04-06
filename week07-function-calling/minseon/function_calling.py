"""
7주차: Function Calling
========================================
핵심 개념:
  1. 외부 함수 호출 인터페이스 설계
  2. JSON 스키마 정의
  3. 질문 의도에 따른 함수 자동 호출

흐름:
  사용자 질문
    → GPT가 의도 파악
    → 어떤 함수를 호출할지 결정 (tool_choice)
    → 함수 실행
    → 결과를 바탕으로 최종 답변 생성
"""

import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


# ============================================================
# STEP 1: 외부 함수 정의 (실제로 실행될 Python 함수)
# ============================================================

def get_weather(city: str, unit: str = "celsius") -> dict:
    """날씨 조회"""
    dummy = {
        "서울": {"temp": 18, "condition": "맑음", "humidity": 45},
        "부산": {"temp": 22, "condition": "흐림", "humidity": 60},
        "제주": {"temp": 25, "condition": "비",   "humidity": 80},
    }
    data = dummy.get(city, {"temp": 20, "condition": "알 수 없음", "humidity": 50})
    temp = data["temp"] if unit == "celsius" else data["temp"] * 9/5 + 32
    return {
        "city": city,
        "temperature": f"{temp}°{'C' if unit == 'celsius' else 'F'}",
        "condition": data["condition"],
        "humidity": f"{data['humidity']}%",
    }


def search_product(keyword: str, max_price: int = None) -> dict:
    """쇼핑몰 상품 검색"""
    products = [
        {"name": "아이폰 15",    "category": "스마트폰", "price": 1_200_000},
        {"name": "갤럭시 S24",   "category": "스마트폰", "price": 1_100_000},
        {"name": "맥북 에어",    "category": "노트북",   "price": 1_500_000},
        {"name": "나이키 운동화","category": "신발",     "price":   150_000},
        {"name": "패딩 점퍼",    "category": "의류",     "price":   200_000},
    ]
    results = [p for p in products if keyword in p["name"]]
    if max_price:
        results = [p for p in results if p["price"] <= max_price]
    return {"keyword": keyword, "count": len(results), "results": results}


def calculate(expression: str) -> dict:
    """사칙연산 계산"""
    allowed = set("0123456789+-*/(). ")
    if not all(c in allowed for c in expression):
        return {"error": "허용되지 않는 문자가 포함되어 있습니다."}
    try:
        result = eval(expression)
        return {"expression": expression, "result": result}
    except Exception as e:
        return {"error": str(e)}


def get_exchange_rate(from_currency: str, to_currency: str) -> dict:
    """환율 조회"""
    rates = {
        ("USD", "KRW"): 1340.0,
        ("EUR", "KRW"): 1450.0,
        ("JPY", "KRW"): 8.9,
        ("KRW", "USD"): round(1 / 1340.0, 6),
    }
    key = (from_currency.upper(), to_currency.upper())
    rate = rates.get(key)
    if rate is None:
        return {"error": f"{from_currency} → {to_currency} 환율 정보 없음"}
    return {
        "from": from_currency.upper(),
        "to":   to_currency.upper(),
        "rate": rate,
        "example": f"1 {from_currency.upper()} = {rate} {to_currency.upper()}",
    }


# ============================================================
# STEP 2: JSON 스키마 정의 (OpenAI tools 형식)
# - 모델이 이 스키마를 보고 어떤 함수를 호출할지, 어떤 인자를 넘길지 결정
# ============================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "특정 도시의 현재 날씨(기온, 상태, 습도)를 조회합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "날씨를 조회할 도시 이름 (예: 서울, 부산, 제주)",
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "온도 단위 (기본값: celsius)",
                    },
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_product",
            "description": "쇼핑몰에서 상품을 키워드로 검색합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "검색할 상품 키워드 (예: 아이폰, 운동화)",
                    },
                    "max_price": {
                        "type": "integer",
                        "description": "최대 가격 필터 (원 단위, 선택사항)",
                    },
                },
                "required": ["keyword"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "사칙연산 수식을 계산합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "계산할 수식 (예: 1234 * 5678, (100 + 200) / 3)",
                    },
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_exchange_rate",
            "description": "두 통화 간의 환율을 조회합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_currency": {
                        "type": "string",
                        "description": "변환할 통화 코드 (예: USD, EUR, JPY)",
                    },
                    "to_currency": {
                        "type": "string",
                        "description": "변환될 통화 코드 (예: KRW)",
                    },
                },
                "required": ["from_currency", "to_currency"],
            },
        },
    },
]


# ============================================================
# STEP 3: 함수 실행 라우터
# - 모델이 선택한 함수 이름과 인자를 받아 실제 함수 실행
# ============================================================

FUNCTION_MAP = {
    "get_weather":      get_weather,
    "search_product":   search_product,
    "calculate":        calculate,
    "get_exchange_rate": get_exchange_rate,
}

def execute_tool(name: str, arguments: dict) -> str:
    func = FUNCTION_MAP.get(name)
    if func is None:
        return json.dumps({"error": f"알 수 없는 함수: {name}"}, ensure_ascii=False)
    result = func(**arguments)
    return json.dumps(result, ensure_ascii=False)


# ============================================================
# STEP 4: Function Calling 핵심 루프
# ============================================================

def run(user_message: str) -> str:
    """
    질문 의도에 따라 함수를 자동 선택하고 호출하는 메인 함수

    [흐름]
    1. 사용자 메시지 → GPT 전송 (tools 목록 포함)
    2. GPT가 tool_calls 반환 → 어떤 함수를 어떤 인자로 호출할지
    3. 해당 함수 실행
    4. 실행 결과를 messages에 추가 → GPT가 최종 답변 생성
    """
    print(f"\n{'='*55}")
    print(f"[질문] {user_message}")
    print(f"{'='*55}")

    messages = [
        {
            "role": "system",
            "content": (
                "당신은 유용한 AI 어시스턴트입니다. "
                "날씨, 상품 검색, 계산, 환율 조회가 필요한 경우 "
                "반드시 제공된 함수를 사용하세요."
            ),
        },
        {"role": "user", "content": user_message},
    ]

    # ── 1단계: GPT에게 함수 목록 전달 ──
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",   # "auto": GPT가 알아서 함수 선택
                              # "none": 함수 사용 안 함
                              # {"type":"function","function":{"name":"..."}}: 강제 지정
    )

    msg = response.choices[0].message

    # ── 2단계: GPT가 함수 호출을 선택한 경우 ──
    if msg.tool_calls:
        print(f"\n[GPT 판단] 함수 호출 필요 → {len(msg.tool_calls)}개")
        messages.append(msg)

        for tc in msg.tool_calls:
            name = tc.function.name
            args = json.loads(tc.function.arguments)

            print(f"\n  함수명 : {name}")
            print(f"  인자   : {json.dumps(args, ensure_ascii=False)}")

            # ── 3단계: 실제 함수 실행 ──
            result = execute_tool(name, args)
            print(f"  결과   : {result}")

            # 함수 결과를 messages에 추가 (role: tool)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

        # ── 4단계: 함수 결과 바탕으로 최종 답변 생성 ──
        final = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
        )
        answer = final.choices[0].message.content

    else:
        # 함수 호출 없이 바로 답변 (일반 지식 질문 등)
        print("\n[GPT 판단] 함수 호출 불필요 → 직접 답변")
        answer = msg.content

    print(f"\n[답변] {answer}")
    return answer


# ============================================================
# 실행
# ============================================================

if __name__ == "__main__":
    questions = [
        "서울 날씨 어때?",                         # → get_weather
        "1달러가 몇 원이야?",                       # → get_exchange_rate
        "아이폰 검색해줘",                          # → search_product
        "1234 곱하기 5678은?",                      # → calculate
        "100만원 이하 상품 찾아줘 갤럭시",           # → search_product (max_price 포함)
        "파이썬이 뭐야?",                           # → 함수 없이 직접 답변
    ]

    for q in questions:
        run(q)
        print()
