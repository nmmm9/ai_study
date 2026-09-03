"""
logging_config.py — 구조화된 로깅 설정

print() 대신 `logger = get_logger(__name__)` 후 logger.info/warning/error를 사용하세요.
레벨별 필터링, 나중에 파일/외부 로깅 서비스(예: LangSmith)로의 전환이 쉬워집니다.
"""

import logging
import sys

_CONFIGURED = False


def _configure() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    # Windows 콘솔은 기본 코드페이지(cp949)를 쓰는 경우가 많아, em dash 등
    # cp949로 표현 안 되는 문자가 로그에 섞이면 StreamHandler가 조용히 실패한다.
    # stdout을 UTF-8로 재설정하고, 그래도 안 되면 대체 문자로 치환해 절대 죽지 않게 한다.
    stream = sys.stdout
    if hasattr(stream, "reconfigure"):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    _configure()
    return logging.getLogger(name)
