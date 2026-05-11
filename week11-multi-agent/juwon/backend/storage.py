"""
storage.py - 분석 결과 히스토리 저장/불러오기
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
        del history[sorted(history.keys())[0]]
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
    return history[sorted(history.keys())[-1]]


def load_previous_history() -> dict | None:
    """최신 직전 기록 반환 (비교용)"""
    history = load_all_history()
    keys = sorted(history.keys())
    if len(keys) < 2:
        return None
    return history[keys[-2]]
