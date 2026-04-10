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
    description="수학 계산을 수행합니다. 사칙연산, 퍼센트 계산 등에 사용합니다.",
    parameters={
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "계산식 (예: 1500000 * 0.033, 45000 / 12)"},
        },
        "required": ["expression"],
    },
)
async def calculate(expression: str) -> dict:
    try:
        # Safe eval: only allow math operations
        allowed = set("0123456789+-*/.() %")
        if not all(c in allowed for c in expression.replace(" ", "")):
            return {"error": "허용되지 않는 문자가 포함되어 있습니다"}
        result = eval(expression)
        return {"expression": expression, "result": result}
    except Exception as e:
        return {"error": f"계산 실패: {str(e)}"}
