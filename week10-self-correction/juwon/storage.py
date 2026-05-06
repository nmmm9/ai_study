"""
storage.py - 분석 결과 히스토리 저장/불러오기

JSON 파일로 날짜별 분석 결과를 관리
최근 30개 기록 유지
"""

import json
import os
from datetime import datetime

STORAGE_FILE = os.path.join(os.path.dirname(__file__), "history.json")


def save_history(data: dict) -> None:
    history = load_all_history()
    key = datetime.now().strftime("%Y-%m-%d %H:%M")
    history[key] = data

    if len(history) > 30:
        oldest = sorted(history.keys())[0]
        del history[oldest]

    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def load_all_history() -> dict:
    if not os.path.exists(STORAGE_FILE):
        return {}
    with open(STORAGE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_latest_history() -> dict | None:
    history = load_all_history()
    if not history:
        return None
    latest_key = sorted(history.keys())[-1]
    return history[latest_key]


def load_previous_history() -> dict | None:
    history = load_all_history()
    today = datetime.now().strftime("%Y-%m-%d")
    past_keys = sorted([k for k in history.keys() if not k.startswith(today)])
    if not past_keys:
        return None
    return history[past_keys[-1]]
