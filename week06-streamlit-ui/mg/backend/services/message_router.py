"""Message Router — Two-tier routing for RAG chatbot.

Tier 1: Regex catches obvious greetings → skip search entirely (~0ms)
Tier 2: Everything else → quick vector search → check top-1 score
  - score >= 0.55 → full RAG pipeline
  - score < 0.55 → direct LLM (no context)

Why not regex for retrieval indicators too?
  Regex is a maintenance treadmill. A similarity score adapts to any question
  form without code changes. Keep regex ONLY for unambiguous greetings.
"""

import re

TRIVIAL_PATTERNS = [
    re.compile(r"^\s*(안녕|하이|헬로|hi|hello|hey)\s*[!?.~]*\s*$", re.I),
    re.compile(r"^\s*(감사|고마워|고맙|땡큐|thank|thx)\S*.*$", re.I),
    re.compile(r"^\s*(네|응|ㅇㅇ|ㅋ+|ㅎ+|ㅠ+|오케이|ok|알겠|확인|좋아|굿)\s*[!?.~]*\s*$", re.I),
    re.compile(r"^\s*(잘가|바이|bye|수고|안녕히)\S*.*$", re.I),
]

RELEVANCE_THRESHOLD = 0.35


def is_trivial(message: str) -> bool:
    """Tier 1: Fast regex check for obvious greetings/small talk."""
    cleaned = message.strip()
    if not cleaned:
        return True
    return any(p.match(cleaned) for p in TRIVIAL_PATTERNS)
