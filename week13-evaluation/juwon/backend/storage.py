"""
storage.py - JSON 기반 히스토리 저장소 + 벡터 검색 (Week 12/13)
history.json  : 분석 결과 + 임베딩
keywords.json : 키워드 구독 목록
"""
import json
import os
import uuid
from datetime import datetime

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

_DIR          = os.path.dirname(__file__)
HISTORY_FILE  = os.path.join(_DIR, "history.json")
KEYWORDS_FILE = os.path.join(_DIR, "keywords.json")

_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))


def _embed(text: str) -> list[float]:
    resp = _openai.embeddings.create(model="text-embedding-3-small", input=text[:8000])
    return resp.data[0].embedding


def _report_to_text(report: dict) -> str:
    top_repos = ", ".join(r["name"] for r in report.get("repos", [])[:10])
    return (
        f"언어: {report.get('language', '전체')} | 기간: {report.get('period', 'weekly')}\n"
        f"트렌딩 레포: {top_repos}\n"
        f"AI/ML: {report.get('analysis_ai', '')[:400]}\n"
        f"웹/앱: {report.get('analysis_web', '')[:400]}\n"
        f"보안: {report.get('analysis_sec', '')[:400]}\n"
        f"결론: {report.get('judge_decision', '')[:400]}"
    )


def _load(path: str) -> list:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save(path: str, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _strip(record: dict) -> dict:
    return {k: v for k, v in record.items() if k != "embedding"}


# ── 리포트 CRUD ──────────────────────────────────────────────

def save_history(data: dict) -> None:
    records = _load(HISTORY_FILE)
    try:
        embedding = _embed(_report_to_text(data))
    except Exception:
        embedding = []
    records.append({
        "id":               str(uuid.uuid4()),
        "created_at":       datetime.now().isoformat(),
        "language":         data.get("language", "전체"),
        "period":           data.get("period", "weekly"),
        "repos":            data.get("repos", []),
        "language_stats":   data.get("language_stats", {}),
        "top_topics":       data.get("top_topics", {}),
        "analysis_ai":      data.get("analysis_ai", ""),
        "analysis_web":     data.get("analysis_web", ""),
        "analysis_sec":     data.get("analysis_sec", ""),
        "supervisor_report": data.get("supervisor_report", ""),
        "critic_feedback":  data.get("critic_feedback", ""),
        "judge_decision":   data.get("judge_decision", ""),
        "debate_history":   data.get("debate_history", []),
        "embedding":        embedding,
    })
    _save(HISTORY_FILE, records)


def load_all_history() -> list[dict]:
    return [_strip(r) for r in reversed(_load(HISTORY_FILE))]


def load_latest_history() -> dict | None:
    records = _load(HISTORY_FILE)
    return _strip(records[-1]) if records else None


def search_reports(query: str, limit: int = 3) -> list[dict]:
    records = _load(HISTORY_FILE)
    if not records:
        return []
    try:
        q_vec = np.array(_embed(query))
    except Exception:
        return [_strip(r) for r in records[-limit:]]
    scored = []
    for r in records:
        emb = r.get("embedding")
        if not emb:
            continue
        v   = np.array(emb)
        sim = float(np.dot(q_vec, v) / (np.linalg.norm(q_vec) * np.linalg.norm(v) + 1e-9))
        scored.append((sim, r))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [_strip(r) for _, r in scored[:limit]]


def load_history_stats() -> list[dict]:
    return [
        {"date": r.get("created_at", "")[:10], "languages": r.get("language_stats", {})}
        for r in _load(HISTORY_FILE)
    ]


# ── 키워드 구독 ──────────────────────────────────────────────

def get_keywords() -> list[str]:
    return _load(KEYWORDS_FILE)


def add_keyword(keyword: str) -> bool:
    kws = get_keywords()
    if keyword in kws:
        return False
    kws.append(keyword)
    _save(KEYWORDS_FILE, kws)
    return True


def delete_keyword(keyword: str) -> None:
    _save(KEYWORDS_FILE, [k for k in get_keywords() if k != keyword])


def check_keyword_matches(repos: list[dict]) -> list[str]:
    keywords = get_keywords()
    if not keywords:
        return []
    matched = []
    for repo in repos:
        text = (
            repo.get("name", "") + " " +
            repo.get("description", "") + " " +
            " ".join(repo.get("topics", []))
        ).lower()
        for kw in keywords:
            if kw.lower() in text and kw not in matched:
                matched.append(kw)
    return matched
