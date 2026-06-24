"""
session_manager.py — 멀티세션 관리 (Supabase 연동)

Supabase sessions 테이블에 대화 세션을 저장합니다.
user_id는 로그인한 사용자의 auth.uid()와 연결됩니다.
"""

import os
import uuid
from datetime import datetime

from supabase import create_client, Client

_client: Client | None = None


def _get_client() -> Client:
    global _client
    if _client is None:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_KEY", "")
        if not url or not key:
            raise ValueError(".env에 SUPABASE_URL과 SUPABASE_KEY를 설정해주세요.")
        _client = create_client(url, key)
    return _client


def set_auth_token(access_token: str) -> None:
    """로그인 후 받은 JWT 토큰을 클라이언트에 설정 (RLS 적용)"""
    _get_client().auth.set_session(access_token, "")


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


# ── 세션 CRUD ────────────────────────────────────────────────────

def new_session(name: str = "") -> str:
    sid  = str(uuid.uuid4())[:8]
    name = name or f"대화 {datetime.now().strftime('%m/%d %H:%M')}"
    _get_client().table("sessions").insert({
        "id":         sid,
        "name":       name,
        "messages":   [],
        "traces":     [],
        "created_at": datetime.now().isoformat(),
    }).execute()
    return sid


def get_all() -> dict:
    res = _get_client().table("sessions").select("*").order("created_at", desc=True).execute()
    return {row["id"]: row for row in (res.data or [])}


def save_session(sid: str, messages: list, traces: list) -> None:
    _get_client().table("sessions").update({
        "messages": messages,
        "traces":   traces,
    }).eq("id", sid).execute()


def rename_session(sid: str, name: str) -> None:
    _get_client().table("sessions").update({"name": name}).eq("id", sid).execute()


def delete_session(sid: str) -> None:
    _get_client().table("sessions").delete().eq("id", sid).execute()
