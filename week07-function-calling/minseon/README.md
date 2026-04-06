# 7주차: Function Calling - minseon

## 기술 스택
| 항목 | 선택 | 대안 | 선택 이유 |
|------|------|------|----------|
| LLM | GPT-4o-mini | Claude, Gemini | OpenAI Function Calling 공식 지원 |
| 함수 스키마 | JSON Schema | Pydantic | OpenAI tools 형식 표준 |
| 실행 환경 | Python 3.12 | - | - |

## 핵심 구현

### 주요 로직
```
사용자 질문
  → GPT가 질문 의도 파악
  → tools 목록에서 알맞은 함수 선택 (tool_choice="auto")
  → 함수 실행 (Python)
  → 결과를 GPT에게 전달
  → 최종 자연어 답변 생성
```

### 구현한 함수
| 함수 | 기능 |
|------|------|
| `get_weather(city, unit)` | 도시 날씨 조회 |
| `search_product(keyword, max_price)` | 쇼핑몰 상품 검색 |
| `calculate(expression)` | 사칙연산 계산 |
| `get_exchange_rate(from, to)` | 환율 조회 |

### 코드 실행 방법
```bash
cd week07-function-calling/minseon
pip install -r requirements.txt
python function_calling.py
```

`.env` 파일에 API 키 필요:
```
OPENAI_API_KEY=sk-...
```

## WHY (의사결정 기록)
1. **Q**: 왜 tool_choice="auto"를 선택했는가?
   **A**: 모델이 스스로 함수 호출 여부를 판단하도록 해야 일반 질문(파이썬이 뭐야?)은 함수 없이 답변하고, 실시간 정보가 필요한 질문만 함수를 호출하는 자연스러운 동작이 가능하기 때문

2. **Q**: 다르게 구현한다면 어떻게 했을까?
   **A**: Pydantic으로 JSON 스키마를 자동 생성하면 타입 안전성이 높아짐. 실제 API(날씨, 환율)를 연동하면 더 실용적인 구현 가능

## 트러블슈팅 로그
| # | 문제 상황 | 에러 메시지 | 원인 | 해결 방법 |
|---|----------|-----------|------|----------|
| 1 | eval() 보안 문제 | - | 임의 코드 실행 가능 | 허용 문자 화이트리스트 적용 |

## 회고
- 이번 주 배운 점: LLM이 단순 텍스트 생성을 넘어 외부 시스템과 연동하는 방법. JSON 스키마 설계가 함수 호출 정확도에 큰 영향을 줌
- 다음 주 준비할 것: ReAct 패턴 - 함수 호출을 반복적으로 수행하며 복잡한 문제 해결



# 1. 폴더 이동
cd c:\Users\user\ai_study\week07-function-calling\minseon\fastapi-react\backend

# 2. 가상환경 활성화
venv312\Scripts\activate

# 3. 서버 실행
uvicorn server:app --reload
