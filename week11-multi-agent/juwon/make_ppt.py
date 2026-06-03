from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# ── 색상 팔레트 ──────────────────────────────────────────────
BG      = RGBColor(0x0d, 0x11, 0x17)   # GitHub 다크
BLUE    = RGBColor(0x58, 0xa6, 0xff)   # 강조 파랑
GREEN   = RGBColor(0x3f, 0xb9, 0x50)   # 강조 초록
YELLOW  = RGBColor(0xd2, 0x9e, 0x22)   # 강조 노랑
RED     = RGBColor(0xf8, 0x51, 0x49)   # 강조 빨강
GRAY    = RGBColor(0x8b, 0x94, 0x9e)   # 서브텍스트
WHITE   = RGBColor(0xc9, 0xd1, 0xd9)   # 본문
CARD    = RGBColor(0x16, 0x1b, 0x22)   # 카드 배경

W, H = Inches(13.33), Inches(7.5)


def new_prs() -> Presentation:
    prs = Presentation()
    prs.slide_width  = W
    prs.slide_height = H
    return prs


def bg(slide):
    shape = slide.shapes.add_shape(1, 0, 0, W, H)
    shape.fill.solid()
    shape.fill.fore_color.rgb = BG
    shape.line.fill.background()
    return shape


def box(slide, x, y, w, h, color=CARD, radius=False):
    shape = slide.shapes.add_shape(1, x, y, w, h)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape


def txt(slide, text, x, y, w, h, size=24, color=WHITE, bold=False, align=PP_ALIGN.LEFT):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    p  = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size  = Pt(size)
    run.font.color.rgb = color
    run.font.bold  = bold
    run.font.name  = "Malgun Gothic"


def accent_line(slide, x, y, w, color=BLUE):
    line = slide.shapes.add_shape(1, x, y, w, Pt(3))
    line.fill.solid()
    line.fill.fore_color.rgb = color
    line.line.fill.background()


# ── 슬라이드 1: 표지 ─────────────────────────────────────────
def slide_cover(prs):
    sl = prs.slides.add_slide(prs.slide_layouts[6])
    bg(sl)
    accent_line(sl, Inches(1), Inches(3.3), Inches(11.33), BLUE)
    txt(sl, "Week 11 — 오늘의 업데이트", Inches(1), Inches(1.5), Inches(11), Inches(1),
        size=36, color=BLUE, bold=True, align=PP_ALIGN.CENTER)
    txt(sl, "GitHub Tech Trend Analyzer", Inches(1), Inches(2.4), Inches(11), Inches(0.8),
        size=22, color=GRAY, align=PP_ALIGN.CENTER)
    items = ["트렌드 변화 감지", "자동 스케줄링", "채팅 기능", "UI 개선", "데이터 수집 개선"]
    colors = [GREEN, BLUE, YELLOW, RED, GREEN]
    for i, (item, c) in enumerate(zip(items, colors)):
        txt(sl, f"{'①②③④⑤'[i]}  {item}",
            Inches(1.5 + i * 2.1), Inches(4.2), Inches(2), Inches(0.6),
            size=14, color=c, bold=True)


# ── 슬라이드 2: 트렌드 변화 감지 ─────────────────────────────
def slide_compare(prs):
    sl = prs.slides.add_slide(prs.slide_layouts[6])
    bg(sl)
    txt(sl, "① 트렌드 변화 감지", Inches(0.8), Inches(0.4), Inches(8), Inches(0.7),
        size=28, color=GREEN, bold=True)
    txt(sl, "분석할 때마다 이전 결과와 자동 비교", Inches(0.8), Inches(1.0), Inches(10), Inches(0.5),
        size=16, color=GRAY)
    accent_line(sl, Inches(0.8), Inches(1.5), Inches(11.7), GREEN)

    cards = [
        ("🆕", "새로 등장", "이전엔 없었던\n신규 레포", BLUE),
        ("🚀", "급등",     "트렌드 점수가\n크게 오른 레포", GREEN),
        ("📉", "급락",     "점수가 크게\n떨어진 레포", RED),
        ("👋", "사라짐",   "목록에서\n빠진 레포", YELLOW),
    ]
    for i, (icon, title, desc, c) in enumerate(cards):
        bx = Inches(0.8 + i * 3.1)
        box(sl, bx, Inches(2.0), Inches(2.8), Inches(3.8), CARD)
        txt(sl, icon,  bx + Inches(0.2), Inches(2.2), Inches(2.5), Inches(0.7), size=30)
        txt(sl, title, bx + Inches(0.2), Inches(3.0), Inches(2.5), Inches(0.5), size=18, color=c, bold=True)
        txt(sl, desc,  bx + Inches(0.2), Inches(3.5), Inches(2.5), Inches(0.8), size=13, color=GRAY)

    txt(sl, "분석을 두 번 이상 실행하면 자동으로 비교 결과가 표시됩니다",
        Inches(0.8), Inches(6.3), Inches(11), Inches(0.5), size=13, color=GRAY, align=PP_ALIGN.CENTER)


# ── 슬라이드 3: 자동 스케줄링 ────────────────────────────────
def slide_schedule(prs):
    sl = prs.slides.add_slide(prs.slide_layouts[6])
    bg(sl)
    txt(sl, "② 자동 스케줄링", Inches(0.8), Inches(0.4), Inches(8), Inches(0.7),
        size=28, color=BLUE, bold=True)
    txt(sl, "버튼 없이 매일 정해진 시간에 자동 실행", Inches(0.8), Inches(1.0), Inches(10), Inches(0.5),
        size=16, color=GRAY)
    accent_line(sl, Inches(0.8), Inches(1.5), Inches(11.7), BLUE)

    flow = ["⏰ 매일 지정 시간", "→", "🤖 자동 분석", "→", "📧 메일 자동 발송"]
    colors_f = [YELLOW, GRAY, GREEN, GRAY, BLUE]
    for i, (step, c) in enumerate(zip(flow, colors_f)):
        txt(sl, step, Inches(0.6 + i * 2.4), Inches(2.4), Inches(2.3), Inches(0.8),
            size=17, color=c, bold=("→" not in step), align=PP_ALIGN.CENTER)

    box(sl, Inches(0.8), Inches(3.4), Inches(5.5), Inches(2.8), CARD)
    txt(sl, "사이드바 설정", Inches(1.0), Inches(3.6), Inches(5), Inches(0.5),
        size=15, color=BLUE, bold=True)
    for i, line in enumerate(["• 자동 실행 토글 ON/OFF", "• 실행 시간 선택 (0~23시)", "• 분석 기간 선택", "• 다음 실행 시간 표시"]):
        txt(sl, line, Inches(1.0), Inches(4.1 + i * 0.5), Inches(5), Inches(0.45), size=13, color=WHITE)

    box(sl, Inches(6.8), Inches(3.4), Inches(5.7), Inches(2.8), CARD)
    txt(sl, "사용 기술", Inches(7.0), Inches(3.6), Inches(5.3), Inches(0.5),
        size=15, color=GREEN, bold=True)
    for i, line in enumerate(["• APScheduler — 백그라운드 스케줄러", "• CronTrigger — 시간 지정 실행", "• FastAPI lifespan — 서버 시작/종료 관리"]):
        txt(sl, line, Inches(7.0), Inches(4.1 + i * 0.5), Inches(5.3), Inches(0.45), size=13, color=WHITE)


# ── 슬라이드 4: 채팅 기능 ────────────────────────────────────
def slide_chat(prs):
    sl = prs.slides.add_slide(prs.slide_layouts[6])
    bg(sl)
    txt(sl, "③ 채팅 기능", Inches(0.8), Inches(0.4), Inches(8), Inches(0.7),
        size=28, color=YELLOW, bold=True)
    txt(sl, "분석 결과를 보면서 AI에게 바로 질문", Inches(0.8), Inches(1.0), Inches(10), Inches(0.5),
        size=16, color=GRAY)
    accent_line(sl, Inches(0.8), Inches(1.5), Inches(11.7), YELLOW)

    questions = [
        "이번주 가장 주목할 레포 하나만 뽑아줘",
        "보안 관련 레포만 정리해줘",
        "비전공자도 이해할 수 있게 설명해줘",
        "이 트렌드가 내년에도 계속될까?",
    ]
    for i, q in enumerate(questions):
        row = i // 2
        col = i %  2
        bx = Inches(0.8 + col * 6.2)
        by = Inches(2.1 + row * 1.5)
        box(sl, bx, by, Inches(5.8), Inches(1.2), CARD)
        txt(sl, f'💬  "{q}"', bx + Inches(0.2), by + Inches(0.3),
            Inches(5.4), Inches(0.7), size=14, color=WHITE)

    txt(sl, "분석 결과 전체(레포 목록 + 전문가 분석 + Judge 결론)를 AI가 참고해서 답변",
        Inches(0.8), Inches(6.3), Inches(11.7), Inches(0.5), size=13, color=GRAY, align=PP_ALIGN.CENTER)


# ── 슬라이드 5: UI + 데이터 개선 ─────────────────────────────
def slide_improve(prs):
    sl = prs.slides.add_slide(prs.slide_layouts[6])
    bg(sl)
    txt(sl, "④⑤ UI 개선 + 데이터 수집 개선", Inches(0.8), Inches(0.4), Inches(12), Inches(0.7),
        size=28, color=RED, bold=True)
    accent_line(sl, Inches(0.8), Inches(1.1), Inches(11.7), RED)

    box(sl, Inches(0.8), Inches(1.4), Inches(5.8), Inches(5.5), CARD)
    txt(sl, "④ 마크다운 렌더링", Inches(1.0), Inches(1.6), Inches(5.4), Inches(0.5),
        size=17, color=RED, bold=True)
    befores = ["### 주목할 트렌드", "- **TensorFlow**: 인기 지속", "- 급부상 중인 AutoGPT"]
    afters  = ["주목할 트렌드 (헤더)", "• TensorFlow: 인기 지속", "• 급부상 중인 AutoGPT"]
    txt(sl, "이전", Inches(1.0), Inches(2.1), Inches(2.5), Inches(0.4), size=12, color=GRAY)
    txt(sl, "이후", Inches(3.8), Inches(2.1), Inches(2.5), Inches(0.4), size=12, color=GREEN)
    for i, (b, a) in enumerate(zip(befores, afters)):
        txt(sl, b, Inches(1.0), Inches(2.5 + i * 0.6), Inches(2.6), Inches(0.55), size=11, color=GRAY)
        txt(sl, a, Inches(3.8), Inches(2.5 + i * 0.6), Inches(2.6), Inches(0.55), size=11, color=WHITE)
    txt(sl, "react-markdown 라이브러리 사용", Inches(1.0), Inches(5.3), Inches(5.4), Inches(0.4),
        size=12, color=GRAY)

    box(sl, Inches(7.0), Inches(1.4), Inches(5.5), Inches(5.5), CARD)
    txt(sl, "⑤ 데이터 수집 방식 교체", Inches(7.2), Inches(1.6), Inches(5.1), Inches(0.5),
        size=17, color=GREEN, bold=True)

    txt(sl, "이전", Inches(7.2), Inches(2.2), Inches(5), Inches(0.4), size=12, color=GRAY)
    box(sl, Inches(7.2), Inches(2.6), Inches(5.1), Inches(0.9), RGBColor(0x2a, 0x0d, 0x0d))
    txt(sl, "GitHub API 검색\n누적 스타 기준 → 오래된 거대 레포 상위 점령",
        Inches(7.3), Inches(2.65), Inches(4.9), Inches(0.8), size=11, color=RED)

    txt(sl, "이후", Inches(7.2), Inches(3.7), Inches(5), Inches(0.4), size=12, color=GREEN)
    box(sl, Inches(7.2), Inches(4.1), Inches(5.1), Inches(0.9), RGBColor(0x1a, 0x2d, 0x1a))
    txt(sl, "GitHub Trending 페이지 스크래핑\n이번 주 획득 스타 수 → 진짜 트렌드 반영",
        Inches(7.3), Inches(4.15), Inches(4.9), Inches(0.8), size=11, color=GREEN)

    txt(sl, "OSSInsight와 유사한 결과 달성", Inches(7.2), Inches(5.3), Inches(5.1), Inches(0.4),
        size=12, color=BLUE, bold=True)


# ── 슬라이드 6: 마무리 ───────────────────────────────────────
def slide_summary(prs):
    sl = prs.slides.add_slide(prs.slide_layouts[6])
    bg(sl)
    accent_line(sl, Inches(0.8), Inches(1.8), Inches(11.7), BLUE)
    txt(sl, "오늘 추가된 것들", Inches(0.8), Inches(0.6), Inches(11), Inches(0.9),
        size=30, color=BLUE, bold=True, align=PP_ALIGN.CENTER)

    rows = [
        ("①", "트렌드 변화 감지", "이전 분석과 비교 → 급등/급락/신규/사라짐", GREEN),
        ("②", "자동 스케줄링",   "매일 지정 시간 자동 분석 + 메일 발송",     BLUE),
        ("③", "채팅 기능",       "분석 결과 기반 AI 질문 응답",               YELLOW),
        ("④", "UI 개선",         "마크다운 렌더링으로 가독성 향상",            RED),
        ("⑤", "데이터 수집 개선","GitHub Trending 스크래핑 → 정확도 향상",   GREEN),
    ]
    for i, (num, title, desc, c) in enumerate(rows):
        by = Inches(2.1 + i * 0.95)
        box(sl, Inches(0.8), by, Inches(11.7), Inches(0.82), CARD)
        txt(sl, num,   Inches(1.0),  by + Inches(0.15), Inches(0.5),  Inches(0.55), size=18, color=c, bold=True)
        txt(sl, title, Inches(1.6),  by + Inches(0.15), Inches(2.8),  Inches(0.55), size=16, color=WHITE, bold=True)
        txt(sl, desc,  Inches(4.5),  by + Inches(0.18), Inches(7.8),  Inches(0.5),  size=13, color=GRAY)


# ── 실행 ─────────────────────────────────────────────────────
prs = new_prs()
slide_cover(prs)
slide_compare(prs)
slide_schedule(prs)
slide_chat(prs)
slide_improve(prs)
slide_summary(prs)

out = r"c:\윤주원\ai study\ai_study\week11-multi-agent\juwon\week11_update.pptx"
prs.save(out)
print("저장 완료:", out)
