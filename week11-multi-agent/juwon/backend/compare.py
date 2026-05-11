"""
compare.py - 이전 분석과 현재 분석을 비교해서 트렌드 변화를 감지
"""


def compare_reports(current_repos: list, previous_repos: list) -> dict:
    if not previous_repos:
        return {"has_previous": False}

    prev_map = {r["name"]: r for r in previous_repos}
    curr_map = {r["name"]: r for r in current_repos}

    # 이번에 새로 등장한 레포
    new_repos = [r for r in current_repos if r["name"] not in prev_map]

    # 이전엔 있었는데 사라진 레포
    disappeared = [r for r in previous_repos if r["name"] not in curr_map]

    # trend_score 변화 계산
    rising  = []
    falling = []
    for r in current_repos:
        if r["name"] in prev_map:
            diff = r.get("trend_score", 0) - prev_map[r["name"]].get("trend_score", 0)
            if diff >= 5:
                rising.append({**r, "score_diff": round(diff, 1)})
            elif diff <= -5:
                falling.append({**r, "score_diff": round(diff, 1)})

    rising.sort(key=lambda x: x["score_diff"], reverse=True)
    falling.sort(key=lambda x: x["score_diff"])

    return {
        "has_previous": True,
        "new_repos":    new_repos[:5],
        "rising":       rising[:5],
        "falling":      falling[:5],
        "disappeared":  disappeared[:5],
    }
