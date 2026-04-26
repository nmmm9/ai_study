"""
main.py
───────
CLI 실행 진입점

실행:
    python main.py
    python main.py --query "청년도약계좌 자격조건 알려줘"
    python main.py --visualize
"""

import argparse
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BOLD  = "\033[1m"
CYAN  = "\033[96m"
GREEN = "\033[92m"
DIM   = "\033[2m"
RESET = "\033[0m"


def print_banner() -> None:
    print(f"\n{BOLD}{'━'*60}{RESET}")
    print(f"{BOLD}  청년정책 AI 상담사 — LangGraph 버전{RESET}")
    print(f"{BOLD}{'━'*60}{RESET}")


def print_graph_structure() -> None:
    from graph import get_mermaid, graph as ootd_graph

    print(f"\n{BOLD}{CYAN}📊 그래프 구조 (Mermaid){RESET}")
    print(f"{DIM}{'─'*60}{RESET}")
    print(get_mermaid())
    print(f"{DIM}{'─'*60}{RESET}")
    print(f"{DIM}💡 https://mermaid.live 에서 렌더링 가능{RESET}")

    try:
        png = ootd_graph.get_graph().draw_mermaid_png()
        with open("graph_visualization.png", "wb") as f:
            f.write(png)
        print(f"✅ 그래프 이미지 저장: graph_visualization.png")
    except Exception as e:
        print(f"{DIM}⚠️  PNG 저장 실패: {e}{RESET}")


def print_trace(trace: list) -> None:
    print(f"\n{BOLD}📋 실행 순서{RESET}")
    print(f"{DIM}{'─'*60}{RESET}")
    for i, step in enumerate(trace, 1):
        print(f"  {DIM}[{i}]{RESET} {BOLD}{step['node']}{RESET}")
        print(f"       {DIM}→ {step['summary']}{RESET}")
    print(f"{DIM}{'─'*60}{RESET}")


def run_once(query: str) -> None:
    from graph import stream_run
    from tools.policy_loader import get_policy_count

    print(f"\n{BOLD}📄 로드된 정책 수: {get_policy_count()}개{RESET}")
    print(f"{BOLD}❓ 질문: {query}{RESET}")
    print(f"\n{DIM}{'─'*60}{RESET}")
    print(f"{BOLD}{CYAN}🚀 LangGraph 에이전트 실행 시작{RESET}")
    print(f"{DIM}{'─'*60}{RESET}")

    last_updates = {}
    node_count   = 0

    for node_name, updates in stream_run(query):
        node_count  += 1
        last_updates = updates

    trace = last_updates.get("execution_trace", [])
    if trace:
        print_trace(trace)

    print(f"\n{BOLD}{GREEN}✅ 총 {node_count}개 노드 실행 완료{RESET}")


def interactive_loop() -> None:
    print(f"\n{DIM}종료: 'quit' 또는 'exit' 입력{RESET}\n")
    while True:
        query = input(f"{BOLD}❓ 질문: {RESET}").strip()
        if query.lower() in ("quit", "exit", "종료"):
            print(f"\n{BOLD}👋 이용해주셔서 감사합니다!{RESET}")
            break
        if not query:
            continue
        run_once(query)
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="청년정책 LangGraph 에이전트")
    parser.add_argument("--query",      default="", help="질문 (없으면 대화형 모드)")
    parser.add_argument("--visualize",  action="store_true", help="그래프 구조만 출력")
    args = parser.parse_args()

    print_banner()

    if args.visualize:
        print_graph_structure()
        sys.exit(0)

    print_graph_structure()

    if args.query:
        run_once(args.query)
    else:
        interactive_loop()


if __name__ == "__main__":
    main()
