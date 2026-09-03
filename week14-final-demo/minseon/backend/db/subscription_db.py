"""
subscription_db.py — 키워드 구독 & D-Day 알림 DB (Feature 1, 3)

테이블:
  keyword_subscriptions  : 사용자 키워드 구독
  user_applications      : 정책 지원 현황 트래킹
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

_DB_DIR  = Path(__file__).parent.parent.parent / "database" / "data" / "subscriptions"
_DB_PATH = _DB_DIR / "subscriptions.db"


def _conn() -> sqlite3.Connection:
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(_DB_PATH))
    c.row_factory = sqlite3.Row
    return c


def init_db() -> None:
    with _conn() as c:
        # 키워드 구독
        c.execute("""
            CREATE TABLE IF NOT EXISTS keyword_subscriptions (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                keyword    TEXT NOT NULL,
                created_at TEXT DEFAULT '',
                UNIQUE(user_email, keyword)
            )
        """)
        # 지원 현황 트래킹
        c.execute("""
            CREATE TABLE IF NOT EXISTS user_applications (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email  TEXT NOT NULL,
                policy_name TEXT NOT NULL,
                policy_id   TEXT DEFAULT '',
                status      TEXT DEFAULT 'scrapped',
                deadline    TEXT DEFAULT '',
                applied_at  TEXT DEFAULT '',
                memo        TEXT DEFAULT '',
                updated_at  TEXT DEFAULT ''
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_sub_email ON keyword_subscriptions(user_email)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_app_email ON user_applications(user_email)")
        c.commit()


# ── 키워드 구독 ──────────────────────────────────────────────────────

def add_subscription(email: str, keyword: str) -> bool:
    init_db()
    try:
        with _conn() as c:
            c.execute(
                "INSERT OR IGNORE INTO keyword_subscriptions(user_email, keyword, created_at) VALUES(?,?,?)",
                (email, keyword, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            c.commit()
        return True
    except Exception:
        return False


def remove_subscription(email: str, keyword: str) -> bool:
    init_db()
    with _conn() as c:
        c.execute("DELETE FROM keyword_subscriptions WHERE user_email=? AND keyword=?", (email, keyword))
        c.commit()
    return True


def get_subscriptions(email: str) -> list[str]:
    init_db()
    with _conn() as c:
        rows = c.execute("SELECT keyword FROM keyword_subscriptions WHERE user_email=?", (email,)).fetchall()
    return [r["keyword"] for r in rows]


def get_all_subscriptions() -> list[dict]:
    """스케줄러용: 전체 구독 목록."""
    init_db()
    with _conn() as c:
        rows = c.execute("SELECT user_email, keyword FROM keyword_subscriptions").fetchall()
    return [dict(r) for r in rows]


def match_subscriptions(doc_text: str) -> list[str]:
    """정책 텍스트와 매칭되는 구독 이메일 반환."""
    init_db()
    with _conn() as c:
        rows = c.execute("SELECT user_email, keyword FROM keyword_subscriptions").fetchall()
    matched = set()
    text_lower = doc_text.lower()
    for r in rows:
        if r["keyword"].lower() in text_lower:
            matched.add(r["user_email"])
    return list(matched)


# ── 지원 현황 트래킹 ─────────────────────────────────────────────────

_STATUS_LABELS = {
    "scrapped":  "스크랩",
    "preparing": "서류 준비 중",
    "applied":   "제출 완료",
    "waiting":   "결과 대기",
    "passed":    "합격",
    "failed":    "불합격",
}


def add_application(email: str, policy_name: str, policy_id: str = "", deadline: str = "") -> int:
    init_db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO user_applications(user_email,policy_name,policy_id,status,deadline,applied_at,updated_at) VALUES(?,?,?,?,?,?,?)",
            (email, policy_name, policy_id, "scrapped", deadline, now, now)
        )
        c.commit()
        return cur.lastrowid


def update_status(app_id: int, status: str, memo: str = "") -> bool:
    init_db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _conn() as c:
        c.execute(
            "UPDATE user_applications SET status=?, memo=?, updated_at=? WHERE id=?",
            (status, memo, now, app_id)
        )
        c.commit()
    return True


def get_application_owner(app_id: int) -> str | None:
    """app_id로 해당 지원 현황 레코드의 소유자 이메일을 조회 (권한 확인용)."""
    init_db()
    with _conn() as c:
        row = c.execute("SELECT user_email FROM user_applications WHERE id=?", (app_id,)).fetchone()
    return row["user_email"] if row else None


def get_applications(email: str) -> list[dict]:
    init_db()
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM user_applications WHERE user_email=? ORDER BY updated_at DESC",
            (email,)
        ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["status_label"] = _STATUS_LABELS.get(d["status"], d["status"])
        d["dday"] = _calc_dday(d.get("deadline", ""))
        result.append(d)
    return result


def get_upcoming_deadlines_for_email() -> list[dict]:
    """스케줄러용: D-3, D-1 마감 임박 항목 조회."""
    init_db()
    today    = datetime.now().strftime("%Y-%m-%d")
    d3_date  = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
    d1_date  = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    with _conn() as c:
        rows = c.execute("""
            SELECT * FROM user_applications
            WHERE deadline IN (?, ?)
              AND status NOT IN ('passed', 'failed')
            ORDER BY deadline ASC
        """, (d3_date, d1_date)).fetchall()
    return [dict(r) for r in rows]


def _calc_dday(deadline: str) -> str:
    if not deadline:
        return ""
    try:
        delta = (datetime.strptime(deadline, "%Y-%m-%d") - datetime.now()).days
        if delta < 0:
            return "마감"
        if delta == 0:
            return "D-Day"
        return f"D-{delta}"
    except Exception:
        return ""
