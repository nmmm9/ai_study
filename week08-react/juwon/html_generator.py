"""
html_generator.py - 여행 계획 HTML 보고서 생성

Agent가 수집한 모든 데이터를 받아 브라우저에서 볼 수 있는
아름다운 HTML 여행 계획서로 변환
"""

from datetime import datetime


def generate_html(collected: dict, react_log: list) -> str:
    """수집된 여행 데이터를 HTML 문서로 변환"""

    meta    = collected.get("_meta", {})
    city    = meta.get("city", "여행지")
    days    = meta.get("days", 3)
    query   = meta.get("user_query", "")
    steps   = meta.get("steps", [])
    now     = datetime.now().strftime("%Y년 %m월 %d일")

    # ── 데이터 파싱 ──────────────────────────
    weather     = collected.get("get_weather", {})
    attractions = collected.get("search_attractions", {})
    restaurants = collected.get("search_restaurants", {})
    accommodation = collected.get("search_accommodation", {})
    transport   = collected.get("get_transportation", {})
    budget      = collected.get("calculate_budget", {})
    festivals   = collected.get("get_festivals", {})
    tips        = collected.get("get_local_tips", {})
    season      = collected.get("get_best_season", {})
    itinerary   = collected.get("create_itinerary", {})

    # ── 섹션 HTML 생성 함수들 ─────────────────

    def weather_section():
        if not weather or "error" in weather:
            return ""
        forecast_html = ""
        for f in weather.get("3일예보", []):
            forecast_html += f"""
            <div class="forecast-card">
                <div class="forecast-date">{f.get('날짜','')}</div>
                <div class="forecast-icon">{f.get('날씨','')}</div>
                <div class="forecast-temp">
                    <span class="high">{f.get('최고','')}</span>
                    <span class="low">{f.get('최저','')}</span>
                </div>
            </div>"""
        return f"""
        <section class="section">
            <h2 class="section-title">🌤 현재 날씨</h2>
            <div class="weather-main">
                <div class="weather-now">
                    <div class="weather-condition">{weather.get('현재날씨','')}</div>
                    <div class="weather-temp">{weather.get('현재기온','')}</div>
                    <div class="weather-meta">
                        💧 습도 {weather.get('습도','')} &nbsp;|&nbsp;
                        💨 풍속 {weather.get('풍속','')}
                    </div>
                    <div class="weather-tags">
                        <span class="tag tag-blue">{weather.get('우산여부','')}</span>
                        <span class="tag tag-green">{weather.get('옷차림','')}</span>
                    </div>
                </div>
                <div class="forecast-list">{forecast_html}</div>
            </div>
        </section>"""

    def attractions_section():
        if not attractions or "error" in attractions:
            return ""
        items_html = ""
        for cat, items in attractions.get("관광지", {}).items():
            emoji = "🌿" if cat == "자연" else "🏛"
            for item in items:
                items_html += f'<span class="attraction-tag">{emoji} {item}</span>'
        return f"""
        <section class="section">
            <h2 class="section-title">🗺 관광지</h2>
            <div class="tag-cloud">{items_html}</div>
        </section>"""

    def restaurants_section():
        if not restaurants or "error" in restaurants:
            return ""
        cards = ""
        for r in restaurants.get("맛집목록", []):
            price_color = {"저렴": "#22c55e", "중급": "#3b82f6", "고급": "#f59e0b"}.get(r.get("price",""), "#888")
            cards += f"""
            <div class="rest-card">
                <div class="rest-name">{r.get('name','')}</div>
                <div class="rest-meta">
                    <span class="rest-cuisine">{r.get('cuisine','')}</span>
                    <span class="rest-price" style="color:{price_color}">{'💰' * {'저렴':1,'중급':2,'고급':3}.get(r.get('price',''),2)}</span>
                </div>
                <div class="rest-specialty">✨ {r.get('specialty','')}</div>
                <div class="rest-area">📍 {r.get('area','')}</div>
            </div>"""
        return f"""
        <section class="section">
            <h2 class="section-title">🍽 맛집</h2>
            <div class="card-grid">{cards}</div>
        </section>"""

    def accommodation_section():
        if not accommodation or "error" in accommodation:
            return ""
        cards = ""
        for a in accommodation.get("숙소목록", []):
            type_color = {"저렴": "#22c55e", "중급": "#3b82f6", "고급": "#f59e0b"}.get(a.get("type",""), "#888")
            cards += f"""
            <div class="acc-card">
                <div class="acc-name">{a.get('name','')}</div>
                <div class="acc-type" style="background:{type_color}20;color:{type_color};border:1px solid {type_color}40">
                    {a.get('type','')}
                </div>
                <div class="acc-price">💳 {a.get('price','')}</div>
                <div class="acc-location">📍 {a.get('location','')}</div>
                <div class="acc-features">🏨 {a.get('features','')}</div>
            </div>"""
        return f"""
        <section class="section">
            <h2 class="section-title">🏨 숙소</h2>
            <div class="card-grid">{cards}</div>
        </section>"""

    def transport_section():
        if not transport or "error" in transport:
            return ""
        routes_html = ""
        for k, v in transport.get("교통편", {}).items():
            if isinstance(v, dict):
                for method, info in v.items():
                    routes_html += f"""
                    <div class="trans-row">
                        <span class="trans-method">{method}</span>
                        <span class="trans-info">{info}</span>
                    </div>"""
            else:
                routes_html += f"""
                <div class="trans-row">
                    <span class="trans-method">{k}</span>
                    <span class="trans-info">{v}</span>
                </div>"""
        return f"""
        <section class="section">
            <h2 class="section-title">🚆 교통편</h2>
            <div class="trans-box">
                <div class="trans-title">{transport.get('출발지','')} → {transport.get('목적지','')}</div>
                {routes_html}
                <div class="trans-local">
                    <span class="tag tag-blue">현지 교통</span>
                    {transport.get('현지교통','')}
                </div>
            </div>
        </section>"""

    def budget_section():
        if not budget or "error" in budget:
            return ""
        items = [
            ("🏨 숙박비", budget.get("숙박비", "")),
            ("🍽 식비",   budget.get("식비", "")),
            ("🚌 교통비", budget.get("교통비", "")),
            ("🎭 활동비", budget.get("활동비", "")),
        ]
        items_html = "".join(
            f'<div class="budget-row"><span class="budget-label">{label}</span><span class="budget-amount">{amount}</span></div>'
            for label, amount in items
        )
        return f"""
        <section class="section">
            <h2 class="section-title">💰 예산</h2>
            <div class="budget-box">
                {items_html}
                <div class="budget-total">
                    <span>💎 총 예산</span>
                    <span class="budget-total-amount">{budget.get('총예산','')}</span>
                </div>
                <div class="budget-daily">하루 평균 {budget.get('1일평균','')}</div>
            </div>
        </section>"""

    def itinerary_section():
        if not itinerary or "error" in itinerary:
            return ""
        days_html = ""
        for day_label, schedule in itinerary.get("일정표", {}).items():
            slots = [
                ("🌅 오전", schedule.get("오전", "")),
                ("☀️ 점심", schedule.get("점심", "")),
                ("🌇 오후", schedule.get("오후", "")),
                ("🌙 저녁", schedule.get("저녁", "")),
            ]
            slots_html = "".join(
                f'<div class="slot"><span class="slot-time">{time}</span><span class="slot-act">{act}</span></div>'
                for time, act in slots
            )
            days_html += f"""
            <div class="day-card">
                <div class="day-header">{day_label}</div>
                <div class="day-slots">{slots_html}</div>
            </div>"""
        return f"""
        <section class="section">
            <h2 class="section-title">📅 날짜별 일정</h2>
            <div class="itinerary-grid">{days_html}</div>
        </section>"""

    def festivals_section():
        if not festivals or not festivals.get("축제목록"):
            return ""
        cards = ""
        for f in festivals.get("축제목록", []):
            cards += f"""
            <div class="festival-card">
                <div class="festival-name">🎉 {f.get('name','')}</div>
                <div class="festival-month">📅 {f.get('month','')}</div>
                <div class="festival-location">📍 {f.get('location','')}</div>
                <div class="festival-desc">{f.get('desc','')}</div>
            </div>"""
        return f"""
        <section class="section">
            <h2 class="section-title">🎊 축제 & 행사</h2>
            <div class="card-grid">{cards}</div>
        </section>"""

    def tips_section():
        if not tips or not tips.get("꿀팁"):
            return ""
        tips_html = "".join(f'<li class="tip-item">💡 {tip}</li>' for tip in tips.get("꿀팁", []))
        return f"""
        <section class="section">
            <h2 class="section-title">✨ 여행 꿀팁</h2>
            <ul class="tips-list">{tips_html}</ul>
        </section>"""

    def season_section():
        if not season or "error" in season:
            return ""
        exclude = {"city", "최적시기", "tip"}
        seasons_html = ""
        for k, v in season.items():
            if k not in exclude:
                seasons_html += f'<div class="season-row"><span class="season-name">{k}</span><span class="season-desc">{v}</span></div>'
        tip_html = f'<div class="season-tip">💬 TIP: {season.get("tip","")}</div>' if season.get("tip") else ""
        return f"""
        <section class="section">
            <h2 class="section-title">📆 최적 여행 시기</h2>
            <div class="season-best">🌟 {season.get('최적시기','')}</div>
            <div class="season-grid">{seasons_html}</div>
            {tip_html}
        </section>"""

    def react_log_section():
        if not react_log:
            return ""
        rows = ""
        for i, log in enumerate(react_log, 1):
            rows += f"""
            <tr>
                <td>{i}</td>
                <td><code>{log.get('action','')}</code></td>
                <td>{json.dumps(log.get('args',{}), ensure_ascii=False)}</td>
                <td>✅ 완료</td>
            </tr>"""
        return f"""
        <section class="section react-section">
            <h2 class="section-title">🤖 ReAct 실행 로그</h2>
            <p class="react-desc">AI가 스스로 판단하며 도구를 호출한 과정 (총 {len(react_log)}회)</p>
            <table class="react-table">
                <thead>
                    <tr><th>#</th><th>Action (도구)</th><th>Arguments (인자)</th><th>Observation</th></tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </section>"""

    import json  # 내부에서 사용

    # ── CSS ──────────────────────────────────
    css = """
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', -apple-system, sans-serif; background: #f0f4ff; color: #1e293b; }

        /* Hero */
        .hero { background: linear-gradient(135deg, #1d4ed8 0%, #7c3aed 100%); color: white; padding: 60px 40px; text-align: center; }
        .hero-badge { display: inline-block; background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.4); border-radius: 20px; padding: 6px 18px; font-size: 13px; margin-bottom: 16px; }
        .hero-title { font-size: 48px; font-weight: 800; margin-bottom: 8px; }
        .hero-sub   { font-size: 18px; opacity: 0.85; margin-bottom: 20px; }
        .hero-meta  { font-size: 14px; opacity: 0.7; }
        .hero-tags  { margin-top: 20px; display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; }
        .hero-tag   { background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.3); border-radius: 20px; padding: 6px 16px; font-size: 13px; }

        /* Steps */
        .steps-bar { background: white; padding: 20px 40px; display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; border-bottom: 1px solid #e2e8f0; }
        .step-item { background: #eff6ff; color: #2563eb; border-radius: 20px; padding: 6px 14px; font-size: 12px; font-weight: 600; }
        .step-num  { background: #2563eb; color: white; border-radius: 50%; width: 18px; height: 18px; display: inline-flex; align-items: center; justify-content: center; font-size: 10px; margin-right: 6px; }

        /* Container */
        .container { max-width: 1100px; margin: 0 auto; padding: 30px 20px; }

        /* Section */
        .section { background: white; border-radius: 16px; padding: 30px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
        .section-title { font-size: 20px; font-weight: 700; color: #1e293b; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 2px solid #eff6ff; }

        /* Weather */
        .weather-main { display: flex; gap: 30px; align-items: flex-start; flex-wrap: wrap; }
        .weather-now  { flex: 0 0 auto; }
        .weather-condition { font-size: 28px; font-weight: 700; margin-bottom: 4px; }
        .weather-temp { font-size: 52px; font-weight: 800; color: #2563eb; line-height: 1; margin-bottom: 8px; }
        .weather-meta { font-size: 14px; color: #64748b; margin-bottom: 12px; }
        .weather-tags { display: flex; gap: 8px; flex-wrap: wrap; }
        .tag { display: inline-block; border-radius: 20px; padding: 5px 12px; font-size: 12px; font-weight: 600; }
        .tag-blue  { background: #eff6ff; color: #2563eb; }
        .tag-green { background: #f0fdf4; color: #16a34a; }
        .forecast-list { display: flex; gap: 12px; flex-wrap: wrap; }
        .forecast-card { background: #f8fafc; border-radius: 12px; padding: 14px; text-align: center; min-width: 90px; }
        .forecast-date { font-size: 11px; color: #94a3b8; margin-bottom: 6px; }
        .forecast-icon { font-size: 20px; margin-bottom: 6px; }
        .forecast-temp { font-size: 12px; }
        .high { color: #ef4444; font-weight: 700; margin-right: 4px; }
        .low  { color: #3b82f6; }

        /* Tags */
        .tag-cloud { display: flex; gap: 10px; flex-wrap: wrap; }
        .attraction-tag { background: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; border-radius: 20px; padding: 6px 14px; font-size: 14px; }

        /* Cards */
        .card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }

        /* Restaurant */
        .rest-card { background: #fafafa; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; }
        .rest-name { font-weight: 700; font-size: 15px; margin-bottom: 8px; }
        .rest-meta { display: flex; justify-content: space-between; margin-bottom: 6px; }
        .rest-cuisine { font-size: 12px; color: #64748b; }
        .rest-specialty { font-size: 12px; color: #475569; margin-bottom: 4px; }
        .rest-area { font-size: 12px; color: #94a3b8; }

        /* Accommodation */
        .acc-card { background: #fafafa; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; }
        .acc-name { font-weight: 700; font-size: 15px; margin-bottom: 8px; }
        .acc-type { display: inline-block; border-radius: 20px; padding: 3px 10px; font-size: 12px; font-weight: 600; margin-bottom: 8px; }
        .acc-price, .acc-location, .acc-features { font-size: 13px; color: #475569; margin-bottom: 4px; }

        /* Transport */
        .trans-box { background: #f8fafc; border-radius: 12px; padding: 20px; }
        .trans-title { font-weight: 700; font-size: 16px; margin-bottom: 14px; color: #1d4ed8; }
        .trans-row { display: flex; gap: 12px; padding: 10px 0; border-bottom: 1px solid #e2e8f0; align-items: baseline; }
        .trans-method { font-weight: 700; font-size: 14px; min-width: 80px; color: #2563eb; }
        .trans-info { font-size: 14px; color: #475569; }
        .trans-local { margin-top: 14px; font-size: 14px; color: #475569; display: flex; gap: 10px; align-items: baseline; flex-wrap: wrap; }

        /* Budget */
        .budget-box { background: #f8fafc; border-radius: 12px; padding: 20px; }
        .budget-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #e2e8f0; font-size: 15px; }
        .budget-label { color: #475569; }
        .budget-amount { font-weight: 600; }
        .budget-total { display: flex; justify-content: space-between; padding: 16px 0 8px; font-weight: 700; font-size: 18px; margin-top: 4px; }
        .budget-total-amount { color: #2563eb; font-size: 22px; }
        .budget-daily { text-align: right; font-size: 13px; color: #94a3b8; }

        /* Itinerary */
        .itinerary-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }
        .day-card { border: 2px solid #eff6ff; border-radius: 12px; overflow: hidden; }
        .day-header { background: #2563eb; color: white; padding: 10px 16px; font-weight: 700; font-size: 15px; }
        .day-slots { padding: 12px; }
        .slot { display: flex; gap: 8px; padding: 8px 0; border-bottom: 1px solid #f1f5f9; font-size: 13px; align-items: baseline; }
        .slot:last-child { border-bottom: none; }
        .slot-time { min-width: 56px; color: #64748b; font-size: 12px; }
        .slot-act { color: #1e293b; }

        /* Festival */
        .festival-card { background: #fffbeb; border: 1px solid #fde68a; border-radius: 12px; padding: 16px; }
        .festival-name { font-weight: 700; font-size: 15px; margin-bottom: 6px; }
        .festival-month, .festival-location { font-size: 13px; color: #78716c; margin-bottom: 4px; }
        .festival-desc { font-size: 13px; color: #57534e; margin-top: 6px; }

        /* Tips */
        .tips-list { list-style: none; display: flex; flex-direction: column; gap: 10px; }
        .tip-item { background: #f0fdf4; border-left: 3px solid #22c55e; border-radius: 0 8px 8px 0; padding: 10px 16px; font-size: 14px; color: #166534; }

        /* Season */
        .season-best { font-size: 18px; font-weight: 700; color: #2563eb; margin-bottom: 16px; }
        .season-grid { display: flex; flex-direction: column; gap: 8px; }
        .season-row { display: flex; gap: 12px; font-size: 14px; padding: 8px 0; border-bottom: 1px solid #f1f5f9; }
        .season-name { min-width: 80px; font-weight: 600; color: #1d4ed8; }
        .season-desc { color: #475569; }
        .season-tip { margin-top: 16px; background: #fef9c3; border-radius: 8px; padding: 10px 14px; font-size: 13px; color: #854d0e; }

        /* ReAct Log */
        .react-section { background: #1e293b; color: #e2e8f0; }
        .react-section .section-title { color: #60a5fa; border-bottom-color: #334155; }
        .react-desc { font-size: 13px; color: #94a3b8; margin-bottom: 16px; }
        .react-table { width: 100%; border-collapse: collapse; font-size: 13px; }
        .react-table th { background: #334155; padding: 10px 12px; text-align: left; color: #94a3b8; font-weight: 600; }
        .react-table td { padding: 10px 12px; border-bottom: 1px solid #334155; color: #cbd5e1; vertical-align: top; }
        .react-table code { background: #0f172a; padding: 2px 8px; border-radius: 4px; color: #60a5fa; font-size: 12px; }

        /* Footer */
        .footer { text-align: center; padding: 30px; font-size: 13px; color: #94a3b8; }
    """

    # ── HTML 조합 ─────────────────────────────
    meta_tags = meta.get("accommodation_type","중급") + " 숙박 | " + meta.get("meal_budget","보통") + " 식비 | " + meta.get("transport","대중교통")
    steps_html = "".join(
        f'<div class="step-item"><span class="step-num">{i}</span>{s}</div>'
        for i, s in enumerate(steps, 1)
    )

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{city} {days}일 여행 계획</title>
    <style>{css}</style>
</head>
<body>

<div class="hero">
    <div class="hero-badge">✈ AI 여행 플래너 | 8주차 ReAct Agent</div>
    <div class="hero-title">{city} 여행</div>
    <div class="hero-sub">"{query}"</div>
    <div class="hero-meta">생성일: {now}</div>
    <div class="hero-tags">
        <span class="hero-tag">📅 {days}일 여행</span>
        <span class="hero-tag">🏨 {meta.get('accommodation_type','중급')} 숙박</span>
        <span class="hero-tag">🍽 {meta.get('meal_budget','보통')} 식비</span>
        <span class="hero-tag">🚌 {meta.get('transport','대중교통')}</span>
    </div>
</div>

<div class="steps-bar">
    {steps_html}
</div>

<div class="container">
    {itinerary_section()}
    {weather_section()}
    {budget_section()}
    {attractions_section()}
    {restaurants_section()}
    {accommodation_section()}
    {transport_section()}
    {festivals_section()}
    {season_section()}
    {tips_section()}
    {react_log_section()}
</div>

<div class="footer">
    🤖 AI가 ReAct + Plan-and-Execute 패턴으로 자동 생성 &nbsp;|&nbsp;
    도구 {len(react_log)}개 호출 완료 &nbsp;|&nbsp; 8주차 Function Calling Agent
</div>

</body>
</html>"""

    return html


def save_html(collected: dict, react_log: list, output_dir: str = ".") -> str:
    """HTML 파일 저장 후 경로 반환"""
    import os
    meta = collected.get("_meta", {})
    city = meta.get("city", "여행지")
    days = meta.get("days", 3)

    filename = f"여행계획_{city}_{days}일.html"
    filepath = os.path.join(output_dir, filename)

    html = generate_html(collected, react_log)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    return filepath
