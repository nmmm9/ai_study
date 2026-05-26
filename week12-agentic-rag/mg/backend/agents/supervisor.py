"""Supervisor — routes the question to one or more domain agents.

Decides which domain(s) need to be invoked based on the user's question.
Outputs a `plan` list (e.g. ["shopping", "info"]).
"""

import json
from datetime import datetime, timezone, timedelta
from openai import AsyncOpenAI

from config import SUPERVISOR_MODEL

_client = AsyncOpenAI()
KST = timezone(timedelta(hours=9))


DOMAIN_DESCRIPTIONS = {
    "shopping": "쇼핑/이커머스 — 다이소, 쿠팡, 올리브영, 네이버쇼핑, 다나와 가격비교, 마켓컬리, 오늘의집, 당근(중고거래/중고차/알바/부동산), 중고차 시세",
    "lifestyle": "생활 정보 — 택배, 미세먼지, 날씨, 한강 수위, 주유소, 부동산 실거래가, 우편번호, 지하철, 맛집/술집, 주차장, 생활폐기물, 공중화장실, 공시지가, 카카오 지오코딩",
    "sports": "스포츠 — KBO 야구, K리그 축구, KBL 농구, LCK 롤챔스 결과/일정/순위",
    "news": "뉴스/콘텐츠 — 네이버 뉴스, 네이버 블로그 검색/본문, 긱뉴스",
    "finance": "금융/주식 — 한국 주식 KRX, DART 전자공시(공시/기업개황/재무제표), 대신증권 리포트",
    "government": "공공/정부 — 식약처 의약품·식품 안전, LH 청약, SH 서울주택 공고, K-Startup, 국세청 사업자등록, 응급실 병상, 법원경매 공고, 지방선거 후보, 기부처",
    "education": "교육 — 공공도서관 도서 검색, 학교 급식 식단",
    "info": "정보/유틸 — 맞춤법, 글자수, 신조어, 법률, 조선왕조실록, 한국 특허(KIPRIS), 장학금(KOSAF), 지하철 분실물, 로또, 시간/계산기, HWP 변환",
    "documents": "업로드된 문서 — 사용자가 첨부한 PDF/TXT/MD에서 정보 검색. 일반 지식이 아니라 '이 문서에서' 같은 질문이면 여기.",
    "data": "통계/실시간 데이터 — KOSIS 국가통계, 서울 핫스팟 실시간 혼잡도",
    "travel": "교통/여행 — 고속버스(KOBUS), 시외버스(Tmoney), 국립휴양림 예약 가능 객실, 도어투도어 대중교통 길찾기(ODsay)",
    "culture": "문화/엔터 — 영화관(CGV/메가박스/롯데) 시간표, 마라톤·철인3종 일정, 공연 티켓(YES24/인터파크)",
    "health": "의료/미용 — 강남언니 성형외과/피부과 검색 (응급실은 government)",
}


async def _date_context() -> str:
    """현재 날짜/요일/어제/직전 일요일 정보를 한 줄로."""
    from datetime import timedelta as _td
    weekdays = ["월", "화", "수", "목", "금", "토", "일"]
    now_dt = datetime.now(KST)
    today_wd = weekdays[now_dt.weekday()]
    yesterday_dt = now_dt - _td(days=1)
    last_sun_delta = (now_dt.weekday() - 6) % 7 or 7
    last_sun = now_dt - _td(days=last_sun_delta)
    return (
        f"오늘={now_dt.strftime('%Y-%m-%d')} ({today_wd}요일), "
        f"어제={yesterday_dt.strftime('%Y-%m-%d')} ({weekdays[yesterday_dt.weekday()]}요일), "
        f"직전 일요일={last_sun.strftime('%Y-%m-%d')}"
    )


async def supervisor_node(state: dict, model: str | None = None) -> dict:
    """Decide which domain agents to dispatch.

    Returns updated state with `plan` and `next_agent` populated.
    Uses `state["history"]` (prior turns) to resolve coreferences like
    "거기", "그것", "아까 그 약" before routing.
    """
    model = model or SUPERVISOR_MODEL
    question = state["question"]
    history: list[dict] = state.get("history", []) or []
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M (KST)")

    domain_text = "\n".join(f"- {k}: {v}" for k, v in DOMAIN_DESCRIPTIONS.items())

    system = f"""당신은 멀티 에이전트 시스템의 Supervisor입니다.
현재 시각: {now}

사용자의 질문을 보고 어떤 도메인 에이전트가 필요한지 결정하세요.
이전 대화가 있으면 맥락을 활용해 후속 질문(예: "거기는?", "그럼 가격은?")을 정확히 라우팅하세요.

도메인:
{domain_text}

규칙:
1. 한 질문에 여러 도메인이 필요할 수 있습니다 (예: "강남역 맛집 + 미세먼지" → lifestyle 1개)
2. 가능한 적은 수의 에이전트를 선택하세요 (불필요한 호출 방지)
3. 일반 대화나 도구가 필요 없는 질문은 빈 배열을 반환하세요

반드시 JSON 형식으로만 응답:
{{"reasoning": "왜 이 에이전트들을 선택했는지 한 문장", "agents": ["domain1", "domain2"]}}
"""

    messages: list[dict] = [{"role": "system", "content": system}]
    # Include compact history (last 6 turns) so Supervisor sees context
    for h in history[-6:]:
        role = h.get("role")
        content = h.get("content") or ""
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content[:600]})
    messages.append({"role": "user", "content": question})

    response = await _client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.1,
    )

    content = response.choices[0].message.content or "{}"
    try:
        parsed = json.loads(content)
        agents = parsed.get("agents", [])
        reasoning = parsed.get("reasoning", "")
    except json.JSONDecodeError:
        agents = []
        reasoning = "라우팅 실패 — 직접 답변"

    # Filter to known domains
    valid = [a for a in agents if a in DOMAIN_DESCRIPTIONS]

    return {
        "plan": valid,
        "completed_agents": [],
        "messages": [
            {"role": "system", "content": f"[Supervisor] {reasoning}"}
        ],
        "_reasoning": reasoning,
    }
