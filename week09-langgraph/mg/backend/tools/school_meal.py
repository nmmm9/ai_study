"""학교 급식 식단 — NEIS via k-skill-proxy."""

from datetime import datetime, timezone, timedelta
import httpx
from tools.registry import register_tool

PROXY = "https://k-skill-proxy.nomadamas.org"
KST = timezone(timedelta(hours=9))


@register_tool(
    name="school_meal",
    description="한국 초·중·고등학교 급식 식단을 조회합니다. 학교 이름과 교육청을 입력하세요. 날짜 미지정 시 오늘 날짜 사용.",
    parameters={
        "type": "object",
        "properties": {
            "school_name": {"type": "string", "description": "학교 이름 (예: 미래초등학교)"},
            "education_office": {"type": "string", "description": "교육청 이름 (예: 서울특별시교육청)"},
            "meal_date": {"type": "string", "description": "YYYYMMDD (없으면 오늘)"},
        },
        "required": ["school_name", "education_office"],
    },
)
async def school_meal(school_name: str, education_office: str, meal_date: str | None = None) -> dict:
    if not meal_date:
        meal_date = datetime.now(KST).strftime("%Y%m%d")

    async with httpx.AsyncClient(timeout=15) as client:
        # 1. Find school code
        sresp = await client.get(
            f"{PROXY}/v1/neis/school-search",
            params={"educationOffice": education_office, "schoolName": school_name},
        )
        if sresp.status_code != 200:
            return {"error": f"학교 검색 실패 (status {sresp.status_code})"}

        sdata = sresp.json()
        schools = sdata.get("schools") or sdata.get("results") or []
        if not schools:
            return {"error": "학교를 찾을 수 없습니다", "school": school_name}

        first = schools[0]
        edu_code = first.get("ATPT_OFCDC_SC_CODE") or first.get("educationOfficeCode")
        sch_code = first.get("SD_SCHUL_CODE") or first.get("schoolCode")
        if not edu_code or not sch_code:
            return {"error": "학교 코드를 가져올 수 없습니다", "first": first}

        # 2. Get meal
        mresp = await client.get(
            f"{PROXY}/v1/neis/school-meal",
            params={
                "educationOfficeCode": edu_code,
                "schoolCode": sch_code,
                "mealDate": meal_date,
            },
        )
        if mresp.status_code == 200:
            return mresp.json()
        return {"error": f"급식 조회 실패 (status {mresp.status_code})", "body": mresp.text[:300]}
