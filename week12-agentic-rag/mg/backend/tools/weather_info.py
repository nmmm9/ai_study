"""현재 날짜/시간 + 간단한 계산 — 기본 유틸리티 도구."""

from datetime import datetime
from tools.registry import register_tool


@register_tool(
    name="get_current_time",
    description="현재 한국 날짜와 시간을 반환합니다.",
    parameters={"type": "object", "properties": {}},
)
async def get_current_time() -> dict:
    from datetime import timezone, timedelta
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    weekday = ["월", "화", "수", "목", "금", "토", "일"][now.weekday()]
    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "weekday": f"{weekday}요일",
        "formatted": now.strftime(f"%Y년 %m월 %d일 ({weekday}) %H:%M"),
    }


@register_tool(
    name="calculate",
    description="수학 계산을 수행합니다 (사칙연산, 퍼센트). 날짜 계산은 date_arithmetic 도구를 사용하세요.",
    parameters={
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "수학식 (예: 1500000 * 0.033, 45000 / 12). 날짜 형식 금지."},
        },
        "required": ["expression"],
    },
)
async def calculate(expression: str) -> dict:
    expr = expression.strip()
    # Reject obvious date patterns to avoid leading-zero SyntaxError
    if "-" in expr and any(part.isdigit() and len(part) == 2 and part.startswith("0")
                            for part in expr.replace(" ", "").split("-")):
        return {
            "error": "날짜 계산은 calculate 도구를 사용하지 마세요. date_arithmetic 도구를 사용하세요.",
            "expression": expression,
        }
    try:
        allowed = set("0123456789+-*/.() %")
        if not all(c in allowed for c in expr.replace(" ", "")):
            return {"error": "허용되지 않는 문자가 포함되어 있습니다"}
        result = eval(expr)
        return {"expression": expression, "result": result}
    except Exception as e:
        return {"error": f"계산 실패: {str(e)}"}


@register_tool(
    name="date_arithmetic",
    description="날짜 계산 전용 도구. 오늘로부터 N일 전/후, 특정 요일의 직전 날짜 등을 계산합니다.",
    parameters={
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["add_days", "subtract_days", "last_weekday", "next_weekday", "weekday_of"],
                "description": "add_days/subtract_days: N일 가감. last_weekday/next_weekday: 직전/다음 특정 요일. weekday_of: 특정 날짜의 요일 조회.",
            },
            "base_date": {
                "type": "string",
                "description": "기준 날짜 YYYY-MM-DD (없으면 오늘)",
            },
            "days": {
                "type": "integer",
                "description": "add_days/subtract_days 용. 가감할 일수.",
            },
            "weekday": {
                "type": "string",
                "enum": ["월", "화", "수", "목", "금", "토", "일"],
                "description": "last_weekday/next_weekday 용. 찾을 요일.",
            },
        },
        "required": ["operation"],
    },
)
async def date_arithmetic(operation: str, base_date: str | None = None,
                          days: int = 0, weekday: str | None = None) -> dict:
    from datetime import timezone, timedelta, date as date_cls
    kst = timezone(timedelta(hours=9))
    if base_date:
        try:
            y, m, d = base_date.split("-")
            base = date_cls(int(y), int(m), int(d))
        except Exception as e:
            return {"error": f"잘못된 base_date 형식: {e}. YYYY-MM-DD 필요"}
    else:
        base = datetime.now(kst).date()

    weekdays = ["월", "화", "수", "목", "금", "토", "일"]

    def format_result(d: date_cls) -> dict:
        return {
            "date": d.strftime("%Y-%m-%d"),
            "weekday": weekdays[d.weekday()] + "요일",
            "formatted": d.strftime(f"%Y년 %m월 %d일 ({weekdays[d.weekday()]})"),
        }

    if operation == "add_days":
        return format_result(base + timedelta(days=days))

    if operation == "subtract_days":
        return format_result(base - timedelta(days=days))

    if operation == "weekday_of":
        return format_result(base)

    if operation in ("last_weekday", "next_weekday"):
        if weekday not in weekdays:
            return {"error": "weekday 인자가 필요합니다 (월/화/.../일)"}
        target_idx = weekdays.index(weekday)
        current_idx = base.weekday()
        if operation == "last_weekday":
            # 직전 해당 요일 (오늘이 목요일이고 weekday=일이면 직전 일요일)
            delta = (current_idx - target_idx) % 7
            if delta == 0:
                delta = 7  # 같은 요일이면 1주 전
            return format_result(base - timedelta(days=delta))
        else:  # next_weekday
            delta = (target_idx - current_idx) % 7
            if delta == 0:
                delta = 7
            return format_result(base + timedelta(days=delta))

    return {"error": f"지원하지 않는 operation: {operation}"}
