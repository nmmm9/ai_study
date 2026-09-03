"""
session_manager.py — 멀티세션 관리 (Supabase 연동)

Supabase sessions 테이블에 대화 세션을 저장합니다.
user_id는 로그인한 사용자의 auth.uid()와 연결됩니다.
"""

import uuid
from datetime import datetime

from supabase import create_client, Client

from backend.config import settings

_client: Client | None = None


def _get_client() -> Client:
    global _client
    if _client is None:
        if not settings.supabase_url or not settings.supabase_key:
            raise ValueError(".env에 SUPABASE_URL과 SUPABASE_KEY를 설정해주세요.")
        _client = create_client(settings.supabase_url, settings.supabase_key)
    return _client


def set_auth_token(access_token: str) -> None:
    """로그인 후 받은 JWT 토큰을 클라이언트에 설정 (RLS 적용)"""
    _get_client().auth.set_session(access_token, "")


def _client_for_token(access_token: str) -> Client:
    """
    요청 1건 전용 Supabase 클라이언트를 새로 만들어 postgrest에 사용자 JWT를 실어줍니다.

    _get_client()의 전역 싱글턴에 postgrest.auth()를 직접 호출하면, FastAPI가
    동시에 여러 사용자의 요청을 처리할 때 한 사용자의 토큰이 다른 사용자 요청에
    섞여 들어갈 수 있습니다(공유 상태 오염). sessions 테이블처럼 RLS로
    auth.uid() = user_id를 검사하는 테이블은 요청마다 독립된 클라이언트를 써야 합니다.
    """
    client = create_client(settings.supabase_url, settings.supabase_key)
    client.postgrest.auth(access_token)
    return client


# ── 회원가입 / 로그인 ────────────────────────────────────────────

def sign_up(email: str, password: str) -> dict:
    """회원가입. 성공 시 user 정보 반환"""
    res = _get_client().auth.sign_up({"email": email, "password": password})
    return {"user": res.user, "session": res.session}


def sign_in(email: str, password: str) -> dict:
    """로그인. 성공 시 user + access_token 반환"""
    res = _get_client().auth.sign_in_with_password({"email": email, "password": password})
    if res.session:
        # RLS를 위해 토큰 설정
        _get_client().postgrest.auth(res.session.access_token)
    return {"user": res.user, "session": res.session}


def sign_out() -> None:
    _get_client().auth.sign_out()


# ── 세션 CRUD (로그인 사용자 전용 — access_token으로 RLS 통과) ──────

def new_session(user_id: str, access_token: str, name: str = "") -> str:
    sid  = str(uuid.uuid4())[:8]
    name = name or f"대화 {datetime.now().strftime('%m/%d %H:%M')}"
    _client_for_token(access_token).table("sessions").insert({
        "id":         sid,
        "user_id":    user_id,
        "name":       name,
        "messages":   [],
        "traces":     [],
        "created_at": datetime.now().isoformat(),
    }).execute()
    return sid


def get_all(access_token: str) -> dict:
    """RLS가 auth.uid() = user_id인 행만 자동으로 걸러줍니다."""
    res = (
        _client_for_token(access_token)
        .table("sessions").select("*").order("created_at", desc=True).execute()
    )
    return {row["id"]: row for row in (res.data or [])}


def save_session(access_token: str, sid: str, messages: list, traces: list) -> None:
    _client_for_token(access_token).table("sessions").update({
        "messages": messages,
        "traces":   traces,
    }).eq("id", sid).execute()


def rename_session(access_token: str, sid: str, name: str) -> None:
    _client_for_token(access_token).table("sessions").update({"name": name}).eq("id", sid).execute()


def delete_session(access_token: str, sid: str) -> None:
    _client_for_token(access_token).table("sessions").delete().eq("id", sid).execute()
