"""
chatbot.py - Giao diện CLI cho PC Price Agent
Hiển thị tracking Thought → Action → Observation theo thời gian thực.

Cách chạy:
    pip install openai python-dotenv
    export OPENAI_API_KEY="sk-..."
    python chatbot.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from agent import PCPriceAgent, Step


PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")


class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    MAGENTA = "\033[95m"
    BLUE = "\033[94m"
    RED = "\033[91m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"


WIDTH = 78


EXAMPLE_QUERIES = [
    "PC gaming RTX 4070 giá bao nhiêu?",
    "Sắp xếp laptop Dell XPS theo giá tăng dần",
    "RAM DDR5 32GB giá bao nhiêu?",
    "Kiểm tra Intel i5-13400 với main B760 và RAM DDR5 có tương thích không?",
]


def banner() -> None:
    print(f"\n{C.CYAN}{C.BOLD}{'═' * WIDTH}")
    print(f"{'  🖥️  PC PRICE AI AGENT':^{WIDTH}}")
    print(f"{'  Powered by OpenAI + Tool Calling':^{WIDTH}}")
    print(f"{'═' * WIDTH}{C.RESET}\n")


def divider(char: str = "─", color: str = C.GRAY) -> None:
    print(f"{color}{char * WIDTH}{C.RESET}")


def print_step_header(step_index: int) -> None:
    print(f"\n{C.BOLD}{C.BLUE}┌{'─'*4} BƯỚC {step_index} {'─'*(WIDTH-11)}┐{C.RESET}")


def print_thought(text: str) -> None:
    if not text:
        return
    print(f"{C.BOLD}{C.YELLOW}💭 THOUGHT{C.RESET}")
    for line in text.split("\n"):
        print(f"   {C.WHITE}{line}{C.RESET}")


def print_action(tool_name: str, tool_input: dict) -> None:
    print(f"\n{C.BOLD}{C.MAGENTA}⚡ ACTION  →  Tool: `{tool_name}`{C.RESET}")
    for key, value in tool_input.items():
        print(f"   {C.GRAY}{key:<12}: {C.WHITE}{value}{C.RESET}")


def print_observation(raw_json: str) -> None:
    print(f"\n{C.BOLD}{C.GREEN}🔭 OBSERVATION{C.RESET}")
    try:
        data = json.loads(raw_json)
        if "results" in data:
            total = data.get("total_found", 0)
            print(f"   {C.GRAY}Tìm thấy {C.WHITE}{total}{C.GRAY} sản phẩm:{C.RESET}")
            for i, r in enumerate(data.get("results", []), 1):
                stock = f"{C.GREEN}Còn hàng{C.RESET}" if r.get("in_stock") else f"{C.RED}Hết hàng{C.RESET}"
                print(f"\n   {C.BOLD}[{i}] {r['name']}{C.RESET}")
                print(f"       💰 Giá  : {C.YELLOW}{r['price']}{C.RESET}")
                print(f"       🏪 Shop : {C.CYAN}{r['shop']}{C.RESET}  |  {stock}")
                print(f"       🔗 Link : {C.BLUE}{r['url']}{C.RESET}")
        elif "checks" in data:
            print(f"   {C.GRAY}{data.get('summary', '')}{C.RESET}")
            for item in data.get("checks", []):
                status = f"{C.GREEN}OK{C.RESET}" if item.get("compatible") else f"{C.RED}Lỗi{C.RESET}"
                print(f"   - {status} {item['component_pair']}: {item['details']}")
            if data.get("issues"):
                print(f"\n   {C.YELLOW}Vấn đề:{C.RESET}")
                for issue in data["issues"]:
                    print(f"   • {issue}")
        else:
            print(f"   {C.GRAY}{json.dumps(data, ensure_ascii=False, indent=2)}{C.RESET}")
    except Exception:
        print(f"   {C.GRAY}{raw_json[:500]}{C.RESET}")


def print_duration(ms: float) -> None:
    print(f"\n   {C.DIM}⏱ {ms:.0f} ms{C.RESET}")


def on_step_callback(step: Step) -> None:
    print_step_header(step.step_index)
    if step.thought:
        print_thought(step.thought)
    if step.action_tool:
        print_action(step.action_tool, step.action_input)
    if step.observation:
        print_observation(step.observation)
    print_duration(step.duration_ms)


def print_final_answer(answer: str, trace) -> None:
    divider("═", C.CYAN)
    print(f"{C.BOLD}{C.CYAN}✅ KẾT QUẢ CUỐI CÙNG{C.RESET}\n")
    print(f"{C.WHITE}{answer}{C.RESET}")
    divider("─", C.GRAY)
    print(
        f"{C.DIM}  Tổng thời gian: {trace.total_duration_ms:.0f} ms  |  "
        f"Bước: {len(trace.steps)}  |  "
        f"Tokens: {trace.input_tokens} in / {trace.output_tokens} out{C.RESET}"
    )
    divider("═", C.CYAN)


def check_api_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        print(f"{C.RED}❌ Chưa thiết lập OPENAI_API_KEY!{C.RESET}")
        print(f"   Chạy: {C.YELLOW}export OPENAI_API_KEY='sk-...'{C.RESET}")
        sys.exit(1)


def main() -> None:
    check_api_key()
    banner()

    print(f"{C.GRAY}Ví dụ câu hỏi:{C.RESET}")
    for q in EXAMPLE_QUERIES:
        print(f"  {C.DIM}▸ {q}{C.RESET}")

    print(f"\n{C.GRAY}Gõ {C.WHITE}'quit'{C.GRAY} hoặc {C.WHITE}Ctrl+C{C.GRAY} để thoát.{C.RESET}\n")

    agent = PCPriceAgent()

    while True:
        divider()
        try:
            user_input = input(f"{C.BOLD}{C.CYAN}Bạn:{C.RESET} ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{C.GRAY}Tạm biệt! 👋{C.RESET}\n")
            break

        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit", "thoát", "q"}:
            print(f"\n{C.GRAY}Tạm biệt! 👋{C.RESET}\n")
            break

        print(f"\n{C.BOLD}{C.WHITE}🤖 Agent đang xử lý...{C.RESET}")
        divider()

        try:
            trace = agent.run(user_input, on_step=on_step_callback)
            print_final_answer(trace.final_answer, trace)
        except Exception as e:
            print(f"\n{C.RED}❌ Lỗi: {e}{C.RESET}\n")

        print()


if __name__ == "__main__":
    main()
