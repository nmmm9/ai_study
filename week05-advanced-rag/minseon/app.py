"""
5주차: Advanced RAG - Streamlit 웹 인터페이스

[4주차 대비 개선된 시각화]
  - Pre-retrieval: 생성된 Multi-query 목록 표시
  - Retrieval: Hybrid Search (BM25 + Vector) 결과 표시
  - Post-retrieval: Re-ranking 전후 순위 변화, 압축 여부 표시
  - 단계별 소요 시간 추적 (파이프라인 병목 파악)
"""

import os
import tempfile

import streamlit as st

from rag_pipeline import AdvancedRagPipeline, CHAT_MODEL, EMBEDDING_MODEL, SYSTEM_PROMPT_TEMPLATE

# ── 페이지 설정 ────────────────────────────────────────────────
st.set_page_config(page_title="Advanced RAG 챗봇", page_icon="🚀", layout="wide")


# ── 출처 카드 렌더링 ───────────────────────────────────────────

def render_source_cards(hits: list[dict]):
    st.markdown(f"**참조한 출처 ({len(hits)}개)**")
    cols = st.columns(min(len(hits), 3))
    for col, hit in zip(cols, hits):
        source    = hit["metadata"]["source"]
        sim       = hit["similarity"]
        chunk_idx = hit["metadata"]["chunk_index"]
        preview   = hit["content"][:120].replace("\n", " ")
        compressed_badge = " 🗜️압축" if hit.get("compressed") else ""
        with col:
            st.markdown(f"""
<div style="border:1px solid #e5e7eb;border-radius:8px;padding:10px;font-size:13px;">
  <div style="font-weight:700;color:#2563eb;">{source}{compressed_badge}</div>
  <div style="color:#6b7280;font-size:11px;">유사도: {sim:.1%} · 청크 #{chunk_idx}</div>
  <div style="margin-top:6px;color:#374151;">{preview}...</div>
</div>""", unsafe_allow_html=True)

    with st.expander("전체 청크 내용 보기"):
        for i, hit in enumerate(hits):
            compressed_marker = " [압축됨]" if hit.get("compressed") else ""
            st.markdown(
                f"**[{i+1}] {hit['metadata']['source']}**"
                f" — 유사도 {hit['similarity']:.1%}{compressed_marker}"
            )
            st.text(hit["content"])
            st.divider()


# ── 파이프라인 단계 시각화 (비용·시간 포함) ──────────────────────

_STAGE_LABELS = {
    "pre":         ("①", "Pre-retrieval",  "Multi-query Generation"),
    "embedding":   ("②", "Retrieval",      "Hybrid Search 임베딩"),
    "reranking":   ("③", "Post-retrieval", "GPT Re-ranking"),
    "compression": ("③", "Post-retrieval", "Context Compression"),
    "generation":  ("④", "Generation",     "LLM 스트리밍"),
}

def render_pipeline_process(rag: AdvancedRagPipeline):
    """Advanced RAG 각 단계 결과 + 비용·시간 시각화"""
    cost = rag._last_cost_summary
    by_stage = cost.get("by_stage", {})

    with st.expander("🔬 Advanced RAG 파이프라인 실행 결과", expanded=True):

        # ── ① Pre-retrieval ─────────────────────────────────
        pre = by_stage.get("pre", {})
        st.markdown(f"#### ① Pre-retrieval: Multi-query Generation")
        c1, c2, c3 = st.columns(3)
        c1.metric("소요 시간", f"{pre.get('elapsed', 0):.2f}s")
        c2.metric("토큰", f"{pre.get('input_tokens', 0):,}")
        c3.metric("비용", f"${pre.get('cost_usd', 0):.5f}")
        for i, q in enumerate(rag._last_queries):
            st.markdown(f"`쿼리 {i+1}` {q}")

        st.divider()

        # ── ② Retrieval ─────────────────────────────────────
        emb = by_stage.get("embedding", {})
        candidates = rag._last_candidates
        st.markdown("#### ② Retrieval: Hybrid Search (BM25 + Vector)")
        c1, c2, c3 = st.columns(3)
        c1.metric("소요 시간", f"{cost.get('stage_times', {}).get('retrieval', emb.get('elapsed', 0)):.2f}s")
        c2.metric("임베딩 토큰", f"{emb.get('input_tokens', 0):,}")
        c3.metric("비용", f"${emb.get('cost_usd', 0):.5f}")
        st.markdown(f"**{len(rag._last_queries)}개 쿼리** × Hybrid Search → **{len(candidates)}개 후보** 수집")
        for i, hit in enumerate(candidates[:6]):
            st.markdown(f"- `[{i+1}]` **{hit['metadata']['source']}** — {hit['similarity']:.1%}")
        if len(candidates) > 6:
            st.caption(f"... 외 {len(candidates)-6}개")

        st.divider()

        # ── ③ Post-retrieval ─────────────────────────────────
        rer = by_stage.get("reranking", {})
        cmp = by_stage.get("compression", {})
        post_cost = rer.get("cost_usd", 0) + cmp.get("cost_usd", 0)
        post_elapsed = cost.get("stage_times", {}).get("post", rer.get("elapsed", 0) + cmp.get("elapsed", 0))
        hits = rag._last_hits
        compressed = rag._last_compressed
        compressed_count = sum(1 for h in compressed if h.get("compressed"))

        st.markdown("#### ③ Post-retrieval: Re-ranking + Compression")
        c1, c2, c3 = st.columns(3)
        c1.metric("소요 시간", f"{post_elapsed:.2f}s")
        c2.metric("API 호출", f"{rer.get('calls',0)+cmp.get('calls',0)}회")
        c3.metric("비용", f"${post_cost:.5f}")
        st.markdown(f"Re-ranking: {len(candidates)}개 → **{len(hits)}개** 선별  |  압축 적용: **{compressed_count}개**")
        for i, hit in enumerate(hits):
            c_marker = " 🗜️" if hit.get("compressed") else ""
            st.markdown(f"- `[{i+1}]` **{hit['metadata']['source']}** — {hit['similarity']:.1%}{c_marker}")

        st.divider()

        # ── ④ Generation ────────────────────────────────────
        gen = by_stage.get("generation", {})
        st.markdown("#### ④ Generation: LLM 스트리밍")
        c1, c2, c3 = st.columns(3)
        c1.metric("소요 시간", f"{gen.get('elapsed', 0):.2f}s")
        c2.metric("토큰 (입력/출력)", f"{gen.get('input_tokens',0):,} / {gen.get('output_tokens',0):,}")
        c3.metric("비용", f"${gen.get('cost_usd', 0):.5f}")


def render_cost_summary(cost: dict):
    """이번 응답의 비용·시간 요약 카드"""
    if not cost:
        return
    total_usd = cost.get("total_cost_usd", 0)
    total_krw = cost.get("total_cost_krw", 0)
    total_sec = cost.get("total_elapsed", 0)
    total_tok = cost.get("total_input_tokens", 0) + cost.get("total_output_tokens", 0)

    st.markdown(
        f"""<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:6px;">
  <span style="background:#f0fdf4;border:1px solid #86efac;border-radius:8px;padding:3px 10px;font-size:12px;color:#166534;">
    💰 ${total_usd:.5f} (₩{total_krw:.2f})
  </span>
  <span style="background:#eff6ff;border:1px solid #93c5fd;border-radius:8px;padding:3px 10px;font-size:12px;color:#1e40af;">
    ⏱ {total_sec:.1f}s
  </span>
  <span style="background:#faf5ff;border:1px solid #c4b5fd;border-radius:8px;padding:3px 10px;font-size:12px;color:#5b21b6;">
    🔤 {total_tok:,} 토큰
  </span>
</div>""",
        unsafe_allow_html=True,
    )


# ── 세션 상태 초기화 ───────────────────────────────────────────
if "rag" not in st.session_state:
    st.session_state.rag = AdvancedRagPipeline()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "total_tokens" not in st.session_state:
    st.session_state.total_tokens = {"input": 0, "output": 0}
if "total_cost_usd" not in st.session_state:
    st.session_state.total_cost_usd = 0.0
if "auto_indexed" not in st.session_state:
    st.session_state.auto_indexed = False

rag: AdvancedRagPipeline = st.session_state.rag

# ── 자동 인덱싱 ────────────────────────────────────────────────
if not st.session_state.auto_indexed:
    with st.spinner("data/ 폴더 자동 인덱싱 중..."):
        results = rag.auto_index_data_dir()
    if results:
        st.toast(f"✅ {len(results)}개 파일 자동 인덱싱 완료!")
    st.session_state.auto_indexed = True

# ── 사이드바 ───────────────────────────────────────────────────
with st.sidebar:
    st.title("🚀 Advanced RAG 챗봇")
    st.caption("5주차: Advanced RAG 파이프라인")
    st.divider()

    # Advanced RAG 기법 배지
    st.markdown("""
**적용된 Advanced RAG 기법:**
- ✅ Multi-query Generation
- ✅ Hybrid Search (BM25 + Vector)
- ✅ RRF Fusion
- ✅ GPT Re-ranking
- ✅ Context Compression
""")
    st.divider()

    # ── 문서 업로드 ───────────────────────────────────────────
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
    top_k = st.slider("top-k (최종 청크 수)", 1, 8, 5)
    threshold = st.slider("유사도 임계값", 0.0, 1.0, 0.2, step=0.05)
    max_per_source = st.slider("문서당 최대 청크", 1, 3, 2)
    use_compression = st.checkbox("Context Compression 사용", value=True,
                                   help="청크에서 핵심 내용만 추출 (추가 API 호출 발생)")
    show_sources = st.checkbox("출처 카드 표시", value=True)
    show_process = st.checkbox("파이프라인 과정 표시", value=False)

    st.divider()

    # ── 통계 ──────────────────────────────────────────────────
    st.subheader("📊 통계")
    stats = rag.get_stats()
    col1, col2 = st.columns(2)
    col1.metric("총 문서", f"{stats['total_documents']}개")
    col2.metric("총 청크", f"{stats['total_chunks']}개")

    total = st.session_state.total_tokens
    st.caption(f"토큰  입력: {total['input']:,} / 출력: {total['output']:,}")
    total_usd = st.session_state.total_cost_usd
    st.markdown(
        f"<span style='font-size:13px;font-weight:700;color:#166534'>"
        f"누적 비용: ${total_usd:.4f} (₩{total_usd*1380:.1f})</span>",
        unsafe_allow_html=True,
    )
    st.caption(f"임베딩: `{EMBEDDING_MODEL}`  |  채팅: `{CHAT_MODEL}`")

    st.divider()
    if st.button("대화 초기화", use_container_width=True):
        st.session_state.messages = []
        rag.reset_conversation()
        st.session_state.total_tokens = {"input": 0, "output": 0}
        st.session_state.total_cost_usd = 0.0
        st.rerun()


# ── 메인 화면: 탭 ──────────────────────────────────────────────
tab_chat, tab_compare, tab_pipeline = st.tabs([
    "💬 챗봇",
    "📊 Naive vs Advanced RAG",
    "⚙️ 파이프라인 구조",
])

# ════════════════════════════════════════════════════════════
# 탭 1: 챗봇
# ════════════════════════════════════════════════════════════
with tab_chat:
    st.header("🚀 Advanced RAG 챗봇")
    st.caption("청년 주거·취업·금융·교육·복지 정책 질문 | Multi-query + Hybrid Search + Re-ranking + Compression")

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
        "질문을 입력하세요... (예: 청년도약계좌 자격이 뭐야?)" if sources
        else "먼저 사이드바에서 문서를 업로드해주세요",
        disabled=not sources,
    )

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant"):
            full_response = st.write_stream(
                rag.chat_stream(
                    user_input,
                    top_k=top_k,
                    threshold=threshold,
                    max_per_source=max_per_source,
                    use_compression=use_compression,
                )
            )

        hits_result  = rag._last_compressed
        usage_result = rag._last_usage
        cost_summary = rag._last_cost_summary

        # 출처 카드
        if hits_result and show_sources:
            with st.chat_message("assistant"):
                render_source_cards(hits_result)
                render_cost_summary(cost_summary)

        # 파이프라인 단계별 상세 표시
        if show_process:
            render_pipeline_process(rag)

        # 누적 통계 저장
        st.session_state.total_tokens["input"]  += usage_result.get("input", 0)
        st.session_state.total_tokens["output"] += usage_result.get("output", 0)
        st.session_state.total_cost_usd         += cost_summary.get("total_cost_usd", 0)
        st.session_state.messages.append({
            "role":    "assistant",
            "content": full_response,
            "hits":    hits_result,
        })

# ════════════════════════════════════════════════════════════
# 탭 2: Naive vs Advanced RAG 비교
# ════════════════════════════════════════════════════════════
with tab_compare:
    st.header("📊 Naive RAG vs Advanced RAG")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Naive RAG (4주차)")
        st.markdown("""
```
[질문]
  ↓
[임베딩] 질문 → 벡터 변환
  ↓
[벡터 검색] 코사인 유사도 top-k
  ↓
[LLM] 검색 결과 그대로 주입
  ↓
[답변]
```
**한계:**
- 모호한 질문 → 검색 품질 저하
- 벡터 유사도만으로 순위 결정
- 청크 내 노이즈가 그대로 전달
- 단일 검색 방식 (의미론적만)
""")

    with col2:
        st.subheader("Advanced RAG (5주차)")
        st.markdown("""
```
[질문]
  ↓ Pre-retrieval
[Multi-query] 3개 쿼리로 확장
  ↓ Retrieval
[Hybrid Search] BM25 + Vector
  → RRF Fusion으로 결과 병합
  ↓ Post-retrieval
[Re-ranking] GPT로 재평가
[Compression] 핵심 내용 추출
  ↓
[LLM] 정제된 컨텍스트 주입
  ↓
[답변]
```
""")

    st.divider()

    st.subheader("각 기법이 해결하는 문제")

    improvements = [
        {
            "문제 (Naive RAG)": "모호한 질문으로 검색 품질 저하",
            "해결 기법": "Multi-query Generation",
            "원리": "하나의 질문을 3가지 관점으로 확장 → 검색 커버리지 향상",
        },
        {
            "문제 (Naive RAG)": "벡터 유사도 순위가 항상 최적이 아님",
            "해결 기법": "Hybrid Search (BM25 + Vector)",
            "원리": "키워드 정확도 + 의미론적 유사도 동시 활용 → RRF로 최적 병합",
        },
        {
            "문제 (Naive RAG)": "표면적 유사도 함정 (내용 없는 문서가 상위 랭크)",
            "해결 기법": "GPT Re-ranking",
            "원리": "질문+문서를 함께 분석해 실제 관련성 재평가",
        },
        {
            "문제 (Naive RAG)": "청크 내 노이즈가 LLM 컨텍스트 낭비",
            "해결 기법": "Context Compression",
            "원리": "각 청크에서 질문과 직접 관련된 내용만 추출",
        },
    ]

    for item in improvements:
        with st.expander(f"**{item['해결 기법']}** — {item['문제 (Naive RAG)']}"):
            st.markdown(f"**문제:** {item['문제 (Naive RAG)']}")
            st.markdown(f"**해결:** {item['해결 기법']}")
            st.markdown(f"**원리:** {item['원리']}")

# ════════════════════════════════════════════════════════════
# 탭 3: 파이프라인 구조
# ════════════════════════════════════════════════════════════
with tab_pipeline:
    st.header("⚙️ Advanced RAG 파이프라인 구조")

    st.markdown("""
```
사용자 질문
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  Pre-retrieval: query_service.py                        │
│                                                         │
│  Multi-query Generation                                 │
│  "청년도약계좌 조건?" →                                  │
│    쿼리1: "청년도약계좌 가입 자격 나이 소득"               │
│    쿼리2: "청년도약계좌 정부 기여금 지원 금액"              │
│    쿼리3: "청년도약계좌 신청 방법 기간"                    │
└─────────────────────────────────────────────────────────┘
    │ 3개 쿼리
    ▼
┌─────────────────────────────────────────────────────────┐
│  Retrieval: vector_store.py                             │
│                                                         │
│  각 쿼리마다 Hybrid Search 실행                           │
│  ┌──────────────┐   ┌──────────────┐                   │
│  │ BM25 Search  │   │ Vector Search│                   │
│  │ (키워드 정확도)│   │ (의미론적)   │                   │
│  └──────┬───────┘   └──────┬───────┘                   │
│         └────────┬─────────┘                           │
│              RRF Fusion                                 │
│  3개 쿼리 결과 병합 → 중복 제거 → 후보 풀 구성            │
└─────────────────────────────────────────────────────────┘
    │ 후보 청크들 (top_k × 3)
    ▼
┌─────────────────────────────────────────────────────────┐
│  Post-retrieval                                         │
│                                                         │
│  1. Re-ranking (reranker_service.py)                    │
│     GPT가 질문+각 청크를 함께 분석 → 0~10 점수 부여       │
│     → 점수 기준 재정렬 → 최종 top_k 선별                  │
│                                                         │
│  2. Context Compression (compression_service.py)        │
│     각 청크에서 질문과 직접 관련된 내용만 추출             │
│     → 노이즈 제거 + 토큰 절약                            │
└─────────────────────────────────────────────────────────┘
    │ 정제된 컨텍스트
    ▼
┌─────────────────────────────────────────────────────────┐
│  Generation: llm_service.py                             │
│                                                         │
│  시스템 프롬프트 + 대화 히스토리 + 정제된 컨텍스트         │
│  → GPT-4o-mini 스트리밍 응답                            │
└─────────────────────────────────────────────────────────┘
    │
    ▼
  답변 + 출처 카드
```
""")

    st.divider()

    st.subheader("파일 구조")
    st.code("""week05-advanced-rag/minseon/
├── app.py                          # Streamlit UI
├── rag_pipeline.py                 # Advanced RAG 오케스트레이터
├── requirements.txt
└── services/
    ├── query_service.py            # [NEW] Multi-query Generation
    ├── vector_store.py             # [ENHANCED] BM25 + Hybrid Search
    ├── compression_service.py      # [NEW] Context Compression
    ├── reranker_service.py         # GPT Re-ranking
    ├── embedding_service.py        # OpenAI 임베딩
    ├── llm_service.py              # GPT 스트리밍
    ├── chunking_service.py         # 마크다운 구조 기반 청킹
    └── document_service.py         # 문서 로딩 (md/txt/pdf)""", language="text")

    st.divider()
    st.subheader("실제 시스템 프롬프트")
    st.code(SYSTEM_PROMPT_TEMPLATE, language="markdown")
