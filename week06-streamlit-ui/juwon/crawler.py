"""
점핏(Jumpit) 신입 채용공고 크롤러
- 인증 없이 사용 가능한 공개 API 활용
- 결과를 job_postings_crawled.md 형식으로 저장
"""

import time
import random
import requests
from pathlib import Path

# ── 설정 ──────────────────────────────────────────────────────────
MAX_PAGES   = 5      # 목록 페이지 수 (페이지당 20개 = 최대 100개 공고)
DELAY       = 0.8    # 요청 간 대기(초)
OUTPUT_FILE = Path(__file__).parent / "job_postings_crawled.md"

BASE_URL  = "https://jumpit-api.saramin.co.kr/api"
HEADERS   = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://www.jumpit.co.kr/",
}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)


# ── 목록 수집 ─────────────────────────────────────────────────────
def get_position_ids(page: int) -> list[dict]:
    """신입(years=0) 공고 목록에서 id, 회사명, 직무명 수집"""
    params = {
        "sort":  "rsp_rate",
        "years": 0,           # 신입
        "page":  page,
    }
    try:
        resp = SESSION.get(f"{BASE_URL}/positions", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        positions = data.get("result", {}).get("positions", [])
        print(f"  [목록] {page}페이지 → {len(positions)}개")
        return [
            {
                "id":      p["id"],
                "company": p.get("companyName", ""),
                "title":   p.get("title", ""),
            }
            for p in positions
        ]
    except Exception as e:
        print(f"  [목록 오류] {page}페이지: {e}")
        return []


# ── 상세 수집 ─────────────────────────────────────────────────────
def get_position_detail(position_id: int) -> dict | None:
    """공고 상세 API에서 주요업무/자격요건/우대사항 수집"""
    try:
        resp = SESSION.get(f"{BASE_URL}/position/{position_id}", timeout=10)
        resp.raise_for_status()
        return resp.json().get("result", {})
    except Exception as e:
        print(f"    [상세 오류] id={position_id}: {e}")
        return None


# ── md 변환 ───────────────────────────────────────────────────────
def to_md_block(idx: int, detail: dict) -> str:
    company    = detail.get("companyName", "").strip()
    title      = detail.get("title", "").strip()
    resp       = (detail.get("responsibility", "") or "").strip()
    qual       = (detail.get("qualifications", "") or "").strip()
    preferred  = (detail.get("preferredRequirements", "") or "").strip()
    welfare    = (detail.get("welfare", "") or "").strip()
    tech       = ", ".join(
        t.get("name", "") for t in detail.get("techStacks", [])
    )

    # 핵심 내용이 없으면 스킵
    if not (resp or qual):
        return ""

    lines = [f"## 공고 {idx}: {company} — {title}", ""]

    if tech:
        lines += ["### 기술 스택", "", tech, ""]
    if resp:
        lines += ["### 주요 업무", "", resp, ""]
    if qual:
        lines += ["### 자격 요건", "", qual, ""]
    if preferred:
        lines += ["### 우대 사항", "", preferred, ""]
    if welfare:
        lines += ["### 복리후생", "", welfare, ""]

    return "\n".join(lines)


# ── 메인 ──────────────────────────────────────────────────────────
def main():
    print("=" * 52)
    print("  점핏(Jumpit) 신입 채용공고 크롤러")
    print("=" * 52)

    # 1. 목록 수집
    all_jobs = []
    for page in range(1, MAX_PAGES + 1):
        jobs = get_position_ids(page)
        all_jobs.extend(jobs)
        time.sleep(DELAY)

    print(f"\n총 {len(all_jobs)}개 공고 상세 수집 시작...\n")

    # 2. 상세 수집 + md 변환
    md_blocks = []
    for i, job in enumerate(all_jobs, 1):
        print(f"  [{i:3}/{len(all_jobs)}] {job['company'][:20]:20} {job['title'][:30]}")
        detail = get_position_detail(job["id"])
        if detail:
            block = to_md_block(len(md_blocks) + 1, detail)
            if block:
                md_blocks.append(block)
                print(f"         ✓ 저장 (누적 {len(md_blocks)}개)")
            else:
                print(f"         - 내용 없음 (스킵)")
        time.sleep(random.uniform(DELAY, DELAY + 0.5))

    # 3. 파일 저장
    if md_blocks:
        content = "\n\n---\n\n".join(md_blocks)
        OUTPUT_FILE.write_text(content, encoding="utf-8")
        print(f"\n✅ 완료: {len(md_blocks)}개 공고 → {OUTPUT_FILE.name}")
    else:
        print("\n❌ 수집 실패")


if __name__ == "__main__":
    main()
