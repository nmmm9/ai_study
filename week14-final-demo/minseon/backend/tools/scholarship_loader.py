"""
scholarship_loader.py
──────────────────────
한국장학재단 CSV → RAG doc 변환 로더

CSV 위치: database/data/scholarships/*.csv
인코딩:   CP949 (EUC-KR 계열)

컬럼:
  번호 / 운영기관명 / 상품명 / 운영기관구분 / 상품구분 / 학자금유형구분 /
  대학구분 / 학년구분 / 학과구분 / 성적기준 / 소득기준 / 지원내역 /
  특정자격 / 지역거주여부 / 선발방법 / 선발인원 / 자격제한 /
  추천필요여부 / 제출서류 / 홈페이지주소 / 모집시작일 / 모집종료일
"""

import csv
import glob
from pathlib import Path
from typing import Optional

from backend.logging_config import get_logger

logger = get_logger(__name__)

SCHOLARSHIP_DIR = Path(__file__).parent.parent.parent / "database" / "data" / "scholarships"

# 컬럼 인덱스 (헤더 순서 고정)
_COL = {
    "번호":       0,
    "기관명":     1,
    "장학금명":   2,
    "기관구분":   3,
    "상품구분":   4,
    "학자금유형": 5,
    "대학구분":   6,
    "학년구분":   7,
    "학과구분":   8,
    "성적기준":   9,
    "소득기준":  10,
    "지원내역":  11,
    "특정자격":  12,
    "지역거주":  13,
    "선발방법":  14,
    "선발인원":  15,
    "자격제한":  16,
    "추천여부":  17,
    "제출서류":  18,
    "홈페이지":  19,
    "시작일":    20,
    "종료일":    21,
}


def _get(row: list[str], key: str) -> str:
    idx = _COL.get(key, -1)
    if idx < 0 or idx >= len(row):
        return ""
    return row[idx].strip()


def _row_to_doc(row: list[str]) -> Optional[dict]:
    name = _get(row, "장학금명")
    if not name or name == "상품명":  # 헤더 행 스킵
        return None

    institution = _get(row, "기관명")
    product_type = _get(row, "상품구분")      # 장학금 / 학자금대출 등
    aid_type     = _get(row, "학자금유형")    # 지역연고 / 성적우수 등
    univ_type    = _get(row, "대학구분")
    grade        = _get(row, "학년구분")
    dept         = _get(row, "학과구분")
    academic     = _get(row, "성적기준")
    income       = _get(row, "소득기준")
    support      = _get(row, "지원내역")
    qualify      = _get(row, "특정자격")
    region_req   = _get(row, "지역거주")
    select_way   = _get(row, "선발방법")
    select_count = _get(row, "선발인원")
    restrict     = _get(row, "자격제한")
    recommend    = _get(row, "추천여부")
    docs_needed  = _get(row, "제출서류")
    url          = _get(row, "홈페이지")
    start_dt     = _get(row, "시작일")
    end_dt       = _get(row, "종료일")

    period = ""
    if start_dt and end_dt:
        period = f"{start_dt} ~ {end_dt}"
    elif start_dt:
        period = f"{start_dt} ~"

    # 카테고리 판별
    category = "장학금"
    if "대출" in product_type or "학자금" in aid_type:
        category = "금융"

    content = f"""# {name}

## 운영 기관
{institution}

## 장학금 유형
- 구분: {product_type}
- 유형: {aid_type}
- 대학 구분: {univ_type}

## 신청 대상
- 학년: {grade}
- 학과: {dept}

## 신청 자격
### 성적 기준
{academic or '해당 없음'}

### 소득 기준
{income or '해당 없음'}

### 특정 자격
{qualify or '해당 없음'}

### 지역 거주 조건
{region_req or '해당 없음'}

### 자격 제한
{restrict or '해당 없음'}

## 지원 내역
{support or '해당 없음'}

## 선발 방법
{select_way or '해당 없음'}

## 선발 인원
{select_count or '해당 없음'}

## 추천 필요 여부
{recommend or '해당 없음'}

## 제출 서류
{docs_needed or '해당 없음'}

## 신청 기간
{period or '해당 없음'}

## 홈페이지
{url or '한국장학재단 누리집(www.kosaf.go.kr)'}
""".strip()

    return {
        "title":    name,
        "content":  content,
        "source":   f"한국장학재단_{institution[:10]}.csv",
        "category": category,
        "url":      url,
        "period":   period,
        "region":   region_req,
    }


def load_scholarship_csv(file_path: Path) -> list[dict]:
    """
    CSV 파일 1개를 읽어서 doc 목록으로 반환합니다.
    UTF-8(BOM) → CP949 순서로 인코딩을 자동 감지합니다.
    """
    docs: list[dict] = []
    for enc in ("utf-8-sig", "utf-8", "cp949", "euc-kr"):
        try:
            with open(file_path, encoding=enc, errors="strict", newline="") as f:
                reader = csv.reader(f)
                next(reader, None)  # 헤더 스킵
                for row in reader:
                    if not row:
                        continue
                    doc = _row_to_doc(row)
                    if doc:
                        docs.append(doc)
            return docs  # 성공한 인코딩으로 반환
        except (UnicodeDecodeError, UnicodeError):
            docs = []
            continue
        except Exception as e:
            logger.error(f"[scholarship] CSV 로드 실패 ({file_path.name}): {e}")
            return []

    # 마지막 fallback: replace 모드
    try:
        with open(file_path, encoding="cp949", errors="replace", newline="") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if not row:
                    continue
                doc = _row_to_doc(row)
                if doc:
                    docs.append(doc)
    except Exception as e:
        logger.error(f"[scholarship] CSV 로드 실패 ({file_path.name}): {e}")
    return docs


def load_all_scholarships(
    region: str = "",
    category: str = "",
    keyword: str = "",
    top_k: int = 0,
) -> list[dict]:
    """
    scholarships/ 폴더의 모든 CSV를 읽어서 반환합니다.
    region / category / keyword 로 필터링 가능.
    top_k=0이면 전체 반환.
    """
    all_docs: list[dict] = []

    csv_files = sorted(SCHOLARSHIP_DIR.glob("*.csv"))
    if not csv_files:
        logger.warning(f"[scholarship] CSV 파일 없음: {SCHOLARSHIP_DIR}")
        return []

    for csv_file in csv_files:
        docs = load_scholarship_csv(csv_file)
        all_docs.extend(docs)

    logger.info(f"[scholarship] 총 {len(all_docs)}개 장학금 로드")

    # 필터링
    if region:
        all_docs = [
            d for d in all_docs
            if not d.get("region") or region in d.get("region", "")
        ]
    if category:
        all_docs = [d for d in all_docs if d.get("category") == category]
    if keyword:
        kw = keyword.lower()
        all_docs = [
            d for d in all_docs
            if kw in d["title"].lower() or kw in d["content"].lower()
        ]

    return all_docs[:top_k] if top_k else all_docs


def search_scholarships(
    keywords: list[str],
    region: str = "",
    top_k: int = 5,
) -> list[dict]:
    """
    키워드로 장학금을 검색합니다.
    RAG tool에서 바로 호출 가능합니다.
    """
    all_docs = load_all_scholarships(region=region)
    if not all_docs:
        return []

    kw_lower = [k.lower() for k in keywords if k]
    if not kw_lower:
        return all_docs[:top_k]

    def score(doc: dict) -> int:
        text = (doc["title"] + " " + doc["content"]).lower()
        return sum(text.count(kw) for kw in kw_lower)

    ranked = sorted(all_docs, key=score, reverse=True)
    return [d for d in ranked if score(d) > 0][:top_k]


def embed_scholarships_to_vectordb() -> int:
    """
    모든 장학금 데이터를 임베딩하여 ChromaDB에 추가합니다.
    build_index.py 또는 policy_updater.py에서 호출합니다.
    """
    all_docs = load_all_scholarships()
    if not all_docs:
        return 0

    try:
        from backend.modules.embedder import embed_texts
        from backend.modules.vector_store import add_documents, count as db_count

        base_id    = db_count()
        batch_size = 20
        added      = 0

        for i in range(0, len(all_docs), batch_size):
            batch      = all_docs[i : i + batch_size]
            texts      = [f"{d['title']}\n{d['content'][:800]}" for d in batch]
            embeddings = embed_texts(texts)

            add_documents(
                ids        = [f"scholarship_{base_id + added + j}" for j in range(len(batch))],
                embeddings = embeddings,
                documents  = [d["content"][:1500] for d in batch],
                metadatas  = [
                    {
                        "title":    d["title"],
                        "category": d["category"],
                        "source":   d["source"],
                    }
                    for d in batch
                ],
            )
            added += len(batch)
            logger.info(f"[scholarship] 임베딩 진행: {added}/{len(all_docs)}")

        logger.info(f"[scholarship] ChromaDB 추가 완료: {added}개")
        return added

    except Exception as e:
        logger.error(f"[scholarship] 임베딩 실패: {e}")
        return 0
