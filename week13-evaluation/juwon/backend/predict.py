"""
predict.py - 누적 히스토리 기반 미래 트렌드 예측 (Week 13)
history.json에 쌓인 일별 분석 데이터를 시계열로 분석하여 GPT가 미래 트렌드 예측
"""
import json
import os
from collections import Counter, defaultdict
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI

from storage import load_all_history

load_dotenv()
_llm = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))


def _build_timeseries(records: list[dict]) -> dict:
    """히스토리 레코드를 날짜순 시계열로 변환"""
    sorted_records = sorted(records, key=lambda r: r.get("created_at", ""))

    lang_by_date: dict[str, dict] = {}
    repo_names_by_date: dict[str, list] = {}
    conclusions_by_date: dict[str, str] = {}

    for r in sorted_records:
        date = r.get("created_at", "")[:10]
        if not date:
            continue
        lang_by_date[date] = r.get("language_stats", {})
        repo_names_by_date[date] = [repo["name"] for repo in r.get("repos", [])[:10]]
        conclusions_by_date[date] = r.get("judge_decision", "")[:300]

    return {
        "lang_by_date": lang_by_date,
        "repo_names_by_date": repo_names_by_date,
        "conclusions_by_date": conclusions_by_date,
        "dates": sorted(lang_by_date.keys()),
    }


def _calc_lang_trend(lang_by_date: dict[str, dict]) -> dict:
    """언어별 등장 빈도 및 상승/하락 추이 계산"""
    dates = sorted(lang_by_date.keys())
    if not dates:
        return {}

    # 전체 언어 등장 횟수
    total_counts: Counter = Counter()
    for stats in lang_by_date.values():
        for lang, cnt in stats.items():
            total_counts[lang] += cnt

    # 최근 절반 vs 이전 절반 비교 (상승세 파악)
    half = max(1, len(dates) // 2)
    early_dates = dates[:half]
    recent_dates = dates[half:]

    early_counts: Counter = Counter()
    recent_counts: Counter = Counter()
    for d in early_dates:
        for lang, cnt in lang_by_date.get(d, {}).items():
            early_counts[lang] += cnt
    for d in recent_dates:
        for lang, cnt in lang_by_date.get(d, {}).items():
            recent_counts[lang] += cnt

    trend_score = {}
    all_langs = set(early_counts) | set(recent_counts)
    for lang in all_langs:
        e = early_counts.get(lang, 0)
        r = recent_counts.get(lang, 0)
        if e == 0:
            trend_score[lang] = r * 2  # 새로 등장한 언어
        else:
            trend_score[lang] = (r - e) / e  # 성장률

    return {
        "total_counts": dict(total_counts.most_common(15)),
        "trend_score":  dict(sorted(trend_score.items(), key=lambda x: x[1], reverse=True)[:10]),
    }


def _collect_rising_repos(records: list[dict]) -> list[str]:
    """최근 2회 이상 등장한 레포 (지속적 관심 신호)"""
    recent = sorted(records, key=lambda r: r.get("created_at", ""))[-7:]
    counter: Counter = Counter()
    for r in recent:
        for repo in r.get("repos", []):
            counter[repo["name"]] += 1
    return [name for name, cnt in counter.most_common(10) if cnt >= 2]


def run_prediction() -> dict:
    records = load_all_history()
    if len(records) < 2:
        return {
            "error": "예측에 필요한 데이터가 부족합니다. 최소 2일치 분석 기록이 필요합니다.",
            "record_count": len(records),
        }

    ts = _build_timeseries(records)
    lang_trend = _calc_lang_trend(ts["lang_by_date"])
    rising_repos = _collect_rising_repos(records)

    # GPT 예측용 요약 텍스트 작성
    history_summary = []
    for date in ts["dates"]:
        langs  = ts["lang_by_date"].get(date, {})
        repos  = ts["repo_names_by_date"].get(date, [])
        concl  = ts["conclusions_by_date"].get(date, "")
        top_langs = ", ".join(f"{l}({c})" for l, c in sorted(langs.items(), key=lambda x: -x[1])[:5])
        history_summary.append(f"[{date}] 언어: {top_langs} | 레포: {', '.join(repos[:5])} | 결론: {concl[:150]}")

    summary_text = "\n".join(history_summary[-14:])  # 최근 14일

    rising_text = ", ".join(rising_repos) if rising_repos else "없음"
    trend_text  = ", ".join(
        f"{l}({'+' if v > 0 else ''}{v:.1%})"
        for l, v in list(lang_trend.get("trend_score", {}).items())[:8]
    )

    prompt = f"""아래는 GitHub 트렌딩 저장소의 일별 분석 데이터입니다 (최근 {len(ts['dates'])}일).

=== 날짜별 트렌드 요약 ===
{summary_text}

=== 언어 상승세 분석 ===
상승률 높은 언어: {trend_text}

=== 지속적으로 관심받는 레포 (최근 여러 날 등장) ===
{rising_text}

위 데이터를 분석하여 앞으로 1~2주 내 GitHub 트렌딩을 예측해주세요.

반드시 아래 JSON 형식으로만 응답하세요 (다른 텍스트 없이):
{{
  "predicted_languages": [
    {{"language": "언어명", "confidence": 0~100 사이 숫자, "reason": "한 줄 이유"}},
    ...최대 6개
  ],
  "predicted_topics": ["주제1", "주제2", "주제3", "주제4", "주제5"],
  "predicted_repos": ["예상 레포/프로젝트 종류1", "예상 레포/프로젝트 종류2", "예상 레포/프로젝트 종류3"],
  "overall_prediction": "전체적인 트렌드 예측 (200자 내외 한국어)",
  "confidence_level": "높음|보통|낮음",
  "data_period": "{ts['dates'][0]} ~ {ts['dates'][-1]}",
  "analyzed_days": {len(ts['dates'])}
}}"""

    try:
        resp = _llm.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 GitHub 기술 트렌드 예측 전문가입니다. 반드시 유효한 JSON만 응답합니다."},
                {"role": "user",   "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        prediction = json.loads(resp.choices[0].message.content)
    except Exception as e:
        return {"error": f"GPT 예측 실패: {e}"}

    return {
        **prediction,
        "historical_lang_trend": lang_trend.get("trend_score", {}),
        "total_lang_counts":     lang_trend.get("total_counts", {}),
        "rising_repos":          rising_repos,
        "record_count":          len(records),
    }
