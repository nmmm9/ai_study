"""
main.py - 8주차 여행 플래너 Agent 실행 파일

실행: python main.py

흐름:
1. 사용자가 여행 관련 질문 입력
2. Plan-and-Execute로 계획 수립
3. ReAct 루프로 10개 도구 자동 호출
4. 결과를 HTML 파일로 저장 + 브라우저 자동 오픈
"""

import os
import webbrowser

from agent import run_agent
from html_generator import save_html

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    print("=" * 55)
    print("  ✈  여행 플래너 AI Agent  |  8주차 ReAct")
    print("=" * 55)
    print("\n질문 예시:")
    print("  - 제주도 3박 4일 여행 계획 완벽하게 짜줘")
    print("  - 부산 여행 가려는데 날씨, 관광지, 예산 다 알려줘")
    print("  - 경주 2박 3일 역사 여행 계획 세워줘")
    print("  - 강릉 1박 2일 여행 추천해줘")
    print("\n종료: 'quit' 또는 'exit'")
    print("-" * 55)

    while True:
        print()
        user_input = input("나: ").strip()

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            print("\n여행 플래너를 종료합니다. 즐거운 여행 되세요! ✈")
            break

        # ── Agent 실행 ──────────────────────────
        try:
            collected, react_log = run_agent(user_input)

            # ── HTML 저장 ────────────────────────
            print("\n" + "=" * 55)
            print("  [Phase 3] 📄 HTML 보고서 생성 중...")
            print("=" * 55)

            filepath = save_html(collected, react_log, OUTPUT_DIR)
            abs_path = os.path.abspath(filepath)

            print(f"\n  ✅ 완료! 파일 저장: {os.path.basename(filepath)}")
            print(f"  🌐 브라우저에서 열리는 중...")

            # 브라우저 자동 오픈
            webbrowser.open(f"file:///{abs_path.replace(os.sep, '/')}")

            print(f"\n  👆 브라우저에서 '{os.path.basename(filepath)}' 확인하세요!")

        except Exception as e:
            print(f"\n오류 발생: {e}")
            print("다시 시도해주세요.")


if __name__ == "__main__":
    main()
