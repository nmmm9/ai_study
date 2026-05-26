"""Domain Agent — runs a small ReAct-style loop with only its own tools.

Each domain agent (shopping, lifestyle, sports, info) gets:
- A domain-specific system prompt
- Only the tools belonging to its domain
- Its own tool-call loop (max 3 rounds)

This is a "subgraph" inside each main graph node. The benefit over the
8-week single-LLM approach is:
- Smaller tool list per call → fewer hallucinations
- Domain-specific instructions
- Parallel-ready (each domain is independent)
"""

import json
from datetime import datetime, timezone, timedelta
from openai import AsyncOpenAI

from tools.registry import _tools, execute_tool
from tools import get_tools_for_domain
from config import DOMAIN_MODEL

_client = AsyncOpenAI()
KST = timezone(timedelta(hours=9))
MAX_AGENT_ROUNDS = 3


DOMAIN_PROMPTS = {
    "shopping": """당신은 '쇼핑 전문' 에이전트입니다.
다이소, 쿠팡, 올리브영, 네이버쇼핑, 중고차 등 상품/매장/재고/가격비교 전문가.

원칙:
- 매장 재고 조회는 '매장 검색 → 재고 조회' 순서로 진행
- 가격 비교 시 단위(개/팩)와 배송비를 명확히 표기
- 네이버쇼핑은 가격 비교 (sort=price_asc), 평점/리뷰 (sort=review) 등 sort 옵션 활용
- 검색 결과가 없으면 솔직하게 0개라고 답변""",

    "lifestyle": """당신은 '생활 정보 전문' 에이전트입니다.
택배, 미세먼지, 날씨, 한강 수위, 주유소, 부동산, 지하철, 맛집/술집, 주차장, 생활폐기물 전문가.

원칙:
- 미세먼지 조회는 "시도 + 시" 형식 (예: "경기 안양", "서울 강남구")
- 날씨는 위도/경도 기준 (서울 시청=37.5665,126.9780)
- 위치 기반 검색(맛집/주유소/주차장)은 정확한 동/구 단위로
- 부동산은 행정구역 코드(lawd_cd)가 필요하면 zipcode_search로 먼저 조회""",

    "sports": """당신은 '스포츠 전문' 에이전트입니다.
KBO 야구, K리그 축구, KBL 농구, LCK 롤챔스 결과/일정/순위 전문가.

원칙:
- 날짜 미지정 시 오늘 또는 가장 최근 경기 조회
- 월요일은 KBO 경기가 없으므로 빈 결과여도 정상
- 팀명은 정확한 한글 표기 사용 (예: "서울 SK", "부산 KCC")""",

    "news": """당신은 '뉴스 전문' 에이전트입니다.
네이버 뉴스, 긱뉴스 등 최신 콘텐츠를 검색합니다.

원칙:
- 네이버 뉴스는 sort=date(최신순)이 기본
- 긱뉴스는 IT/개발 위주이므로 일반 시사는 네이버 뉴스 사용
- 결과는 5~10개로 압축, 제목+요약+링크 위주로""",

    "finance": """당신은 '금융 전문' 에이전트입니다.
한국 주식(KRX) 종목 검색과 시세 조회 전문가.

원칙:
- 종목명만 입력해도 종목코드를 자동으로 찾아 반환
- 기준일자(bas_dd) 미지정 시 최신 거래일 자동 사용""",

    "government": """당신은 '공공/정부 전문' 에이전트입니다.
식약처 의약품/식품 안전, LH 청약 공고, K-Startup 창업지원, 국세청 사업자등록 진위확인 전문가.

원칙:
- 의약품 조회는 정확한 제품명 사용 (예: "타이레놀")
- 식품 안전은 키워드 기반 검색
- LH 공고는 광역시도(예: "서울특별시") + 상태(공고중)
- K-Startup 검색은 사업명/공고명 키워드, 통계는 연도 단위로 조회
- 사업자등록 진위확인은 b_no(10자리), start_dt(YYYYMMDD), p_nm(대표자명) 필수""",

    "education": """당신은 '교육 전문' 에이전트입니다.
공공도서관 도서 검색과 학교 급식 식단 조회.

원칙:
- 도서 검색은 키워드 기반 (저자/제목 모두 가능)
- 학교 급식은 학교명 + 교육청(예: "서울특별시교육청") 필수
- 날짜 미지정 시 오늘 급식""",

    "info": """당신은 '정보/유틸 전문' 에이전트입니다.
맞춤법, 글자수, 법률, 조선왕조실록, 로또, 계산, 시간, 날짜 계산, HWP 변환 등 유틸리티.

원칙:
- 법률 검색은 action 파라미터(search/search_precedents/search_ordinance)를 정확히 선택
- 조선왕조실록은 인물/사건 키워드를 정확히 입력
- 글자수는 텍스트 그대로 전달, 결과 그대로 표시
- 계산 결과는 단계별로 설명

날짜/요일 계산 절대 규칙:
- "지난주 ○요일", "어제", "3일 후" 같은 날짜는 date_arithmetic 도구만 사용하세요.
- "지난주 일요일" → date_arithmetic(operation="last_weekday", weekday="일")
- "어제" → date_arithmetic(operation="subtract_days", days=1)
- "3일 후" → date_arithmetic(operation="add_days", days=3)
- calculate 도구에 "2026-05-26 - 7" 같은 형식 절대 금지. 항상 SyntaxError 발생.
- 도구 호출 없이 머릿속에서 날짜를 추측하지 마세요. 반드시 도구로 확인.""",

    "documents": """당신은 '문서 검색 전문' 에이전트입니다.
사용자가 업로드한 PDF/TXT/MD 문서를 ChromaDB 벡터 검색으로 조회합니다.

원칙:
- document_search 는 단발 검색용. 답변에 출처(파일명, 페이지)를 반드시 포함
- list_uploaded_documents 로 어떤 문서가 있는지 먼저 확인 가능
- 검색 결과가 빈약하면 다른 키워드로 재검색""",

    "data": """당신은 '통계/실시간 데이터 전문' 에이전트입니다.
KOSIS 국가통계와 서울 핫스팟 혼잡도를 조회합니다.

원칙:
- KOSIS 는 '검색 → 메타 조회 → 데이터 조회' 순서로 진행 (kosis_search → kosis_meta → kosis_data)
- 통계 시점은 prdSe (Y=연간, Q=분기, M=월간) 명시
- 서울 혼잡도는 121개 핫스팟 중 정확한 이름 필요 (예: 강남역, 명동, 홍대입구, 경복궁)""",

    "travel": """당신은 '교통/여행 전문' 에이전트입니다.
고속버스, 시외버스, 국립휴양림, 대중교통 길찾기 도구를 다룹니다.

원칙:
- 버스 조회는 '터미널 코드 목록 → 출발/도착 코드 → 시간표' 순서
- 날짜는 YYYYMMDD 형식
- korean_transit_route 는 ODsay 키 필요 (없으면 안내 메시지 반환)
- 휴양림은 JS SPA 라 직접 호출 제한적 — 안내 위주""",

    "culture": """당신은 '문화/엔터 전문' 에이전트입니다.
영화관 시간표, 마라톤 일정, 공연 티켓 정보를 조회합니다.

원칙:
- 영화관은 chain (cgv/megabox/lotte) 명시
- 티켓은 platform (yes24/interpark) + goods_code 필요 (URL 마지막 숫자)
- 잔여석/시간표는 JS 동적 로딩 — 공식 사이트 안내 가능""",

    "health": """당신은 '의료/미용 전문' 에이전트입니다.
강남언니 성형/피부과 검색을 다룹니다.

원칙:
- 강남언니는 NEXT_DATA payload 파싱
- 응급실 / 의약품 / 식품 안전 정보는 government 도메인 사용""",
}


def _get_tool_schemas(domain: str) -> list[dict]:
    """Build OpenAI tool schemas for tools in this domain only."""
    tool_names = get_tools_for_domain(domain)
    schemas = []
    for name in tool_names:
        tool = _tools.get(name)
        if not tool:
            continue
        schemas.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"],
            },
        })
    return schemas


async def run_domain_agent(
    domain: str,
    question: str,
    model: str | None = None,
    on_event=None,
    history: list[dict] | None = None,
):
    """Run one domain agent. Returns (results, messages_log).

    on_event(event_type, data) — optional callback for UI events:
      - "tool_call":  {"domain", "tool", "args"}
      - "tool_result": {"domain", "tool", "result"}
    """
    model = model or DOMAIN_MODEL
    history = history or []
    now = datetime.now(KST).strftime("%Y년 %m월 %d일 %H:%M")
    system = f"{DOMAIN_PROMPTS[domain]}\n\n현재 시각: {now} (KST)"

    messages: list[dict] = [{"role": "system", "content": system}]
    # Inject prior turns for context (limit to last 4 turns to save tokens)
    for h in history[-4:]:
        role = h.get("role")
        content = h.get("content") or ""
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content[:500]})
    messages.append({"role": "user", "content": question})
    tool_schemas = _get_tool_schemas(domain)

    if not tool_schemas:
        return [], messages

    collected = []

    for _ in range(MAX_AGENT_ROUNDS):
        response = await _client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tool_schemas,
            temperature=0.2,
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            # Agent decided no more tool calls needed
            if msg.content:
                messages.append({"role": "assistant", "content": msg.content})
            break

        messages.append(msg.model_dump())

        for tc in msg.tool_calls:
            fn_name = tc.function.name
            try:
                fn_args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                fn_args = {}

            if on_event:
                await on_event("tool_call", {
                    "domain": domain,
                    "tool": fn_name,
                    "args": fn_args,
                })

            result = await execute_tool(fn_name, fn_args)

            if on_event:
                await on_event("tool_result", {
                    "domain": domain,
                    "tool": fn_name,
                    "result": result[:600],
                })

            collected.append({
                "domain": domain,
                "tool": fn_name,
                "args": fn_args,
                "result": result,
            })

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

    return collected, messages
