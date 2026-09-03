"""
behavior_db.py — 사용자 행동 로그 & 협업 필터링 (Feature 7)

테이블:
  policy_views : 정책 조회/검색 이벤트 기록
"""

import sqlite3
import json
from collections import defaultdict
from pathlib import Path
from datetime import datetime

_DB_DIR  = Path(__file__).parent.parent.parent / "database" / "data" / "behavior"
_DB_PATH = _DB_DIR / "behavior.db"


def _conn() -> sqlite3.Connection:
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(_DB_PATH))
    c.row_factory = sqlite3.Row
    return c


def init_db() -> None:
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS policy_views (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  TEXT NOT NULL,
                policy_name TEXT NOT NULL,
                category    TEXT DEFAULT '',
                query       TEXT DEFAULT '',
                viewed_at   TEXT DEFAULT ''
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_session ON policy_views(session_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_policy  ON policy_views(policy_name)")
        c.commit()


def log_view(session_id: str, policy_name: str, category: str = "", query: str = "") -> None:
    """정책 조회 이벤트 기록."""
    init_db()
    with _conn() as c:
        c.execute(
            "INSERT INTO policy_views(session_id,policy_name,category,query,viewed_at) VALUES(?,?,?,?,?)",
            (session_id, policy_name, category, query, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        c.commit()


def log_search_results(session_id: str, docs: list[dict], query: str = "") -> None:
    """검색 결과 문서들을 한 번에 기록."""
    for d in docs:
        log_view(
            session_id=session_id,
            policy_name=d.get("title", "")[:100],
            category=d.get("category", ""),
            query=query,
        )


def get_collab_recommendations(session_id: str, top_k: int = 5) -> list[str]:
    """
    협업 필터링: 이 세션이 본 정책들을 같이 본 다른 세션이
    추가로 본 정책들을 추천합니다 (item-item 방식).
    """
    init_db()
    with _conn() as c:
        # 현재 세션이 본 정책들
        my_rows = c.execute(
            "SELECT DISTINCT policy_name FROM policy_views WHERE session_id=?",
            (session_id,)
        ).fetchall()
        my_policies = {r["policy_name"] for r in my_rows}

        if not my_policies:
            # 신규 사용자: 전체에서 가장 많이 본 인기 정책 추천
            pop_rows = c.execute("""
                SELECT policy_name, COUNT(*) as cnt
                FROM policy_views
                GROUP BY policy_name
                ORDER BY cnt DESC
                LIMIT ?
            """, (top_k,)).fetchall()
            return [r["policy_name"] for r in pop_rows]

        # 내가 본 정책을 함께 본 세션들
        placeholders = ",".join("?" * len(my_policies))
        similar_rows = c.execute(f"""
            SELECT DISTINCT session_id FROM policy_views
            WHERE policy_name IN ({placeholders}) AND session_id != ?
        """, (*my_policies, session_id)).fetchall()
        similar_sessions = [r["session_id"] for r in similar_rows]

        if not similar_sessions:
            return []

        # 유사 세션들이 본 정책 중 내가 안 본 것
        s_placeholders = ",".join("?" * len(similar_sessions))
        p_placeholders = ",".join("?" * len(my_policies))
        recommend_rows = c.execute(f"""
            SELECT policy_name, COUNT(*) as score
            FROM policy_views
            WHERE session_id IN ({s_placeholders})
              AND policy_name NOT IN ({p_placeholders})
            GROUP BY policy_name
            ORDER BY score DESC
            LIMIT ?
        """, (*similar_sessions, *my_policies, top_k)).fetchall()

        return [r["policy_name"] for r in recommend_rows]


def get_popular_by_category(category: str = "", top_k: int = 5) -> list[str]:
    """카테고리별 인기 정책."""
    init_db()
    with _conn() as c:
        if category:
            rows = c.execute("""
                SELECT policy_name, COUNT(*) as cnt
                FROM policy_views WHERE category=?
                GROUP BY policy_name ORDER BY cnt DESC LIMIT ?
            """, (category, top_k)).fetchall()
        else:
            rows = c.execute("""
                SELECT policy_name, COUNT(*) as cnt
                FROM policy_views
                GROUP BY policy_name ORDER BY cnt DESC LIMIT ?
            """, (top_k,)).fetchall()
    return [r["policy_name"] for r in rows]
