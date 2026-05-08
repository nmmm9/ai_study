# Week 10 — Self-Correction (Critic Loop)

9주차 LangGraph Multi-Agent에 **Critic 노드 + 조건부 루프**를 추가해
Writer가 작성한 답변을 자동 검수하고, 점수가 낮으면 피드백을 반영해 재작성합니다.

## 아키텍처

```
[START] → Supervisor → (parallel) → 8 Domain Agents ─┐
                                                      │
                                                      ▼
                                                   Writer ──→ Critic ─┐
                                                     ▲                 │
                                                     │   [score < 7]   │
                                                     │   AND iter < 2  │
                                                     └─────────────────┘
                                                                       │
                                                          [score ≥ 7] → END
```

| 노드 | 역할 |
|------|------|
| **Writer** | 도구 결과를 종합해 답변 작성 (revision_feedback 받으면 재작성) |
| **Critic** | 답변을 1~10점으로 평가 + 구체적 issues/suggestions 반환 |

## Critic 평가 기준

1. **도구 결과 활용도** — 수집된 정보를 모두 반영했는가? (가장 중요)
2. **사실 정확성** — 환각 또는 잘못된 추론 없는가?
3. **답변 구조** — 사용자 질문에 직접 답하는가? Markdown 활용?
4. **누락** — 사용자가 물어본 항목 중 빠뜨린 게 있는가?

| 점수 | 의미 |
|------|------|
| 10 | 완벽 |
| 7~9 | 통과 (작은 보완만 필요) |
| 4~6 | 재작성 필요 (사실 오류 또는 도구 결과 누락) |
| 1~3 | 심각한 문제 (환각 또는 도구 결과 무시) |

설정값 (`agents/critic.py`):
- `PASS_THRESHOLD = 7` — 통과 기준
- `MAX_REVISIONS = 2` — Writer 재호출 최대 횟수

## SSE 이벤트 (9주차에서 추가)

| 이벤트 | 데이터 |
|--------|------|
| `writer_iteration` | `{iteration, is_revision}` — Writer 호출 시작 |
| `revision_start` | `{iteration}` — 재작성 모드 진입 |
| `critic_score` | `{score, passed, issues, suggestions, iteration}` |
| `done` | `{final_score, iterations}` |

## 실행

```bash
# 백엔드
cd backend
py -m pip install -r requirements.txt
py -m uvicorn main:app --reload --port 8000

# 프론트엔드
cd frontend
npm install
npm run dev
```

## 9주차 → 10주차 변화

| 항목 | 9주차 | 10주차 |
|------|------|------|
| 그래프 노드 | 10개 | **11개** (+ Critic) |
| 답변 검증 | 없음 | **Critic 1~10점 채점** |
| 재작성 | 없음 | **자동 (최대 2회)** |
| 사용자 신뢰성 | 답변 그대로 노출 | 점수 < 7이면 자동 개선 후 노출 |

## 핵심 학습 포인트

1. **조건부 루프** — `add_conditional_edges`로 graph cycle 만들기
2. **재귀 한계** — `MAX_REVISIONS`로 무한 루프 방지
3. **상태 누적** — `iteration` 카운트 + 이전 critique 보존
4. **JSON Mode** — Critic의 정형화된 점수 추출
5. **피드백 루프** — Writer가 이전 draft + critique를 받아 재작성
