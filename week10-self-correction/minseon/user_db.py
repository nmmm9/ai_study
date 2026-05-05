"""
user_db.py
──────────
SQLite 기반 사용자 관리

테이블:
  users             — 사용자 (이름, 이메일, 나이, 지역, 이메일수신허용)
  notification_log  — 발송 이력
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "users.db"


def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db() -> None:
    with _conn() as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT    NOT NULL,
                email           TEXT    NOT NULL UNIQUE,
                age             INTEGER NOT NULL,
                region          TEXT    NOT NULL,
                email_allowed   INTEGER NOT NULL DEFAULT 1,
                notify_interval TEXT    NOT NULL DEFAULT 'weekly',
                last_notified   TEXT,
                created_at      TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS notification_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                email      TEXT NOT NULL,
                policies   TEXT,
                sent_at    TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            );
        """)
        # 기존 DB 마이그레이션 (email_allowed 컬럼 없으면 추가)
        try:
            con.execute("ALTER TABLE users ADD COLUMN email_allowed INTEGER NOT NULL DEFAULT 1")
        except Exception:
            pass
        # 구버전 subscriptions 테이블 호환
        try:
            con.execute("ALTER TABLE subscriptions RENAME TO users")
        except Exception:
            pass


# ── CRUD ─────────────────────────────────────────────────────────

def register_user(
    name: str,
    email: str,
    age: int,
    region: str,
    email_allowed: bool = True,
    interval: str = "weekly",
) -> None:
    """신규 등록 또는 기존 정보 업데이트."""
    init_db()
    with _conn() as con:
        con.execute(
            """
            INSERT INTO users (name, email, age, region, email_allowed, notify_interval)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(email) DO UPDATE SET
                name=excluded.name,
                age=excluded.age,
                region=excluded.region,
                email_allowed=excluded.email_allowed,
                notify_interval=excluded.notify_interval
            """,
            (name, email, age, region, int(email_allowed), interval),
        )


def get_user(email: str) -> dict | None:
    """이메일로 사용자 조회."""
    init_db()
    with _conn() as con:
        row = con.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    return dict(row) if row else None


def update_email_allowed(email: str, allowed: bool) -> None:
    """이메일 수신 허용/거부 변경."""
    with _conn() as con:
        con.execute(
            "UPDATE users SET email_allowed=? WHERE email=?",
            (int(allowed), email),
        )


def update_user(email: str, name: str, age: int, region: str) -> None:
    """사용자 기본 정보 수정."""
    with _conn() as con:
        con.execute(
            "UPDATE users SET name=?, age=?, region=? WHERE email=?",
            (name, age, region, email),
        )


def get_all_users() -> list[dict]:
    init_db()
    with _conn() as con:
        rows = con.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


def get_email_allowed_users() -> list[dict]:
    """이메일 수신을 허용한 사용자만 조회."""
    init_db()
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM users WHERE email_allowed=1"
        ).fetchall()
    return [dict(r) for r in rows]


def mark_notified(email: str) -> None:
    with _conn() as con:
        con.execute(
            "UPDATE users SET last_notified=? WHERE email=?",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), email),
        )


def log_notification(email: str, policy_titles: list[str]) -> None:
    with _conn() as con:
        con.execute(
            "INSERT INTO notification_log (email, policies) VALUES (?, ?)",
            (email, json.dumps(policy_titles, ensure_ascii=False)),
        )


def get_notification_log(email: str, limit: int = 5) -> list[dict]:
    init_db()
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM notification_log WHERE email=? ORDER BY sent_at DESC LIMIT ?",
            (email, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def delete_user(email: str) -> None:
    with _conn() as con:
        con.execute("DELETE FROM users WHERE email=?", (email,))


def should_notify(user: dict) -> bool:
    """마지막 알림 시각 기준으로 발송 여부 결정."""
    from datetime import timedelta
    if not user.get("email_allowed"):
        return False
    last_raw = user.get("last_notified")
    if not last_raw:
        return True
    try:
        last_dt = datetime.fromisoformat(last_raw)
    except ValueError:
        return True
    delta = timedelta(weeks=1) if user.get("notify_interval") == "weekly" else timedelta(days=1)
    return (datetime.now() - last_dt) >= delta
