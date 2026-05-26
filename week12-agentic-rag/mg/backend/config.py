"""Model routing config — Balanced tier (week09)

Supervisor: cheap routing (JSON only)  → nano
Domain agents: tool-call accuracy needed → mini
Writer: final answer quality            → mini

가격 시점에 따라 실제 사용 가능한 모델로 폴백. 기본은 안정적으로 동작하는
gpt-4o-mini로 두고, 5.x 계열은 환경변수나 프론트 드롭다운에서 선택.
"""

import os

# Default to models known to exist on OpenAI API.
# Override via env: MODEL_SUPERVISOR, MODEL_DOMAIN, MODEL_WRITER
SUPERVISOR_MODEL = os.environ.get("MODEL_SUPERVISOR", "gpt-4o-mini")
DOMAIN_MODEL = os.environ.get("MODEL_DOMAIN", "gpt-4o-mini")
WRITER_MODEL = os.environ.get("MODEL_WRITER", "gpt-4o-mini")
