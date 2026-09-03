"""
auth.py — Supabase JWT 검증 (BACKEND 계층)

/api/profiles, /api/subscriptions, /api/applications, /api/sessions 등
사용자 개인 데이터를 다루는 엔드포인트에서 요청자가 실제로 그 계정의 소유자인지
확인하는 데 사용합니다.
"""

from dataclasses import dataclass

from fastapi import Header, HTTPException

from frontend.session_manager import _get_client


@dataclass(frozen=True)
class AuthedUser:
    email:   str
    user_id: str
    token:   str  # sessions 테이블 RLS(auth.uid())를 통과시키기 위해 요청별로 필요


def get_current_user(authorization: str | None = Header(None)) -> AuthedUser:
    """Authorization: Bearer <access_token> 헤더를 검증하고 로그인 사용자 정보를 반환."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="인증 토큰이 필요합니다.")

    token = authorization.removeprefix("Bearer ").strip()
    try:
        res = _get_client().auth.get_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail="유효하지 않거나 만료된 토큰입니다.")

    if not res or not res.user or not res.user.email:
        raise HTTPException(status_code=401, detail="유효하지 않거나 만료된 토큰입니다.")

    return AuthedUser(email=res.user.email, user_id=res.user.id, token=token)


def get_current_user_email(authorization: str | None = Header(None)) -> str:
    """이메일만 필요한 기존 엔드포인트용 (profiles/subscriptions/applications)."""
    return get_current_user(authorization).email


def require_self(current_email: str, target_email: str) -> None:
    """토큰의 이메일과 요청 대상 이메일이 일치하는지 확인 (본인 데이터만 접근 허용)."""
    if current_email.lower() != (target_email or "").lower():
        raise HTTPException(status_code=403, detail="본인 계정의 데이터만 조회/수정할 수 있습니다.")
