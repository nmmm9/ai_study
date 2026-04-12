"""
colorhunt_scraper.py
────────────────────
ColorHunt 비공식 API에서 인기 팔레트를 가져와
tools/colors.py 의 COLOR_PAIRINGS 데이터를 자동으로 업데이트합니다.

실행:
  python colorhunt_scraper.py
  python colorhunt_scraper.py --sort popular --limit 200
  python colorhunt_scraper.py --sort trending --tag fashion
"""

import argparse
import json
import math
import re
import time
from collections import defaultdict
from pathlib import Path

import requests

# ── 알려진 색상명 ↔ RGB 매핑 ───────────────────────────────────
NAMED_COLORS: dict[str, tuple[int, int, int]] = {
    "white":      (255, 255, 255),
    "cream":      (255, 253, 208),
    "ivory":      (255, 255, 240),
    "light_gray": (211, 211, 211),
    "gray":       (128, 128, 128),
    "dark_gray":  ( 64,  64,  64),
    "black":      (  0,   0,   0),
    "light_blue": (173, 216, 230),
    "sky_blue":   (135, 206, 235),
    "blue":       ( 70, 130, 180),
    "navy":       ( 23,  37,  84),
    "royal_blue": ( 65, 105, 225),
    "sage":       (176, 208, 176),
    "mint":       (189, 252, 201),
    "green":      ( 34, 139,  34),
    "olive":      (128, 128,   0),
    "khaki":      (189, 183, 107),
    "tan":        (210, 180, 140),
    "beige":      (245, 245, 220),
    "sand":       (194, 178, 128),
    "camel":      (193, 154, 107),
    "brown":      (139,  69,  19),
    "dark_brown": ( 92,  64,  51),
    "rust":       (183,  65,  14),
    "orange":     (255, 165,   0),
    "coral":      (255, 127,  80),
    "peach":      (255, 218, 185),
    "red":        (220,  20,  60),
    "burgundy":   (128,   0,  32),
    "dusty_rose": (220, 174, 164),
    "pink":       (255, 182, 193),
    "hot_pink":   (255, 105, 180),
    "lavender":   (230, 230, 250),
    "purple":     (128,   0, 128),
    "mauve":      (224, 176, 255),
    "yellow":     (255, 255,   0),
    "mustard":    (255, 219,  88),
    "gold":       (255, 215,   0),
}

COLOR_TONE: dict[str, str] = {
    "white": "light", "cream": "light", "ivory": "light",
    "light_gray": "light", "light_blue": "light", "sky_blue": "light",
    "mint": "light", "sage": "light", "peach": "light",
    "lavender": "light", "dusty_rose": "light", "pink": "light",
    "gray": "neutral", "khaki": "neutral", "olive": "neutral",
    "sand": "neutral", "beige": "neutral",
    "blue": "medium", "green": "medium", "mauve": "medium",
    "coral": "medium", "orange": "medium", "mustard": "medium",
    "brown": "warm", "camel": "warm", "tan": "warm",
    "rust": "warm", "gold": "warm", "yellow": "warm",
    "navy": "dark", "dark_gray": "dark", "black": "dark",
    "burgundy": "dark", "purple": "dark", "dark_brown": "dark",
    "red": "dark", "hot_pink": "dark", "royal_blue": "dark",
}


# ── 헥스 → RGB ──────────────────────────────────────────────────
def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    h = hex_str.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def color_distance(rgb1: tuple, rgb2: tuple) -> float:
    """유클리드 거리 (간단한 색 근접도)"""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(rgb1, rgb2)))


def hex_to_name(hex_str: str) -> str:
    """헥스 코드를 가장 가까운 색상 이름으로 변환합니다."""
    rgb = hex_to_rgb(hex_str)
    best_name = "gray"
    best_dist = float("inf")
    for name, named_rgb in NAMED_COLORS.items():
        d = color_distance(rgb, named_rgb)
        if d < best_dist:
            best_dist = d
            best_name = name
    return best_name


# ── ColorHunt API ───────────────────────────────────────────────
def fetch_palettes(
    sort: str = "popular",
    tag: str = "",
    limit: int = 100,
) -> list[dict]:
    """
    ColorHunt 비공식 API에서 팔레트를 가져옵니다.

    Args:
        sort  : popular | new | random | trending
        tag   : fashion, pastel, vintage, earth 등 (빈 문자열 = 전체)
        limit : 가져올 팔레트 수 (20 단위로 반올림)

    Returns:
        [{"colors": ["#xxxxxx", ...], "likes": int, "tags": str}, ...]
    """
    url = "https://colorhunt.co/php/feed.php"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Referer": "https://colorhunt.co/",
        "Origin":  "https://colorhunt.co",
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Requested-With": "XMLHttpRequest",
    }

    all_palettes: list[dict] = []
    step = 0

    while len(all_palettes) < limit:
        payload = {
            "step": step,
            "sort": sort,
            "tags": tag,
            "timeframe": "30",  # 최근 30일 (popular/trending 시 적용)
        }
        try:
            resp = requests.post(url, data=payload, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.HTTPError as e:
            print(f"  ⚠️  HTTP 오류: {e}")
            break
        except Exception as e:
            print(f"  ⚠️  요청 오류: {e}")
            break

        if not data:
            break

        for item in data:
            code = item.get("code", "")
            if len(code) != 24:
                continue
            # 24자 코드를 6자씩 4개 색상으로 분리
            colors = [f"#{code[i:i+6]}" for i in range(0, 24, 6)]
            all_palettes.append({
                "colors": colors,
                "likes": item.get("likes", 0),
                "tags": item.get("tags", ""),
                "id": item.get("id", ""),
            })

        step += 1
        print(f"  페이지 {step} 수집 완료 ({len(all_palettes)}개)")
        time.sleep(0.5)  # 서버 부하 방지

    return all_palettes[:limit]


# ── 팔레트 → 색상 조합 통계 ──────────────────────────────────────
def build_pairings(palettes: list[dict]) -> dict[str, dict]:
    """
    팔레트 목록에서 색상별 조합 빈도를 집계합니다.

    Returns:
        {color_name: {paired_color: count, ...}, ...}
    """
    pairings: dict[str, dict] = defaultdict(lambda: defaultdict(int))

    for p in palettes:
        names = [hex_to_name(c) for c in p["colors"]]
        unique_names = list(dict.fromkeys(names))  # 중복 제거, 순서 유지

        for i, name in enumerate(unique_names):
            for j, other in enumerate(unique_names):
                if i != j:
                    pairings[name][other] += 1

    return {k: dict(v) for k, v in pairings.items()}


def pairings_to_color_data(pairings: dict[str, dict], top_n: int = 6) -> dict[str, dict]:
    """
    빈도 통계를 tools/colors.py 형식으로 변환합니다.

    각 색상에 대해 가장 많이 함께 등장한 상위 top_n개를 combinations으로 사용합니다.
    """
    result = {}
    for color, paired in pairings.items():
        sorted_pairs = sorted(paired.items(), key=lambda x: x[1], reverse=True)
        combinations = [c for c, _ in sorted_pairs[:top_n]]

        # avoid: 절대 함께 등장하지 않는 색상 (출현 횟수 0 또는 미등장)
        all_names = set(NAMED_COLORS.keys())
        never_paired = [
            c for c in all_names
            if c not in paired and c != color
        ]

        result[color] = {
            "korean_name": _korean_name(color),
            "tone": COLOR_TONE.get(color, "neutral"),
            "combinations": combinations,
            "description": f"ColorHunt 실제 데이터 기반 조합. 상위 {top_n}개 색상과 잘 어울림.",
            "avoid": never_paired[:3],  # 상위 3개만 avoid로 표시
        }
    return result


def _korean_name(color: str) -> str:
    mapping = {
        "white": "화이트", "cream": "크림", "ivory": "아이보리",
        "light_gray": "연회색", "gray": "그레이", "dark_gray": "다크그레이",
        "black": "블랙", "light_blue": "하늘색", "sky_blue": "스카이블루",
        "blue": "블루", "navy": "네이비", "royal_blue": "로얄블루",
        "sage": "세이지", "mint": "민트", "green": "그린",
        "olive": "올리브", "khaki": "카키", "tan": "탄",
        "beige": "베이지", "sand": "샌드", "camel": "카멜",
        "brown": "브라운", "dark_brown": "다크브라운", "rust": "러스트",
        "orange": "오렌지", "coral": "코랄", "peach": "피치",
        "red": "레드", "burgundy": "버건디", "dusty_rose": "더스티로즈",
        "pink": "핑크", "hot_pink": "핫핑크", "lavender": "라벤더",
        "purple": "퍼플", "mauve": "모브", "yellow": "옐로우",
        "mustard": "머스타드", "gold": "골드",
    }
    return mapping.get(color, color)


# ── colors.py 업데이트 ───────────────────────────────────────────
COLORS_PY = Path("tools/colors.py")

def load_existing_pairings() -> dict:
    """기존 COLOR_PAIRINGS를 파싱합니다 (백업용)."""
    # 간단히 eval 없이 파일 통째로 읽어서 원본 보존
    return {}


def update_colors_py(new_data: dict[str, dict]) -> None:
    """
    tools/colors.py 의 COLOR_PAIRINGS를 새 데이터로 업데이트합니다.
    기존 항목은 유지하고, 새 항목을 추가·업데이트합니다.
    """
    content = COLORS_PY.read_text(encoding="utf-8")

    # COLOR_PAIRINGS 블록 찾기
    pattern = re.compile(
        r"(COLOR_PAIRINGS:\s*dict\[str,\s*dict\]\s*=\s*\{)(.*?)(\n\})",
        re.DOTALL,
    )
    match = pattern.search(content)
    if not match:
        print("  ⚠️  COLOR_PAIRINGS 블록을 찾지 못했습니다.")
        return

    # 기존 블록 파싱 (색상 키 추출)
    existing_block = match.group(2)
    existing_keys = set(re.findall(r'^\s*"(\w+)":\s*\{', existing_block, re.MULTILINE))

    # 새 항목만 추가 (기존 항목은 건드리지 않음)
    new_entries = {k: v for k, v in new_data.items() if k not in existing_keys}

    if not new_entries:
        print("  ℹ️  추가할 새 색상이 없습니다 (모두 기존에 존재).")
        return

    # 새 항목을 Python 코드 문자열로 직렬화
    new_block_lines = []
    for color, info in new_entries.items():
        combos = json.dumps(info["combinations"], ensure_ascii=False)
        avoid  = json.dumps(info["avoid"], ensure_ascii=False)
        lines = [
            f'    "{color}": {{',
            f'        "korean_name": "{info["korean_name"]}",',
            f'        "tone": "{info["tone"]}",',
            f'        "combinations": {combos},',
            f'        "description": "{info["description"]}",',
            f'        "avoid": {avoid},',
            f'    }},',
        ]
        new_block_lines.extend(lines)

    # 기존 블록 끝에 삽입
    insert_text = "\n" + "\n".join(new_block_lines)
    new_block = match.group(2) + insert_text
    new_content = content[: match.start(2)] + new_block + content[match.end(2):]

    # 백업
    backup = COLORS_PY.with_suffix(".py.bak")
    backup.write_text(content, encoding="utf-8")
    print(f"  💾 기존 파일 백업: {backup}")

    COLORS_PY.write_text(new_content, encoding="utf-8")
    print(f"  ✅ {len(new_entries)}개 색상 추가 완료: {', '.join(new_entries.keys())}")


# ── 결과 미리보기 ────────────────────────────────────────────────
def preview(palettes: list[dict], color_data: dict, n: int = 5) -> None:
    print(f"\n{'─'*60}")
    print(f"  수집된 팔레트 {len(palettes)}개 중 상위 {n}개 미리보기")
    print(f"{'─'*60}")
    for p in palettes[:n]:
        names = [hex_to_name(c) for c in p["colors"]]
        print(f"  {' + '.join(p['colors'])}  →  {' / '.join(names)}  (♥ {p['likes']})")

    print(f"\n{'─'*60}")
    print(f"  생성된 색상 조합 데이터 ({len(color_data)}개 색상)")
    print(f"{'─'*60}")
    for color, info in list(color_data.items())[:8]:
        combos = ", ".join(info["combinations"])
        print(f"  {color:15s} → {combos}")


# ── CLI ──────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="ColorHunt → colors.py 스크래퍼")
    parser.add_argument("--sort",  default="popular",
                        choices=["popular", "new", "random", "trending"],
                        help="정렬 기준 (기본: popular)")
    parser.add_argument("--tag",   default="",
                        help="태그 필터 (예: fashion, pastel, earth, vintage)")
    parser.add_argument("--limit", type=int, default=100,
                        help="수집할 팔레트 수 (기본: 100)")
    parser.add_argument("--top",   type=int, default=6,
                        help="색상당 추천 조합 수 (기본: 6)")
    parser.add_argument("--dry-run", action="store_true",
                        help="파일 수정 없이 미리보기만 출력")
    args = parser.parse_args()

    print(f"\n{'═'*60}")
    print(f"  🎨 ColorHunt 스크래퍼 시작")
    print(f"  정렬: {args.sort} | 태그: {args.tag or '전체'} | 수집: {args.limit}개")
    print(f"{'═'*60}\n")

    # 1. 팔레트 수집
    print("📡 ColorHunt에서 팔레트 수집 중...")
    palettes = fetch_palettes(sort=args.sort, tag=args.tag, limit=args.limit)

    if not palettes:
        print("❌ 팔레트를 가져오지 못했습니다.")
        print("   → 네트워크 연결 또는 ColorHunt 서버 상태를 확인하세요.")
        return

    print(f"\n✅ 총 {len(palettes)}개 팔레트 수집 완료")

    # 2. 색상 조합 통계 집계
    print("\n🔢 색상 조합 분석 중...")
    pairings = build_pairings(palettes)
    color_data = pairings_to_color_data(pairings, top_n=args.top)

    # 3. 미리보기
    preview(palettes, color_data)

    # 4. colors.py 업데이트
    if not args.dry_run:
        print(f"\n📝 tools/colors.py 업데이트 중...")
        update_colors_py(color_data)
    else:
        print("\n  (--dry-run 모드: 파일 수정 생략)")

    print(f"\n{'═'*60}")
    print("  🎉 완료!")
    print(f"{'═'*60}\n")


if __name__ == "__main__":
    main()
