"""
config.py — 환경변수 중앙 관리

.env 로딩은 이 모듈에서 한 번만 수행합니다.
다른 모듈은 각자 load_dotenv()/os.environ.get()을 호출하지 말고
`from backend.config import settings` 후 settings.xxx를 사용하세요.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


@dataclass(frozen=True)
class Settings:
    openai_api_key:       str
    supabase_url:         str
    supabase_key:         str
    supabase_service_key: str
    tavily_api_key:       str
    public_data_api_key:  str
    lh_supply_api_key:    str
    hug_jeonse_api_key:   str
    hug_lease_api_key:    str
    bokjoro_api_key:      str
    smtp_user:             str
    smtp_password:         str


def _load() -> Settings:
    return Settings(
        openai_api_key       = os.environ.get("OPENAI_API_KEY", ""),
        supabase_url         = os.environ.get("SUPABASE_URL", ""),
        supabase_key         = os.environ.get("SUPABASE_KEY", ""),
        supabase_service_key = os.environ.get("SUPABASE_SERVICE_KEY", "") or os.environ.get("SUPABASE_KEY", ""),
        tavily_api_key       = os.environ.get("TAVILY_API_KEY", "").strip(),
        public_data_api_key  = os.environ.get("PUBLIC_DATA_API_KEY", "").strip(),
        lh_supply_api_key    = os.environ.get("LH_SUPPLY_API_KEY", "").strip(),
        hug_jeonse_api_key   = os.environ.get("HUG_JEONSE_API_KEY", "").strip(),
        hug_lease_api_key    = os.environ.get("HUG_LEASE_API_KEY", "").strip(),
        bokjoro_api_key      = os.environ.get("BOKJORO_API_KEY", "").strip(),
        smtp_user             = os.environ.get("SMTP_USER", "") or os.environ.get("GMAIL_USER", ""),
        smtp_password         = os.environ.get("SMTP_PASSWORD", "") or os.environ.get("GMAIL_PASS", ""),
    )


settings = _load()
