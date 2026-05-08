"""우편번호 검색 — 우체국 ePost.

k-skills 원본: hidden input 필드 sch_zipcode, sch_address1, sch_bdNm 파싱.
curl --http1.1 --tls-max 1.2 경로가 더 안정적이므로 subprocess 사용.
"""

import html as html_module
import re
import subprocess
from tools.registry import register_tool


@register_tool(
    name="zipcode_search",
    description="한국 주소로 우편번호를 검색합니다.",
    parameters={
        "type": "object",
        "properties": {
            "address": {"type": "string", "description": "검색할 주소 (예: 강남대로, 테헤란로, 세종대로 209)"},
        },
        "required": ["address"],
    },
)
async def zipcode_search(address: str) -> dict:
    try:
        # k-skills 원본: curl --http1.1 --tls-max 1.2 경로가 더 안정적
        result = subprocess.run(
            [
                "curl",
                "--http1.1",
                "--tls-max", "1.2",
                "--silent", "--show-error",
                "--location",
                "--retry", "2",
                "--retry-all-errors",
                "--retry-delay", "1",
                "--max-time", "15",
                "--get",
                "--data-urlencode", f"keyword={address}",
                "https://parcel.epost.go.kr/parcel/comm/zipcode/comm_newzipcd_list.jsp",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=20,
        )
        page = result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        # curl 없으면 httpx fallback
        import httpx
        async with httpx.AsyncClient(timeout=15, verify=False) as client:
            resp = await client.get(
                "https://parcel.epost.go.kr/parcel/comm/zipcode/comm_newzipcd_list.jsp",
                params={"keyword": address},
            )
            if resp.status_code != 200:
                return {"error": "우편번호 검색 실패"}
            page = resp.text

    # k-skills 원본: sch_zipcode, sch_address1, sch_bdNm hidden input 파싱
    matches = re.findall(
        r'name="sch_zipcode"\s+value="([^"]+)".*?'
        r'name="sch_address1"\s+value="([^"]+)".*?'
        r'name="sch_bdNm"\s+value="([^"]*)"',
        page,
        re.S,
    )

    results = []
    if matches:
        for zip_code, addr, building in matches[:10]:
            suffix = f" ({building})" if building else ""
            results.append({
                "zipcode": zip_code,
                "address": html_module.unescape(addr) + suffix,
            })
    else:
        # Fallback: <td> 파싱
        rows = re.findall(r"<td[^>]*>(.*?)</td>", page, re.DOTALL)
        for i in range(0, len(rows) - 1, 2):
            zipcode = re.sub(r"<[^>]+>", "", rows[i]).strip()
            addr = re.sub(r"<[^>]+>", "", rows[i + 1]).strip()
            if zipcode and len(zipcode) == 5:
                results.append({"zipcode": zipcode, "address": addr})

    return {
        "query": address,
        "count": len(results),
        "results": results[:10],
    }
