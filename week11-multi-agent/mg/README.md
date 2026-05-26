# Week 11 — Plan-and-Execute (Multi-Agent)

10주차 Self-Correction에 **Planner / Executor / Replanner** 를 추가해
복잡한 multi-step 질문을 단계별로 분해·실행하고, 도중에 plan 을 수정할 수 있게 합니다.

## 아키텍처

```
[START] → Planner → Executor(step N) → Replanner ─┐
              │       ▲                            │
              │       │  ┌─ continue ──────────────┤
              │       │  ├─ revise (new plan) ─────┘
              │       │  └─ finish ──┐
              │       │                ▼
              │       │            Writer ⇄ Critic
              │       │                       │
              │       │            [pass] ──→ END
              │       └─ (advance to next pending step)
              │
              └─ (빈 plan일 때 바로 Writer)
```

| 노드 | 역할 |
|------|------|
| **Planner** | 질문을 1~6개 step 으로 분해. 각 step 에 도메인 hint |
| **Executor** | 한 step 씩 진행, 해당 도메인 에이전트로 dispatch |
| **Replanner** | 매 step 후 continue / revise / finish 결정 |
| **Domain Agent ×8** | 9주차에서 재사용 (52개 도구) |
| **Writer / Critic** | 10주차에서 재사용 (Self-Correction 루프) |

## 핵심 변화 (10주차 → 11주차)

| 항목 | 10주차 | 11주차 |
|------|------|------|
| 라우팅 | Supervisor 1회 | **Planner + 매 step Replanner** |
| 그래프 모양 | DAG + Critic 루프 1개 | **Cycle 2개** (Execute loop + Critic loop) |
| 복잡 질문 처리 | 단일 라우팅 후 병렬 | **순차 step + 동적 재계획** |
| State 변화 | answer만 변화 | **plan 자체가 진화** (revise) |
| 추가 노드 | Critic | **Planner / Executor / Replanner** |

## SSE 이벤트 (11주차 추가)

| 이벤트 | 데이터 |
|--------|------|
| `plan_created` | `{plan: [Step], reasoning}` |
| `step_start` | `{step: {id, domain, task}}` |
| `step_done` | `{step: {..., tool_count, results_summary}}` |
| `replan_decision` | `{action, reasoning, new_plan?}` |

기존 10주차 이벤트 (writer_iteration, critic_score, token, ...) 모두 유지.

## 실행

```bash
# 백엔드
cd backend
py -m uvicorn main:app --reload --port 8000

# 프론트엔드 (다른 터미널)
cd frontend
npm install
npm run dev
```

http://localhost:3000 접속.

## 검증 (실측)

```
Q: "서울 날씨 + 어제 KBO 결과 + 강남구 맛집까지 한 번에"

  plan: 3 steps
    [1] lifestyle: 서울의 현재 날씨 정보 검색
    [2] sports: 어제 KBO 야구 경기 결과 검색
    [3] lifestyle: 강남구의 맛집 정보 검색
  step 1 done (1 tools) → replan: continue
  step 2 done (1 tools) → replan: continue
  step 3 done (2 tools) → replan: revise  ← 결과가 빈약하다고 판단
  step 4 done (3 tools) → replan: revise
  step 5 done (0 tools) → replan: revise (한도 도달)
  critic: 8/10 passed=True
  done: {final_score: 8, iterations: 1, plan_steps: 5, replan_count: 2}
```

## 설정값

`agents/replanner.py`:
- `MAX_REPLAN = 2` — Replanner가 plan을 revise할 수 있는 최대 횟수

`agents/planner.py`:
- `MAX_STEPS = 6` — Planner가 만들 수 있는 step 최대 개수

`agents/critic.py` (10주차에서 그대로):
- `PASS_THRESHOLD = 7`, `MAX_REVISIONS = 2`

## 핵심 학습 포인트

1. **Plan = first-class state** — plan 자체가 그래프 상태의 일부, 도중에 변형 가능
2. **Step-by-step dispatch** — 한 step씩 진행하면 결과를 다음 plan에 반영 가능
3. **이중 cycle** — Execute loop (replanner→executor) + Critic loop (critic→writer)
4. **동적 재계획** — `revise` 액션으로 plan 진화. 사람의 계획 변경을 모방
5. **복합 질문 분해** — 다중 도메인 질문도 단순 step 의 조합으로 표현
