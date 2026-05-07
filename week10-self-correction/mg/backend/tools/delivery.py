"""택배 추적 — CJ대한통운, 우체국택배."""

import re
import httpx
from tools.registry import register_tool


@register_tool(
    name="delivery_tracking",
    description="택배 배송 상태를 추적합니다. CJ대한통운(10~12자리)과 우체국택배(13자리)를 지원합니다.",
    parameters={
        "type": "object",
        "properties": {
            "invoice": {"type": "string", "description": "운송장 번호 (숫자만)"},
            "carrier": {"type": "string", "enum": ["cj", "epost", "auto"], "description": "택배사 (auto면 자동 감지)", "default": "auto"},
        },
        "required": ["invoice"],
    },
)
async def delivery_tracking(invoice: str, carrier: str = "auto") -> dict:
    invoice = re.sub(r"\D", "", invoice)

    if carrier == "auto":
        carrier = "epost" if len(invoice) == 13 else "cj"

    if carrier == "cj":
        return await _track_cj(invoice)
    else:
        return await _track_epost(invoice)


async def _track_cj(invoice: str) -> dict:
    async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
        # Get CSRF token
        page = await client.get("https://www.cjlogistics.com/ko/tool/parcel/tracking")
        csrf_match = re.search(r'name="_csrf"\s+value="([^"]+)"', page.text)
        csrf = csrf_match.group(1) if csrf_match else ""

        resp = await client.post(
            "https://www.cjlogistics.com/ko/tool/parcel/tracking-detail",
            data={"paramInvcNo": invoice, "_csrf": csrf},
            headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
        )

        try:
            data = resp.json()
            result_list = data.get("parcelDetailResultMap", {}).get("resultList", [])
            if not result_list:
                return {"carrier": "cj", "invoice": invoice, "status": "조회 결과 없음"}

            # k-skills 원본 status_map 사용
            status_map = {
                "11": "상품인수",
                "21": "상품이동중",
                "41": "상품이동중",
                "42": "배송지도착",
                "44": "상품이동중",
                "82": "배송출발",
                "91": "배달완료",
            }

            events = [
                {
                    "timestamp": e.get("dTime", ""),
                    "location": e.get("regBranNm", ""),
                    "status_code": e.get("crgSt", ""),
                    "status": status_map.get(e.get("crgSt"), e.get("scanNm") or "알수없음"),
                }
                for e in result_list
            ]
            latest = events[-1] if events else {}
            return {
                "carrier": "CJ대한통운",
                "invoice": invoice,
                "status": latest.get("status", ""),
                "location": latest.get("location", ""),
                "timestamp": latest.get("timestamp", ""),
                "event_count": len(events),
                "recent_events": events[-3:],
            }
        except Exception:
            return {"carrier": "cj", "invoice": invoice, "status": "조회 실패"}


async def _track_epost(invoice: str) -> dict:
    import html as html_module

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://service.epost.go.kr/trace.RetrieveDomRigiTraceList.comm",
            data={"sid1": invoice},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        text = resp.text

        def clean(raw: str) -> str:
            t = re.sub(r"<[^>]+>", " ", raw)
            return " ".join(html_module.unescape(t).split())

        def clean_location(raw: str) -> str:
            t = clean(raw)
            return re.sub(r"\s*(TEL\s*:?\s*)?\d{2,4}[.\-]\d{3,4}[.\-]\d{4}", "", t).strip()

        # k-skills 원본: 상세 이벤트 테이블 파싱 (날짜/시간/발생국/처리현황)
        events_raw = re.findall(
            r"<tr>\s*<td>(\d{4}\.\d{2}\.\d{2})</td>\s*"
            r"<td>(\d{2}:\d{2})</td>\s*"
            r"<td>(.*?)</td>\s*"
            r"<td>\s*<span class=['\"]evtnm['\"]>(.*?)</span>(.*?)</td>\s*</tr>",
            text,
            re.S,
        )

        events = []
        if events_raw:
            for day, time_, location, status, _detail in events_raw:
                events.append({
                    "timestamp": f"{day} {time_}",
                    "location": clean_location(location),
                    "status": clean(status),
                })
        else:
            # Fallback: 단순 <td> 파싱
            rows = re.findall(r"<td[^>]*>(.*?)</td>", text, re.DOTALL)
            for i in range(0, len(rows) - 3, 4):
                events.append({
                    "timestamp": f"{clean(rows[i])} {clean(rows[i + 1])}",
                    "location": clean_location(rows[i + 2]),
                    "status": clean(rows[i + 3]),
                })

        if not events:
            return {"carrier": "우체국", "invoice": invoice, "status": "조회 결과 없음"}

        latest = events[-1]
        return {
            "carrier": "우체국택배",
            "invoice": invoice,
            "status": latest.get("status", ""),
            "location": latest.get("location", ""),
            "timestamp": latest.get("timestamp", ""),
            "event_count": len(events),
            "recent_events": events[-3:],
        }
