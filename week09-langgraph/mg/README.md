# Week 09 — LangGraph Multi-Agent

8주차 단일 ReAct 에이전트를 **LangGraph 기반 멀티 에이전트**로 재구성합니다.
한 명의 LLM이 26개 도구를 모두 다루던 구조 → **Supervisor + 4개 도메인 전문 에이전트 + Writer** 의 협업 구조.

## 아키텍처

```
[START] → Supervisor ─┬→ Shopping ──┐
                      ├→ Lifestyle ─┤
                      ├→ Sports ────┼→ Writer → [END]
                      └→ Info ──────┘
```

| 노드 | 역할 |
|------|------|
| **Supervisor** | 질문 분석 후 어떤 도메인 에이전트가 필요한지 결정 (plan: list[str]) |
| **Shopping** | 다이소, 쿠팡, 올리브영, 중고차 등 7개 도구 |
| **Lifestyle** | 택배, 미세먼지, 한강수위, 주유소, 부동산, 우편번호, 지하철, 맛집/술집 등 9개 도구 |
| **Sports** | KBO, K리그, LCK 등 3개 도구 |
| **Info** | 맞춤법, 법률, 조선왕조실록, 로또, 시간/계산 등 7개 도구 |
| **Writer** | 모든 도메인 결과를 종합해 최종 답변을 스트리밍 |

각 도메인 에이전트는 자기 도메인 도구만 LLM에 노출 → 토큰 효율 ↑, 정확도 ↑.

## 실행

### 백엔드

```bash
cd backend
py -m pip install -r requirements.txt
# .env 에 OPENAI_API_KEY 설정
py -m uvicorn main:app --reload --port 8000
```

### 프론트엔드

```bash
cd frontend
npm install
npm run dev
# http://localhost:3000
```

## API

| 엔드포인트 | 설명 |
|------------|------|
| `GET /api/tools` | 도메인별 도구 목록 |
| `GET /api/graph` | 그래프 메타데이터 (노드/엣지) |
| `POST /api/chat/stream` | SSE 스트리밍 — 멀티 에이전트 실행 |

### SSE 이벤트 타입

| type | data |
|------|------|
| `edge` | `{from, to}` — 그래프 엣지 활성화 |
| `node_start` | `{node}` — 노드 실행 시작 |
| `node_end` | `{node, result_summary}` — 노드 실행 종료 |
| `supervisor_decision` | `{plan, reasoning}` — 라우팅 결정 |
| `tool_call` | `{domain, tool, args}` — 도구 호출 |
| `tool_result` | `{domain, tool, result}` — 도구 결과 |
| `token` | string — Writer 답변 토큰 |
| `done` | null — 종료 |

## 8주차와의 차이

| 항목 | 8주차 (ReAct) | 9주차 (LangGraph) |
|------|---------------|-------------------|
| 구조 | 단일 LLM 루프 | StateGraph (노드/엣지) |
| 도구 노출 | 26개 한꺼번에 | 도메인별 5~9개씩 |
| 시스템 프롬프트 | 일반적 | 도메인 특화 |
| 병렬성 | 순차 | 도메인 에이전트 병렬 실행 |
| 시각화 | 캐릭터 무대 | 그래프 노드/엣지 흐름 |

## 코드 구조

```
backend/
├── main.py                  # FastAPI + SSE
├── agents/
│   ├── state.py             # GraphState (TypedDict)
│   ├── supervisor.py        # 라우팅 노드
│   ├── domain_agent.py      # 도메인별 ReAct 미니 루프
│   └── writer.py            # 최종 답변 스트리밍
├── services/
│   └── graph.py             # StateGraph + agent_stream() 파이프라인
└── tools/
    ├── __init__.py          # TOOL_DOMAINS 매핑
    ├── registry.py
    └── *.py                 # 26개 도구 (8주차에서 복제)

frontend/
└── src/
    ├── app/page.tsx         # 메인 (좌: 채팅 / 우: 그래프)
    ├── components/
    │   ├── ChatMessage.tsx  # 에이전트 트레이스 표시
    │   ├── ChatInput.tsx
    │   └── AgentGraph.tsx   # SVG 그래프 + 실시간 하이라이트
    ├── hooks/useChat.ts     # SSE 처리 + graphState
    └── types/chat.ts
```

## 핵심 학습 포인트

1. **StateGraph** — 노드/엣지/state로 워크플로우 정의
2. **Conditional Edge** — Supervisor의 plan에 따른 동적 라우팅
3. **도메인 분리** — 도구 그룹화로 토큰/정확도 최적화
4. **병렬 에이전트** — `asyncio.Queue`로 여러 도메인 결과 인터리브
5. **세분화된 SSE 이벤트** — 그래프 시각화를 위한 node/edge/tool 이벤트
