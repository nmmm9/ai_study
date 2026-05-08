"""
4주차 과제: RAG 파이프라인 - Streamlit 웹 인터페이스 (고도화 버전)

[고도화 포인트]
  1. 시작 시 data/ 폴더 자동 인덱싱
  2. 출처 정보를 카드 형태로 표시
  3. 파이프라인 동작 방식 설명 탭
  4. 프롬프트 설계 내용 공개 탭
  5. 검색 과정 단계별 시각화
"""

import os
import tempfile

import streamlit as st

from rag_pipeline import CHAT_MODEL, EMBEDDING_MODEL, RagPipeline, SYSTEM_PROMPT_TEMPLATE

# ── 페이지 설정 ────────────────────────────────────────────────
st.set_page_config(page_title="청년정책 RAG 챗봇", page_icon="🔍", layout="wide")


# ── 출처 카드 렌더링 함수 ──────────────────────────────────────

def render_source_cards(hits: list[dict]):
    """출처 정보를 카드 + 펼치기 형태로 렌더링"""
    st.markdown(f"**참조한 출처 ({len(hits)}개)**")
    cols = st.columns(min(len(hits), 3))
    for i, (col, hit) in enumerate(zip(cols, hits)):
        source    = hit["metadata"]["source"]
        sim       = hit["similarity"]
        chunk_idx = hit["metadata"]["chunk_index"]
        preview   = hit["content"][:120].replace("\n", " ")
        with col:
            st.markdown(f"""
<div style="border:1px solid #e5e7eb;border-radius:8px;padding:10px;font-size:13px;">
  <div style="font-weight:700;color:#2563eb;">{source}</div>
  <div style="color:#6b7280;font-size:11px;">유사도: {sim:.1%} · 청크 #{chunk_idx}</div>
  <div style="margin-top:6px;color:#374151;">{preview}...</div>
</div>""", unsafe_allow_html=True)

    with st.expander("전체 청크 내용 보기"):
        for i, hit in enumerate(hits):
            st.markdown(
                f"**[{i+1}] {hit['metadata']['source']}** — 유사도 {hit['similarity']:.1%}"
            )
            st.text(hit["content"])
            st.divider()


# ── 세션 상태 초기화 ───────────────────────────────────────────
if "rag" not in st.session_state:
    st.session_state.rag = RagPipeline()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "total_tokens" not in st.session_state:
    st.session_state.total_tokens = {"input": 0, "output": 0}
if "auto_indexed" not in st.session_state:
    st.session_state.auto_indexed = False

rag: RagPipeline = st.session_state.rag

# ── 자동 인덱싱 (최초 1회) ─────────────────────────────────────
if not st.session_state.auto_indexed:
    with st.spinner("data/ 폴더 자동 인덱싱 중..."):
        results = rag.auto_index_data_dir()
    if results:
        st.toast(f"✅ {len(results)}개 파일 자동 인덱싱 완료!")
    st.session_state.auto_indexed = True

# ── 사이드바 ───────────────────────────────────────────────────
with st.sidebar:
    st.title("🔍 청년정책 RAG 챗봇")
    st.caption("4주차: RAG 파이프라인 고도화")
    st.divider()

    # ── 문서 업로드 & 인덱싱 ──────────────────────────────────
    st.subheader("📂 문서 인덱싱")
    uploaded = st.file_uploader(
        "문서 업로드",
        type=["md", "txt", "pdf"],
        label_visibility="collapsed",
    )
    if uploaded:
        if st.button("인덱싱 시작", type="primary", use_container_width=True):
            suffix = os.path.splitext(uploaded.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded.read())
                tmp_path = tmp.name
            with st.spinner(f"'{uploaded.name}' 처리 중..."):
                result = rag.index_document(tmp_path, source_name=uploaded.name)
            os.remove(tmp_path)
            st.success(f"완료! {result['chunks']}개 청크 ({result['chars']:,}자)")
            st.rerun()

    st.divider()

    # ── 인덱싱된 문서 목록 ────────────────────────────────────
    st.subheader("📚 인덱싱된 문서")
    sources = rag.get_indexed_sources()
    if sources:
        for src in sources:
            col1, col2 = st.columns([3, 1])
            col1.markdown(f"**{src['source']}**  \n`{src['chunks']}개 청크`")
            if col2.button("삭제", key=f"del_{src['source']}", use_container_width=True):
                rag.delete_source(src["source"])
                st.rerun()
    else:
        st.caption("인덱싱된 문서 없음")

    st.divider()

    # ── 검색 설정 ─────────────────────────────────────────────
    st.subheader("⚙️ 검색 설정")
    top_k = st.slider("top-k (가져올 청크 수)", 1, 8, 5,
                      help="질문과 유사한 청크를 몇 개 가져올지")
    threshold = st.slider("유사도 임계값", 0.0, 1.0, 0.2, step=0.05,
                          help="이 값 미만의 청크는 결과에서 제외")
    max_per_source = st.slider("문서당 최대 청크", 1, 3, 2,
                               help="같은 문서에서 최대 몇 개까지 (소스 다양성)")
    show_sources = st.checkbox("출처 카드 표시", value=True)
    show_process = st.checkbox("검색 과정 표시", value=False)

    st.divider()

    # ── 통계 ──────────────────────────────────────────────────
    st.subheader("📊 통계")
    stats = rag.get_stats()
    col1, col2 = st.columns(2)
    col1.metric("총 문서", f"{stats['total_documents']}개")
    col2.metric("총 청크", f"{stats['total_chunks']}개")

    total = st.session_state.total_tokens
    st.caption(
        f"누적 토큰  입력: {total['input']:,} / 출력: {total['output']:,}  "
        f"(합계: {total['input'] + total['output']:,})"
    )
    st.caption(f"임베딩: `{EMBEDDING_MODEL}`  |  채팅: `{CHAT_MODEL}`")

    st.divider()
    if st.button("대화 초기화", use_container_width=True):
        st.session_state.messages = []
        rag.reset_conversation()
        st.session_state.total_tokens = {"input": 0, "output": 0}
        st.rerun()

# ── 메인 화면: 탭 구성 ─────────────────────────────────────────
tab_chat, tab_pipeline, tab_prompt = st.tabs(["💬 챗봇", "⚙️ 파이프라인 동작 방식", "📝 프롬프트 설계"])

# ════════════════════════════════════════════════════════════
# 탭 1: 챗봇
# ════════════════════════════════════════════════════════════
with tab_chat:
    st.header("📖 청년 정책 RAG 챗봇")
    st.caption("청년 주거·취업·금융·교육·복지 정책을 질문하세요. 출처 문서를 함께 보여드립니다.")

    if not sources:
        st.info("왼쪽 사이드바에서 문서를 업로드하거나, data/ 폴더에 파일을 넣고 재시작하세요.")

    # 이전 대화 출력
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg.get("hits") and show_sources:
                render_source_cards(msg["hits"])

    # 사용자 입력
    user_input = st.chat_input(
        "질문을 입력하세요... (예: 청년도약계좌 조건이 뭐야?)" if sources
        else "먼저 사이드바에서 문서를 업로드해주세요",
        disabled=not sources,
    )

    if user_input:
        # 1. 사용자 메시지
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        # 2. 검색 과정 표시 (옵션)
        if show_process:
            with st.expander("🔎 검색 과정", expanded=True):
                with st.spinner("벡터 유사도 검색 중..."):
                    preview_hits = rag.search(
                        user_input,
                        top_k=top_k,
                        threshold=threshold,
                        max_per_source=max_per_source,
                    )
                st.markdown(f"**검색 결과: {len(preview_hits)}개 청크 발견**")
                for i, h in enumerate(preview_hits):
                    st.markdown(
                        f"- `[{i+1}]` **{h['metadata']['source']}** "
                        f"— 유사도 {h['similarity']:.1%}"
                    )

        # 3. 어시스턴트 응답 (스트리밍)
        with st.chat_message("assistant"):
            full_response = st.write_stream(
                rag.chat_stream(
                    user_input,
                    top_k=top_k,
                    threshold=threshold,
                    max_per_source=max_per_source,
                )
            )
            hits_result  = getattr(rag, "_last_hits", [])
            usage_result = getattr(rag, "_last_usage", {"input": 0, "output": 0})

            if hits_result and show_sources:
                render_source_cards(hits_result)

        # 4. 토큰 + 히스토리 저장
        st.session_state.total_tokens["input"]  += usage_result.get("input", 0)
        st.session_state.total_tokens["output"] += usage_result.get("output", 0)
        st.session_state.messages.append({
            "role":    "assistant",
            "content": full_response,
            "hits":    hits_result,
        })

# ════════════════════════════════════════════════════════════
# 탭 2: 파이프라인 동작 방식
# ════════════════════════════════════════════════════════════
with tab_pipeline:
    st.header("⚙️ 이 챗봇은 어떻게 작동하나요?")
    st.caption("RAG(Retrieval-Augmented Generation) 파이프라인 구조를 단계별로 설명합니다.")

    st.markdown("""
```
[사용자 질문]
     ↓
[임베딩] 질문 → 숫자 벡터 변환 (text-embedding-3-small)
     ↓
[검색] 벡터DB에서 코사인 유사도 계산 → 상위 k개 청크 선택
     ↓  (소스 다양성: 같은 문서 최대 2개)
[주입] 검색된 청크를 [출처: 파일명] 형식으로 시스템 프롬프트에 삽입
     ↓
[생성] GPT-4o-mini → 대화 히스토리 + 참고 문서 기반 스트리밍 답변
     ↓
[출력] 답변 + 출처 카드
```
""")

    st.divider()

    info = rag.get_pipeline_info()
    for step_info in info["steps"]:
        with st.expander(f"**{step_info['step']}**", expanded=True):
            st.markdown(f"**{step_info['desc']}**")
            st.code(step_info["detail"], language=None)

    st.divider()
    st.subheader("핵심 개념")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
**임베딩 (Embedding)**
- 텍스트 → 고차원 숫자 벡터 변환
- 의미 유사 텍스트 → 벡터 공간에서 가까운 위치
- 모델: `text-embedding-3-small` (1536차원)

**코사인 유사도**
- 두 벡터 사이의 각도로 유사도 측정
- 범위: -1 ~ 1 (1에 가까울수록 유사)
- 임계값 0.2 이상만 결과에 포함
        """)
    with col2:
        st.markdown("""
**소스 다양성 (Source Diversity)**
- 같은 문서에서 최대 2개 청크만 선택
- 특정 문서 독점 방지
- 다양한 출처에서 균형 있게 정보 수집

**Sliding Window (대화 히스토리)**
- 최근 10쌍 유지, 오래된 대화 자동 제거
- 토큰 비용 절감 + 최신 맥락 우선 보존
        """)

# ════════════════════════════════════════════════════════════
# 탭 3: 프롬프트 설계
# ════════════════════════════════════════════════════════════
with tab_prompt:
    st.header("📝 프롬프트 설계")
    st.caption("LLM에게 어떻게 역할과 규칙을 지시하는지 확인하세요.")

    st.subheader("시스템 프롬프트 구조")
    st.markdown("""
| 구성 요소 | 내용 | 목적 |
|---------|------|-----|
| **역할 (Persona)** | "청년 정책 전문 AI 상담사 '청년도우미'" | AI 전문성 설정 |
| **동작 방식 설명** | RAG 4단계 설명 | AI가 자신의 동작을 이해하도록 |
| **답변 규칙** | 문서 기반, 출처 표시, 모를 땐 솔직히 | 환각(hallucination) 방지 |
| **출처 표시 규칙** | `[출처: 파일명]` 형식 명시 | 신뢰도 향상, 추적 가능성 |
| **답변 형식** | 핵심 → 조건 → 내용 → 신청방법 | 구조화된 응답 유도 |
| **컨텍스트 주입** | `{context}` 플레이스홀더 | 검색된 문서 청크 삽입 |
""")

    st.divider()
    st.subheader("실제 시스템 프롬프트")
    st.code(SYSTEM_PROMPT_TEMPLATE, language="markdown")

    st.divider()
    st.subheader("컨텍스트 포맷 예시")
    st.code("""[문서 1] 출처: 청년_금융지원_종합.md (유사도: 78.3%)
청년도약계좌는 만 19세~34세 청년이 5년간 월 최대 70만원을 납입하면
정부가 기여금을 지원하는 저축 상품입니다...

---

[문서 2] 출처: 청년_주거지원_종합.md (유사도: 65.1%)
청년 월세 한시 특별지원은 보증금 없이 월세로 거주하는 청년에게
매월 최대 20만원을 최장 12개월간 지원합니다...""", language="text")

    st.info("각 청크에 파일명과 유사도를 명시 → LLM이 **[출처: 파일명]**을 답변에 자연스럽게 포함")
