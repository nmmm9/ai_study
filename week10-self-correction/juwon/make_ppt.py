"""
make_ppt.py - Week 10 Self-Correction 발표용 PPT 생성

슬라이드 구성:
1. 표지
2. 9주차 vs 10주차
3. Self-Correction이란?
4. LangGraph 흐름 설계
5. 품질 검토 기준 (reflect 노드)
6. Self-Correction 루프 동작 방식
7. 구현: notifier (Gmail + GitHub README)
8. 데모 화면 설명
9. 회고 & 다음 주
"""

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

# ── 팔레트 ───────────────────────────────────────────────────
BG     = RGBColor(0x0d, 0x11, 0x17)   # GitHub dark bg
CARD   = RGBColor(0x16, 0x1b, 0x22)   # card bg
BORDER = RGBColor(0x30, 0x36, 0x3d)   # border
BLUE   = RGBColor(0x58, 0xa6, 0xff)   # accent blue
GREEN  = RGBColor(0x3f, 0xb9, 0x50)   # green (pass)
RED    = RGBColor(0xf8, 0x51, 0x49)   # red (fail)
YELLOW = RGBColor(0xd2, 0x9e, 0x22)   # yellow
WHITE  = RGBColor(0xff, 0xff, 0xff)
GRAY   = RGBColor(0x8b, 0x94, 0x9e)


def set_bg(slide, prs):
    bg = slide.shapes.add_shape(
        1,
        0, 0,
        prs.slide_width, prs.slide_height,
    )
    bg.fill.solid()
    bg.fill.fore_color.rgb = BG
    bg.line.fill.background()
    bg.zorder = 0


def add_title(slide, text, top=Inches(0.3)):
    txBox = slide.shapes.add_textbox(Inches(0.5), top, Inches(9), Inches(0.7))
    tf    = txBox.text_frame
    tf.word_wrap = False
    p  = tf.paragraphs[0]
    run = p.add_run()
    run.text = text
    run.font.size  = Pt(28)
    run.font.bold  = True
    run.font.color.rgb = BLUE


def add_text(slide, text, left, top, width, height,
             size=14, color=None, bold=False, wrap=True):
    if color is None:
        color = WHITE
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf    = txBox.text_frame
    tf.word_wrap = wrap
    p    = tf.paragraphs[0]
    run  = p.add_run()
    run.text             = text
    run.font.size        = Pt(size)
    run.font.bold        = bold
    run.font.color.rgb   = color


def add_card(slide, prs, text, left, top, width, height,
             accent=BLUE, text_size=13):
    box = slide.shapes.add_shape(1, left, top, width, height)
    box.fill.solid()
    box.fill.fore_color.rgb = CARD
    box.line.color.rgb = accent
    box.line.width     = Pt(1.5)

    txBox = slide.shapes.add_textbox(
        left + Inches(0.1), top + Inches(0.08),
        width - Inches(0.2), height - Inches(0.1),
    )
    tf = txBox.text_frame
    tf.word_wrap = True
    p   = tf.paragraphs[0]
    run = p.add_run()
    run.text           = text
    run.font.size      = Pt(text_size)
    run.font.color.rgb = WHITE


# ════════════════════════════════════════════════════════════
prs = Presentation()
prs.slide_width  = Inches(10)
prs.slide_height = Inches(5.625)
blank = prs.slide_layouts[6]

# ── 슬라이드 1: 표지 ─────────────────────────────────────────
s = prs.slides.add_slide(blank)
set_bg(s, prs)

add_text(s, "Week 10", Inches(0.5), Inches(0.8), Inches(9), Inches(0.5),
         size=18, color=GRAY)
add_text(s, "Self-Correction", Inches(0.5), Inches(1.3), Inches(9), Inches(1),
         size=44, bold=True, color=BLUE)
add_text(s, "결과 검토 및 수정 로직 (Reflection)",
         Inches(0.5), Inches(2.3), Inches(9), Inches(0.6),
         size=20, color=WHITE)
add_text(s, "틀린 결과 시 재검색/수정하는 루프 구현",
         Inches(0.5), Inches(2.9), Inches(9), Inches(0.5),
         size=16, color=GRAY)

add_text(s, "GitHub Tech Trend Analyzer v2",
         Inches(0.5), Inches(4.2), Inches(9), Inches(0.4),
         size=14, color=GREEN)
add_text(s, "LangGraph · Self-Correction · Gmail · GitHub README",
         Inches(0.5), Inches(4.7), Inches(9), Inches(0.4),
         size=12, color=GRAY)

# ── 슬라이드 2: 9주차 vs 10주차 ─────────────────────────────
s = prs.slides.add_slide(blank)
set_bg(s, prs)
add_title(s, "9주차 vs 10주차")

add_card(s, prs,
    "9주차\n\ncollect → validate → analyze → compare → report\n\n"
    "• analyze 노드 1번 실행\n"
    "• 결과가 나쁘더라도 그냥 저장\n"
    "• 품질 검토 없음",
    Inches(0.3), Inches(1.1), Inches(4.5), Inches(3.8),
    accent=GRAY)

add_card(s, prs,
    "10주차\n\ncollect → validate → generate → reflect\n→ compare → notify → report\n\n"
    "• reflect 노드: 품질 자동 채점 (0~100점)\n"
    "• 70점 미만 → 피드백 반영해서 재생성\n"
    "• notify 노드: Gmail + GitHub README 자동 발송",
    Inches(5.2), Inches(1.1), Inches(4.5), Inches(3.8),
    accent=BLUE)

add_text(s, "→", Inches(4.7), Inches(2.6), Inches(0.5), Inches(0.5),
         size=24, color=BLUE, bold=True)

# ── 슬라이드 3: Self-Correction이란? ────────────────────────
s = prs.slides.add_slide(blank)
set_bg(s, prs)
add_title(s, "Self-Correction이란?")

add_text(s,
    "AI가 자기 결과를 스스로 검토하고, 기준에 미달하면 다시 생성하는 루프",
    Inches(0.5), Inches(1.0), Inches(9), Inches(0.5),
    size=16, color=WHITE)

cards = [
    ("🤖 Generate", "AI가 트렌드 분석 결과를 처음 생성", BLUE),
    ("🔍 Reflect",  "기준표로 자동 채점\n(길이·키워드·레포 이름·인사이트·방향성)", YELLOW),
    ("❌ Fail",      "70점 미만이면\n피드백을 붙여서 다시 Generate로", RED),
    ("✅ Pass",      "70점 이상이면\n다음 단계(compare)로 진행", GREEN),
]
for i, (title, body, color) in enumerate(cards):
    add_card(s, prs,
        f"{title}\n\n{body}",
        Inches(0.3 + i * 2.35), Inches(1.7), Inches(2.2), Inches(2.8),
        accent=color)

add_text(s,
    "핵심: AI 결과를 믿지 말고 검증하라. 기준을 코드로 명확히 정의하면 자동으로 품질이 올라간다.",
    Inches(0.5), Inches(4.7), Inches(9), Inches(0.5),
    size=13, color=GRAY)

# ── 슬라이드 4: LangGraph 흐름 설계 ─────────────────────────
s = prs.slides.add_slide(blank)
set_bg(s, prs)
add_title(s, "LangGraph 흐름 설계")

flow = """\
collect  →  validate  →  generate  →  reflect
              ↑↓                        ↑↓
         (데이터 부족)           (점수 70 미만)
          재수집 최대 3회         재생성 최대 3회
                                        ↓ 점수 70 이상
                               compare  →  notify  →  report  →  END"""

add_card(s, prs, flow,
         Inches(0.4), Inches(1.1), Inches(9.2), Inches(2.2),
         accent=BLUE, text_size=14)

nodes = [
    ("collect",  "GitHub API\n데이터 수집",    BLUE),
    ("validate", "레포 5개 이상?\n부족 시 재수집", YELLOW),
    ("generate", "AI 분석 생성\n피드백 반영",    BLUE),
    ("reflect",  "품질 채점\n0~100점",          YELLOW),
    ("compare",  "이전 기록\n비교",              BLUE),
    ("notify",   "Gmail+\nREADME",             GREEN),
    ("report",   "JSON 저장",                  GRAY),
]
for i, (name, desc, color) in enumerate(nodes):
    add_card(s, prs, f"{name}\n\n{desc}",
             Inches(0.2 + i * 1.37), Inches(3.5), Inches(1.25), Inches(1.8),
             accent=color, text_size=11)

# ── 슬라이드 5: 품질 검토 기준 ──────────────────────────────
s = prs.slides.add_slide(blank)
set_bg(s, prs)
add_title(s, "품질 검토 기준 — reflect 노드")

criteria = [
    ("분석 길이",      "300자 이상",   "20점", GREEN),
    ("트렌드 키워드",  "3개 이상",     "25점", GREEN),
    ("레포 이름 언급", "3개 이상",     "25점", GREEN),
    ("인사이트 수",    "3개 이상",     "15점", BLUE),
    ("기술 방향성",    "키워드 2개↑",  "15점", BLUE),
]

for i, (name, cond, pts, color) in enumerate(criteria):
    y = Inches(1.1 + i * 0.82)
    add_card(s, prs, f"{name}  ·  {cond}  →  {pts}",
             Inches(1.0), y, Inches(7.5), Inches(0.68),
             accent=color, text_size=15)

add_card(s, prs, "합계 70점 이상 → 통과 (compare로 진행)   |   70점 미만 → 재생성 (최대 3회)",
         Inches(0.5), Inches(5.1), Inches(9.0), Inches(0.38),
         accent=GREEN, text_size=13)

# ── 슬라이드 6: Self-Correction 루프 동작 방식 ───────────────
s = prs.slides.add_slide(blank)
set_bg(s, prs)
add_title(s, "Self-Correction 루프 동작 방식")

example = """\
[시도 1]  점수: 45/100
  → 분석 짧음 (210자) | 레포 이름 언급 부족 (1개) | 방향성 키워드 부족
  → 피드백 반영하여 재생성

[시도 2]  점수: 65/100
  → 분석 길이 통과 | 트렌드 키워드 부족 (2개) | 방향성 키워드 부족
  → 피드백 반영하여 재생성

[시도 3]  점수: 85/100  ✅ 통과
  → 모든 품질 기준 통과 → compare 노드로 진행"""

add_card(s, prs, example,
         Inches(0.4), Inches(1.1), Inches(9.2), Inches(3.0),
         accent=GREEN, text_size=13)

add_text(s,
    "피드백이 있으면 generate 프롬프트에 '이전 피드백: ...' 섹션이 추가되어\n"
    "AI가 어디가 부족했는지 알고 다시 생성한다.",
    Inches(0.5), Inches(4.3), Inches(9), Inches(0.9),
    size=14, color=GRAY)

# ── 슬라이드 7: notifier — Gmail + GitHub README ─────────────
s = prs.slides.add_slide(blank)
set_bg(s, prs)
add_title(s, "구현: notifier.py — Gmail + GitHub README")

add_card(s, prs,
    "Gmail SMTP 발송\n\n"
    "• smtplib.SMTP_SSL('smtp.gmail.com', 465)\n"
    "• Google 앱 비밀번호 필요 (일반 비밀번호 X)\n"
    "• HTML 이메일: 트렌딩 레포 테이블 + 인사이트 + AI 분석\n"
    "• .env: GMAIL_USER + GMAIL_APP_PASSWORD",
    Inches(0.3), Inches(1.1), Inches(4.5), Inches(3.5),
    accent=BLUE)

add_card(s, prs,
    "GitHub README 업로드\n\n"
    "• GitHub API PUT /repos/:owner/:repo/contents/TREND_REPORT.md\n"
    "• 파일 없으면 새로 생성, 있으면 SHA 포함하여 업데이트\n"
    "• 내용: 트렌딩 레포 + 품질 점수 + Self-Correction 이력\n"
    "• .env: GITHUB_TOKEN + GITHUB_TREND_REPO",
    Inches(5.2), Inches(1.1), Inches(4.5), Inches(3.5),
    accent=GREEN)

add_text(s,
    "notify 노드는 compare 다음에 실행 → 품질 통과한 결과만 발송된다",
    Inches(0.5), Inches(4.8), Inches(9), Inches(0.5),
    size=13, color=GRAY)

# ── 슬라이드 8: 데모 화면 설명 ──────────────────────────────
s = prs.slides.add_slide(blank)
set_bg(s, prs)
add_title(s, "데모 화면 설명")

items = [
    ("품질 점수 메트릭",     "AI 품질 점수 / 재생성 횟수 — 상단 5개 메트릭 중 오른쪽 2개",         BLUE),
    ("Self-Correction 이력", "시도별 점수 + 피드백 타임라인 + 점수 추이 바 차트",                  YELLOW),
    ("알림 발송 상태",       "Gmail: success/error | README: success/error — 결과 색상 표시",       GREEN),
    ("기존 대시보드",        "트렌딩 레포 카드 + 언어 분포 차트 + AI 분석 + 비교 (9주차와 동일)",   GRAY),
    ("사이드바 기록",        "날짜별 품질 점수 포함하여 이전 분석 이력 표시",                       BLUE),
]

for i, (title, desc, color) in enumerate(items):
    y = Inches(1.1 + i * 0.82)
    add_card(s, prs, f"▶ {title}  —  {desc}",
             Inches(0.5), y, Inches(9.0), Inches(0.68),
             accent=color, text_size=13)

# ── 슬라이드 9: 회고 & 다음 주 ──────────────────────────────
s = prs.slides.add_slide(blank)
set_bg(s, prs)
add_title(s, "회고 & 다음 주")

add_card(s, prs,
    "이번 주 배운 점\n\n"
    "• Self-Correction = 품질 기준을 코드로 정의 + 조건 분기로 재실행\n"
    "• reflect 노드를 분리하면 기준 수정이 generate에 영향 없음\n"
    "• 70점 기준: 너무 높으면 무한루프, 너무 낮으면 의미 없음\n"
    "• Gmail App Password는 2단계 인증 후 Google에서 발급 필요\n"
    "• GitHub API: 파일 업데이트 시 기존 SHA를 함께 전달해야 함",
    Inches(0.3), Inches(1.1), Inches(9.4), Inches(2.7),
    accent=BLUE)

add_card(s, prs,
    "다음 주 (Week 11): Multi-Agent\n\n"
    "• 여러 에이전트가 협력하는 구조\n"
    "• 에이전트 A가 에이전트 B에게 작업을 위임\n"
    "• Supervisor 패턴: 중앙 관리자가 서브 에이전트 조율",
    Inches(0.3), Inches(4.0), Inches(9.4), Inches(1.4),
    accent=GREEN)

# ── 저장 ─────────────────────────────────────────────────────
OUTPUT = r"c:\윤주원\ai study\ai_study\week10-self-correction\juwon\week10_발표.pptx"
prs.save(OUTPUT)
print(f"저장 완료: {OUTPUT}")
