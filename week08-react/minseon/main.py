"""
main.py
───────
OOTD 에이전트 진입점

사용법:
  python main.py                        # 대화형 CLI
  python main.py --mode react           # ReAct 모드
  python main.py --mode plan            # Plan-and-Execute 모드
  python main.py --location 부산        # 위치 지정
  python main.py --request "데이트 코디" # 요청사항 지정
"""

import argparse
import sys
import textwrap

# .env 파일 자동 로드 (python-dotenv 설치 시)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv 없어도 환경변수 직접 설정하면 동작

from react_agent import run_agent


# ── ANSI 색상 ──────────────────────────────────────────────────
BOLD  = "\033[1m"
CYAN  = "\033[96m"
RESET = "\033[0m"


def print_banner() -> None:
    banner = f"""
{BOLD}{CYAN}
╔══════════════════════════════════════════════════════════╗
║        👗  OOTD 스타일리스트 AI  — 오늘의 코디 추천        ║
║   날씨 · 옷장 · 색상 조합을 고려한 맞춤 OOTD 추천 에이전트  ║
╚══════════════════════════════════════════════════════════╝
{RESET}"""
    print(banner)


def print_mode_info() -> None:
    print(f"{BOLD}에이전트 패턴 선택{RESET}")
    print("  1. {BOLD}ReAct{RESET}           — Thought → Action → Observation 반복")
    print("        실시간으로 사고 과정을 보여주며 유연하게 추론합니다.")
    print()
    print("  2. {BOLD}Plan-and-Execute{RESET} — 계획 수립 → 단계 실행 → 종합")
    print("        먼저 전체 계획을 세운 뒤 순서대로 실행하고 최종 추천합니다.")
    print()


def interactive_cli() -> None:
    """대화형 CLI 모드"""
    print_banner()

    # 위치 입력
    location = input(f"📍 위치를 입력하세요 (기본값: 서울): ").strip()
    if not location:
        location = "서울"

    print()
    print_mode_info()

    # 모드 선택
    mode_input = input("모드를 선택하세요 [1=ReAct / 2=Plan] (기본값: 1): ").strip()
    mode = "plan" if mode_input == "2" else "react"

    # 요청사항 입력
    user_request = input("\n📝 추가 요청사항 (없으면 엔터): ").strip()

    # 에이전트 실행
    run_agent(mode=mode, location=location, user_request=user_request)

    # 반복 여부
    print()
    again = input("다른 코디도 추천받으시겠어요? (y/n): ").strip().lower()
    if again == "y":
        new_request = input("📝 새 요청사항 (없으면 엔터): ").strip()
        run_agent(mode=mode, location=location, user_request=new_request)

    print(f"\n{BOLD}👋 스타일리시한 하루 되세요!{RESET}\n")


def cli_with_args(args: argparse.Namespace) -> None:
    """커맨드라인 인수 모드"""
    print_banner()
    run_agent(
        mode=args.mode,
        location=args.location,
        user_request=args.request,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="OOTD 스타일리스트 AI — 날씨 기반 코디 추천",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        예시:
          python main.py
          python main.py --mode react --location 서울
          python main.py --mode plan  --location 부산 --request "비즈니스 캐주얼"
        """),
    )
    parser.add_argument(
        "--mode", choices=["react", "plan"], default=None,
        help="에이전트 패턴: react (ReAct) 또는 plan (Plan-and-Execute)",
    )
    parser.add_argument(
        "--location", default=None,
        help="날씨 조회 위치 (기본값: 서울)",
    )
    parser.add_argument(
        "--request", default="",
        help="추가 요청사항 (예: '오늘 면접 있어요', '데이트 코디')",
    )

    args = parser.parse_args()

    # 인수 없이 실행하면 대화형 CLI
    if args.mode is None and args.location is None:
        interactive_cli()
    else:
        args.mode     = args.mode     or "react"
        args.location = args.location or "서울"
        cli_with_args(args)


if __name__ == "__main__":
    main()
