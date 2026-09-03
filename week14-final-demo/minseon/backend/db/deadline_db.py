"""
deadline_db.py — 청년정책 신청 마감일 전용 SQLite DB

벡터 DB는 의미 검색에 특화되어 있어 날짜 정렬·범위 조회에 부적합합니다.
이 모듈은 마감일 정보만 별도 관계형 DB로 관리합니다.

스키마:
  policy_deadlines
    id           TEXT PK     -- 고유 식별자
    name         TEXT        -- 정책명
    category     TEXT        -- 카테고리
    region       TEXT        -- 지역 (전국 공통이면 '')
    start_date   TEXT        -- 신청 시작일 YYYY-MM-DD
    end_date     TEXT        -- 신청 마감일 YYYY-MM-DD (NULL이면 상시)
    benefit      TEXT        -- 지원 내용 요약
    url          TEXT        -- 공식 신청 링크
    phone        TEXT        -- 문의처
    always_open  INTEGER     -- 1=상시모집, 0=기간제
    updated_at   TEXT        -- 갱신 일시

조회 기준: end_date ASC (마감 임박 순), region 필터, 키워드 검색
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from backend.logging_config import get_logger

logger = get_logger(__name__)

_DB_DIR  = Path(__file__).parent.parent.parent / "database" / "data" / "deadlines"
_DB_PATH = _DB_DIR / "deadlines.db"


def _get_conn() -> sqlite3.Connection:
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """테이블 생성 (없으면)."""
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS policy_deadlines (
                id          TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                category    TEXT DEFAULT '',
                region      TEXT DEFAULT '',
                start_date  TEXT DEFAULT '',
                end_date    TEXT DEFAULT '',
                benefit     TEXT DEFAULT '',
                url         TEXT DEFAULT '',
                phone       TEXT DEFAULT '',
                always_open INTEGER DEFAULT 0,
                updated_at  TEXT DEFAULT ''
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_end_date ON policy_deadlines(end_date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_region   ON policy_deadlines(region)")
        conn.commit()


def upsert(record: dict) -> None:
    """레코드 삽입 또는 갱신."""
    record.setdefault("updated_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    with _get_conn() as conn:
        conn.execute("""
            INSERT INTO policy_deadlines
              (id, name, category, region, start_date, end_date, benefit, url, phone, always_open, updated_at)
            VALUES
              (:id, :name, :category, :region, :start_date, :end_date, :benefit, :url, :phone, :always_open, :updated_at)
            ON CONFLICT(id) DO UPDATE SET
              name        = excluded.name,
              category    = excluded.category,
              region      = excluded.region,
              start_date  = excluded.start_date,
              end_date    = excluded.end_date,
              benefit     = excluded.benefit,
              url         = excluded.url,
              phone       = excluded.phone,
              always_open = excluded.always_open,
              updated_at  = excluded.updated_at
        """, record)
        conn.commit()


def query_upcoming(
    region: str = "",
    days: int = 30,
    top_k: int = 10,
    include_always_open: bool = True,
) -> list[dict]:
    """
    마감 임박 정책 조회.
    - today ~ today+days 범위의 end_date 우선 (D-Day 순 정렬)
    - include_always_open=True 이면 상시모집도 포함
    """
    today     = datetime.now().strftime("%Y-%m-%d")
    deadline  = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    region_kw = f"%{region}%" if region else "%"

    with _get_conn() as conn:
        rows = conn.execute("""
            SELECT * FROM policy_deadlines
            WHERE (region = '' OR region LIKE :region OR :region = '%')
              AND (
                    (always_open = 0 AND end_date >= :today AND end_date <= :deadline)
                    OR (always_open = 1 AND :include_always = 1)
              )
            ORDER BY
              always_open ASC,          -- 기간제 먼저
              CASE WHEN end_date = '' THEN '9999-12-31' ELSE end_date END ASC
            LIMIT :top_k
        """, {
            "region":         region_kw,
            "today":          today,
            "deadline":       deadline,
            "include_always": 1 if include_always_open else 0,
            "top_k":          top_k,
        }).fetchall()

    return [dict(r) for r in rows]


def query_by_keyword(keyword: str, top_k: int = 10) -> list[dict]:
    """정책명·지원내용에서 키워드 검색."""
    kw = f"%{keyword}%"
    with _get_conn() as conn:
        rows = conn.execute("""
            SELECT * FROM policy_deadlines
            WHERE name LIKE :kw OR benefit LIKE :kw OR category LIKE :kw
            ORDER BY
              always_open ASC,
              CASE WHEN end_date = '' THEN '9999-12-31' ELSE end_date END ASC
            LIMIT :top_k
        """, {"kw": kw, "top_k": top_k}).fetchall()
    return [dict(r) for r in rows]


def to_doc(row: dict) -> dict:
    """DB 레코드 → 챗봇 document 형식 변환."""
    today    = datetime.now().strftime("%Y-%m-%d")
    end_date = row.get("end_date", "")

    if row.get("always_open"):
        dday_str = "상시모집"
    elif end_date:
        try:
            delta = (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(today, "%Y-%m-%d")).days
            dday_str = f"D-{delta}" if delta >= 0 else "마감"
        except Exception:
            dday_str = end_date
    else:
        dday_str = "기간 미정"

    content = f"""## {row['name']}

- **카테고리**: {row.get('category', '')}
- **지역**: {row.get('region') or '전국'}
- **신청 기간**: {row.get('start_date', '') or '미정'} ~ {end_date or ('상시' if row.get('always_open') else '미정')}
- **마감**: {dday_str}
- **지원 내용**: {row.get('benefit', '')}
- **문의**: {row.get('phone', '') or '-'}
- **신청 링크**: {row.get('url', '') or '공식 사이트 참조'}
"""
    return {
        "id":       row.get("id", ""),
        "title":    f"[{dday_str}] {row['name']}",
        "content":  content,
        "category": row.get("category", ""),
        "source":   "마감일DB",
        "url":      row.get("url", ""),
        "end_date": end_date,
        "dday":     dday_str,
    }


def seed_sample_data() -> None:
    """주요 청년정책 마감 정보 초기 데이터 삽입 (없는 경우에만)."""
    init_db()
    with _get_conn() as conn:
        count = conn.execute("SELECT COUNT(*) FROM policy_deadlines").fetchone()[0]
    if count > 0:
        return  # 이미 데이터 있으면 스킵

    samples = [
        {
            "id":          "youth_leap_account",
            "name":        "청년도약계좌",
            "category":    "금융",
            "region":      "",
            "start_date":  "2025-01-01",
            "end_date":    "",
            "benefit":     "월 70만원 납입 시 정부기여금 최대 6% + 비과세 혜택, 5년 만기",
            "url":         "https://www.kinfa.or.kr",
            "phone":       "1397",
            "always_open": 1,
        },
        {
            "id":          "youth_monthly_rent",
            "name":        "청년 월세 한시 특별지원",
            "category":    "주거",
            "region":      "",
            "start_date":  "2025-03-01",
            "end_date":    "2025-12-31",
            "benefit":     "월 최대 20만원, 최대 12개월 지원",
            "url":         "https://www.myhome.go.kr",
            "phone":       "1600-0777",
            "always_open": 0,
        },
        {
            "id":          "youth_employment_subsidy",
            "name":        "청년일자리도약장려금",
            "category":    "일자리",
            "region":      "",
            "start_date":  "2025-01-01",
            "end_date":    "2025-12-31",
            "benefit":     "중소기업 취업 청년에게 최대 960만원(기업 지원금)",
            "url":         "https://www.work.go.kr",
            "phone":       "1350",
            "always_open": 0,
        },
        {
            "id":          "national_scholarship_1",
            "name":        "국가장학금 1유형",
            "category":    "교육",
            "region":      "",
            "start_date":  "2025-11-01",
            "end_date":    "2026-01-15",
            "benefit":     "소득분위별 최대 연 570만원 (1~3구간 기준)",
            "url":         "https://www.kosaf.go.kr",
            "phone":       "1599-2000",
            "always_open": 0,
        },
        {
            "id":          "youth_inner_company",
            "name":        "청년내일채움공제",
            "category":    "일자리",
            "region":      "",
            "start_date":  "2025-01-01",
            "end_date":    "2025-12-31",
            "benefit":     "2년 근속 시 청년 400만원+기업 400만원+정부 600만원=1,200만원 적립",
            "url":         "https://www.work.go.kr",
            "phone":       "1350",
            "always_open": 0,
        },
        {
            "id":          "youth_housing_dream",
            "name":        "청년주택드림청약통장",
            "category":    "주거",
            "region":      "",
            "start_date":  "2024-02-21",
            "end_date":    "",
            "benefit":     "연 4.5% 금리, 분양가 80% 저금리 대출 연계",
            "url":         "https://www.nhuf.molit.go.kr",
            "phone":       "1600-0700",
            "always_open": 1,
        },
        {
            "id":          "startup_support",
            "name":        "청년창업사관학교",
            "category":    "창업",
            "region":      "",
            "start_date":  "2025-01-06",
            "end_date":    "2025-02-28",
            "benefit":     "창업 공간·멘토링·사업화 자금 최대 1억원",
            "url":         "https://start.go.kr",
            "phone":       "1600-7119",
            "always_open": 0,
        },
        {
            "id":          "youth_mental_health",
            "name":        "청년 마음건강 바우처",
            "category":    "마음건강",
            "region":      "",
            "start_date":  "2025-01-01",
            "end_date":    "",
            "benefit":     "심리상담 서비스 월 4회, 회당 5만원 지원",
            "url":         "https://www.bokjiro.go.kr",
            "phone":       "129",
            "always_open": 1,
        },
        {
            "id":          "youth_future_savings",
            "name":        "청년미래적금",
            "category":    "금융",
            "region":      "",
            "start_date":  "2025-01-01",
            "end_date":    "2025-12-31",
            "benefit":     "시중 금리 + 정부 우대금리, 은행별 상이 (신한·국민·하나·우리·농협 등 참여)",
            "url":         "https://www.kinfa.or.kr",
            "phone":       "1397",
            "always_open": 0,
        },
        {
            "id":          "lh_youth_rental",
            "name":        "LH 청년 매입임대주택",
            "category":    "주거",
            "region":      "",
            "start_date":  "",
            "end_date":    "",
            "benefit":     "시세 40~50% 수준 임대료, 최대 6년 거주",
            "url":         "https://apply.lh.or.kr",
            "phone":       "1600-1004",
            "always_open": 1,
        },
    ]

    for s in samples:
        upsert(s)
    logger.info(f"[deadline_db] 샘플 데이터 {len(samples)}건 삽입 완료")
