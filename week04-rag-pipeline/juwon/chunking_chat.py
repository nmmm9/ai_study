"""
1주차 과제: OpenAI GPT API 연동 - 터미널 챗봇
2주차 확장: PDF/Markdown 로드 및 텍스트 청킹 전략
GPT-4o-mini를 활용한 1:1 대화 + Streaming + 토큰 관리
"""

import re
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).parent / ".env")


# ── 문서 로더 (2주차) ─────────────────────────────────────

class DocumentLoader:
    """PDF / Markdown 파일에서 텍스트 추출"""

    @staticmethod
    def load(path: str) -> str:
        ext = Path(path).suffix.lower()
        if ext == ".md":
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        elif ext == ".pdf":
            try:
                import pypdf  # type: ignore
            except ImportError:
                raise ImportError("PDF 로드에는 pypdf가 필요합니다: pip install pypdf")
            reader = pypdf.PdfReader(path)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        else:
            raise ValueError(f"지원하지 않는 형식: {ext}  (.md, .pdf 만 지원)")


# ── 텍스트 청커 (2주차) ───────────────────────────────────

class TextChunker:
    """
    텍스트 분할 전략 3가지:

    fixed      - 글자 수 기준 고정 크기 분할 + overlap
    separator  - 구분자(\n\n → \n → '. ' → ' ') 기반 재귀 분할
    paragraph  - 빈 줄 기준 단락 분할 (취업공고처럼 항목이 나뉜 문서에 적합)
    """

    STRATEGIES = ("fixed", "separator", "paragraph")

    def __init__(self, strategy: str = "paragraph", chunk_size: int = 500, overlap: int = 50):
        if strategy not in self.STRATEGIES:
            raise ValueError(f"전략은 {self.STRATEGIES} 중 하나여야 합니다.")
        self.strategy = strategy
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        dispatch = {
            "fixed":     self._fixed,
            "separator": self._separator,
            "paragraph": self._paragraph,
        }
        return dispatch[self.strategy](text)

    # ── 전략 1: 고정 크기 + overlap ──────────────────────────

    def _fixed(self, text: str) -> list[str]:
        """
        글자 수 기준으로 chunk_size만큼 자르되,
        overlap만큼 이전 청크와 겹쳐서 문맥 단절을 줄임.

        예) chunk_size=500, overlap=50 이면
            0~500 / 450~950 / 900~1400 ...
        """
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            piece = text[start:end].strip()
            if piece:
                chunks.append(piece)
            if end == len(text):
                break
            start += self.chunk_size - self.overlap
        return chunks

    # ── 전략 2: 구분자 기반 재귀 분할 ────────────────────────

    def _separator(self, text: str) -> list[str]:
        """
        구분자 우선순위: \n\n → \n → '. ' → ' '
        chunk_size 이하가 될 때까지 더 작은 구분자로 재귀 분할.
        langchain RecursiveCharacterTextSplitter와 같은 원리를 직접 구현.
        """
        return self._recursive_split(text.strip(), ["\n\n", "\n", ". ", " "])

    def _recursive_split(self, text: str, separators: list[str]) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        sep = separators[0]
        next_seps = separators[1:]
        parts = text.split(sep)

        chunks = []
        current = ""

        for part in parts:
            candidate = current + (sep if current else "") + part
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    # 현재 버퍼가 아직 크면 더 잘게 재귀 분할
                    if len(current) > self.chunk_size and next_seps:
                        chunks.extend(self._recursive_split(current, next_seps))
                    else:
                        chunks.append(current.strip())
                current = part

        if current:
            if len(current) > self.chunk_size and next_seps:
                chunks.extend(self._recursive_split(current, next_seps))
            else:
                chunks.append(current.strip())

        return [c for c in chunks if c]

    # ── 전략 3: 단락(빈 줄) 기준 분할 ───────────────────────

    def _paragraph(self, text: str) -> list[str]:
        """
        빈 줄(\n\n)을 기준으로 단락을 모으되,
        chunk_size를 넘으면 새 청크를 시작.
        취업공고처럼 '주요업무', '자격요건' 같은 항목 단위가 자연스럽게 유지됨.
        """
        paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

        chunks = []
        current = ""

        for para in paras:
            candidate = current + ("\n\n" if current else "") + para
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                # 단락 자체가 chunk_size를 초과해도 그대로 유지 (의미 단위 보존)
                current = para

        if current:
            chunks.append(current)

        return chunks


# ── ChatBot (1주차 유지 + 2주차 확장) ────────────────────────

class ChatBot:
    """OpenAI GPT 기반 터미널 챗봇 (2주차: 문서 컨텍스트 질의응답 지원)"""

    MODEL = "gpt-4o-mini"
    SYSTEM_PROMPT = (
        "당신은 친절한 취업 상담 AI입니다. "
        "제공된 취업공고 내용을 바탕으로 질문에 한국어로 답변합니다. "
        "문서에 없는 내용은 없다고 솔직하게 말해주세요."
    )
    MAX_HISTORY_TURNS = 10
    MAX_RESPONSE_TOKENS = 1024

    def __init__(self):
        self.client = OpenAI()
        self.history: list[dict] = []
        self.token_usage = {"input": 0, "output": 0}
        # 2주차 추가 필드
        self._raw_text: str = ""          # 원본 텍스트 (전략 변경 시 재청킹용)
        self.chunks: list[str] = []
        self.chunker: TextChunker | None = None

    # ── 히스토리 관리 (1주차) ──────────────────────────────

    def _trim_history(self):
        """오래된 대화 제거: 최근 N턴(user+assistant 쌍)만 유지"""
        max_messages = self.MAX_HISTORY_TURNS * 2
        if len(self.history) > max_messages:
            self.history = self.history[-max_messages:]

    def _build_messages(self, context: str = "") -> list[dict]:
        """system + (선택적 문서 컨텍스트) + history"""
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        if context:
            messages.append({"role": "system", "content": context})
        messages.extend(self.history)
        return messages

    # ── 스트리밍 공통 로직 (1주차 리팩토링) ────────────────

    def _stream(self, messages: list[dict]) -> tuple[str, int, int]:
        """스트리밍 API 호출 → (응답 텍스트, 입력토큰, 출력토큰)"""
        reply = ""
        input_tokens = output_tokens = 0

        stream = self.client.chat.completions.create(
            model=self.MODEL,
            max_tokens=self.MAX_RESPONSE_TOKENS,
            messages=messages,
            stream=True,
            stream_options={"include_usage": True},
        )

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                text = chunk.choices[0].delta.content
                print(text, end="", flush=True)
                reply += text
            if chunk.usage:
                input_tokens = chunk.usage.prompt_tokens
                output_tokens = chunk.usage.completion_tokens

        print()
        return reply, input_tokens, output_tokens

    def _record(self, reply: str, in_tok: int, out_tok: int):
        """히스토리 저장 + 토큰 누적"""
        self.token_usage["input"] += in_tok
        self.token_usage["output"] += out_tok
        print(f"  [토큰: 입력 {in_tok} / 출력 {out_tok}]")
        self.history.append({"role": "assistant", "content": reply})

    # ── 일반 대화 (1주차) ──────────────────────────────────

    def send(self, user_input: str) -> str:
        """문서 없이 일반 대화"""
        self.history.append({"role": "user", "content": user_input})
        self._trim_history()
        reply, in_tok, out_tok = self._stream(self._build_messages())
        self._record(reply, in_tok, out_tok)
        return reply

    # ── 문서 기반 대화 (2주차) ─────────────────────────────

    def load_document(self, path: str, strategy: str = "paragraph") -> int:
        """문서 로드 + 청킹 → 청크 수 반환"""
        self._raw_text = DocumentLoader.load(path)
        self.chunker = TextChunker(strategy=strategy, chunk_size=500, overlap=50)
        self.chunks = self.chunker.chunk(self._raw_text)
        return len(self.chunks)

    def change_strategy(self, strategy: str) -> int:
        """청킹 전략만 바꿔서 기존 문서를 재청킹 → 청크 수 반환"""
        if not self._raw_text:
            raise RuntimeError("먼저 문서를 로드하세요 (load <파일경로>).")
        self.chunker = TextChunker(strategy=strategy, chunk_size=500, overlap=50)
        self.chunks = self.chunker.chunk(self._raw_text)
        return len(self.chunks)

    def _find_relevant_chunks(self, query: str, top_k: int = 3) -> list[str]:
        """
        키워드 단순 매칭으로 관련 청크 상위 top_k개 반환.
        (임베딩 기반 유사도 검색은 3주차에서 다룸)
        """
        if not self.chunks:
            return []
        keywords = query.split()
        scored = sorted(
            ((sum(chunk.lower().count(kw.lower()) for kw in keywords), chunk)
             for chunk in self.chunks),
            reverse=True,
        )
        return [chunk for score, chunk in scored[:top_k] if score > 0]

    def send_with_context(self, user_input: str) -> str:
        """관련 청크를 system 메시지에 주입 후 질의응답 (히스토리엔 원본 질문만 저장)"""
        relevant = self._find_relevant_chunks(user_input)

        context = ""
        if relevant:
            joined = "\n\n---\n\n".join(relevant)
            context = f"아래는 관련 취업공고 내용입니다:\n\n{joined}"
            print(f"  [참조 청크: {len(relevant)}개]")

        self.history.append({"role": "user", "content": user_input})
        self._trim_history()
        reply, in_tok, out_tok = self._stream(self._build_messages(context))
        self._record(reply, in_tok, out_tok)
        return reply

    # ── 유틸리티 ──────────────────────────────────────────

    def print_chunks(self):
        """현재 청크 목록 미리보기 출력"""
        if not self.chunks:
            print("  로드된 문서가 없습니다. 'load <파일경로>' 를 먼저 실행하세요.\n")
            return
        strategy = self.chunker.strategy if self.chunker else "?"
        print(f"\n── 청크 목록 (전략: {strategy} | 총 {len(self.chunks)}개) ──")
        for i, chunk in enumerate(self.chunks, 1):
            preview = chunk[:60].replace("\n", " ")
            print(f"  [{i:02d}] {len(chunk):4d}자  {preview}...")
        print()

    def reset(self):
        """대화 히스토리 초기화"""
        self.history.clear()

    def print_usage(self):
        """누적 토큰 사용량 출력"""
        total = self.token_usage["input"] + self.token_usage["output"]
        print(f"\n── 누적 토큰 사용량 ──")
        print(f"  입력:  {self.token_usage['input']} 토큰")
        print(f"  출력:  {self.token_usage['output']} 토큰")
        print(f"  합계:  {total} 토큰")
        print(f"  대화:  {len(self.history) // 2}턴\n")


# ── 메인 루프 ─────────────────────────────────────────────

def main():
    bot = ChatBot()

    print("┌──────────────────────────────────────────┐")
    print("│   GPT-4o-mini 취업공고 챗봇 (2주차)     │")
    print("├──────────────────────────────────────────┤")
    print("│  load <경로> [전략]  → 문서 로드         │")
    print("│  chunks              → 청크 목록 확인    │")
    print("│  strategy <전략>     → 청킹 전략 변경    │")
    print("│  reset / usage / quit                    │")
    print("└──────────────────────────────────────────┘")
    print("  청킹 전략: fixed | separator | paragraph\n")

    while True:
        try:
            user_input = input("나: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n종료합니다.")
            bot.print_usage()
            break

        if not user_input:
            continue

        # 명령어 파싱
        tokens = user_input.split()
        cmd = tokens[0].lower()

        if cmd == "quit":
            bot.print_usage()
            print("종료합니다.")
            break

        elif cmd == "reset":
            bot.reset()
            print("대화를 초기화했습니다.\n")

        elif cmd == "usage":
            bot.print_usage()

        elif cmd == "chunks":
            bot.print_chunks()

        elif cmd == "load":
            # 사용법: load <경로> [전략]
            if len(tokens) < 2:
                print("  사용법: load <파일경로> [fixed|separator|paragraph]\n")
                continue
            raw_path = tokens[1]
            # 파일을 현재 경로에서 못 찾으면 스크립트 옆 폴더에서도 탐색
            path = raw_path
            if not Path(path).exists():
                alt = Path(__file__).parent / raw_path
                if alt.exists():
                    path = str(alt)
            strategy = tokens[2].lower() if len(tokens) >= 3 else "paragraph"
            if strategy not in TextChunker.STRATEGIES:
                print(f"  지원 전략: {TextChunker.STRATEGIES}\n")
                continue
            try:
                count = bot.load_document(path, strategy)
                print(f"  문서 로드 완료: {Path(path).name}")
                print(f"  청킹 전략: {strategy}  |  청크 수: {count}개\n")
            except Exception as e:
                print(f"  오류: {e}\n")

        elif cmd == "strategy":
            # 사용법: strategy <전략>
            if len(tokens) < 2:
                print(f"  사용법: strategy <{'|'.join(TextChunker.STRATEGIES)}>\n")
                continue
            strategy = tokens[1].lower()
            if strategy not in TextChunker.STRATEGIES:
                print(f"  지원 전략: {TextChunker.STRATEGIES}\n")
                continue
            try:
                count = bot.change_strategy(strategy)
                print(f"  전략 변경: {strategy}  |  청크 수: {count}개\n")
            except RuntimeError as e:
                print(f"  {e}\n")

        else:
            print("AI: ", end="")
            if bot.chunks:
                bot.send_with_context(user_input)
            else:
                bot.send(user_input)
            print()


if __name__ == "__main__":
    main()
