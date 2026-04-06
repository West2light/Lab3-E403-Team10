from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agent.agent import PCPriceAgent
from src.agent.tools import TOOLS_OPENAI, execute_tool
from src.core.config import get_env, load_project_env


ARTIFACTS_DIR = PROJECT_ROOT / "report" / "group_report" / "artifacts"
CASE_FILE = ARTIFACTS_DIR / "evaluation_cases.json"
RESULT_JSON = ARTIFACTS_DIR / "evaluation_results.json"
RESULT_MD = ARTIFACTS_DIR / "evaluation_summary.md"

BASELINE_SYSTEM = """Bạn là trợ lý tư vấn mua PC và linh kiện máy tính tại Việt Nam.
Trả lời bằng tiếng Việt, ngắn gọn và hữu ích.
Lưu ý: bạn KHÔNG có công cụ tìm giá thực tế, hãy dùng kiến thức sẵn có."""

AGENT_PROMPT_V1 = """Bạn là AI Agent tư vấn PC và linh kiện máy tính tại Việt Nam.

- Trả lời bằng tiếng Việt.
- Bạn có thể dùng tool khi thấy cần.
- Nếu có kết quả từ tool thì tóm tắt lại cho người dùng.
- Không bịa thông tin."""

NORMALIZED_COST_PER_1K_TOKENS = 0.01


@dataclass
class RunResult:
    mode: str
    query: str
    answer: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float
    passed: bool
    reasons: list[str]
    tools_used: list[str]
    step_count: int


def load_cases() -> list[dict[str, Any]]:
    with CASE_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def evaluate_answer(answer: str, case: dict[str, Any], tools_used: list[str]) -> tuple[bool, list[str]]:
    text = answer.lower()
    reasons: list[str] = []

    for keyword in case.get("must_include_all", []):
        if keyword.lower() not in text:
            reasons.append(f"missing keyword: {keyword}")

    if case.get("must_include_any"):
        if not any(keyword.lower() in text for keyword in case["must_include_any"]):
            reasons.append(f"missing any of: {', '.join(case['must_include_any'])}")

    ordered_keywords = case.get("ordered_keywords", [])
    if ordered_keywords:
        positions = [text.find(keyword.lower()) for keyword in ordered_keywords]
        if any(position == -1 for position in positions) or positions != sorted(positions):
            reasons.append(f"wrong keyword order: {' -> '.join(ordered_keywords)}")

    for keyword in case.get("forbidden_keywords", []):
        if keyword.lower() in text:
            reasons.append(f"contains forbidden keyword: {keyword}")

    expected_tools = case.get("expected_tools", [])
    if expected_tools:
        missing_tools = [tool for tool in expected_tools if tool not in tools_used]
        if missing_tools:
            reasons.append(f"missing expected tools: {', '.join(missing_tools)}")

    return len(reasons) == 0, reasons


def call_baseline(client: OpenAI, model: str, query: str) -> RunResult:
    start = time.perf_counter()
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": BASELINE_SYSTEM},
            {"role": "user", "content": query},
        ],
    )
    latency_ms = (time.perf_counter() - start) * 1000
    answer = response.choices[0].message.content or ""
    usage = response.usage
    return RunResult(
        mode="baseline",
        query=query,
        answer=answer,
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        total_tokens=usage.total_tokens,
        latency_ms=latency_ms,
        passed=False,
        reasons=[],
        tools_used=[],
        step_count=1,
    )


def call_agent(agent: PCPriceAgent, query: str, mode: str) -> RunResult:
    trace = agent.run(query)
    tools_used = [step.action_tool for step in trace.steps if step.action_tool]
    return RunResult(
        mode=mode,
        query=query,
        answer=trace.final_answer,
        prompt_tokens=trace.input_tokens,
        completion_tokens=trace.output_tokens,
        total_tokens=trace.input_tokens + trace.output_tokens,
        latency_ms=trace.total_duration_ms,
        passed=False,
        reasons=[],
        tools_used=tools_used,
        step_count=len(trace.steps),
    )


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    index = (len(values) - 1) * q
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return values[int(index)]
    return values[lower] + (values[upper] - values[lower]) * (index - lower)


def summarize(mode_results: list[RunResult]) -> dict[str, Any]:
    latencies = sorted(result.latency_ms for result in mode_results)
    tokens = [result.total_tokens for result in mode_results]
    costs = [(token / 1000) * NORMALIZED_COST_PER_1K_TOKENS for token in tokens]
    passes = sum(1 for result in mode_results if result.passed)
    tool_calls = sum(len(result.tools_used) for result in mode_results)

    return {
        "cases": len(mode_results),
        "passes": passes,
        "success_rate": round((passes / len(mode_results)) * 100, 2) if mode_results else 0.0,
        "avg_latency_ms": round(statistics.mean(latencies), 2) if latencies else 0.0,
        "p50_latency_ms": round(percentile(latencies, 0.5), 2),
        "p99_latency_ms": round(percentile(latencies, 0.99), 2),
        "avg_total_tokens": round(statistics.mean(tokens), 2) if tokens else 0.0,
        "normalized_cost_total_usd": round(sum(costs), 4),
        "normalized_cost_avg_usd": round(statistics.mean(costs), 4) if costs else 0.0,
        "tool_calls": tool_calls,
        "avg_steps": round(statistics.mean(result.step_count for result in mode_results), 2) if mode_results else 0.0,
    }


def write_summary_markdown(
    model: str,
    grouped_results: dict[str, list[RunResult]],
    summary: dict[str, dict[str, Any]],
) -> None:
    lines = [
        "# Evaluation Summary",
        "",
        f"- Model: `{model}`",
        f"- Cases: `{len(next(iter(grouped_results.values()), []))}`",
        f"- Normalized cost formula: `${NORMALIZED_COST_PER_1K_TOKENS:.2f} / 1K tokens`",
        "",
        "## Scoreboard",
        "",
        "| Mode | Success Rate | Avg Latency (ms) | P50 (ms) | P99 (ms) | Avg Tokens | Total Normalized Cost | Avg Steps | Tool Calls |",
        "| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for mode in ["baseline", "agent_v1", "agent_v2"]:
        item = summary[mode]
        lines.append(
            f"| {mode} | {item['success_rate']}% | {item['avg_latency_ms']} | {item['p50_latency_ms']} | "
            f"{item['p99_latency_ms']} | {item['avg_total_tokens']} | ${item['normalized_cost_total_usd']} | "
            f"{item['avg_steps']} | {item['tool_calls']} |"
        )

    lines.extend(
        [
            "",
            "## Case Breakdown",
            "",
            "| Case | Baseline | Agent v1 | Agent v2 |",
            "| :--- | :---: | :---: | :---: |",
        ]
    )

    case_count = len(grouped_results["baseline"])
    for index in range(case_count):
        case_name = f"Case {index + 1}"
        row = [case_name]
        for mode in ["baseline", "agent_v1", "agent_v2"]:
            result = grouped_results[mode][index]
            row.append("Pass" if result.passed else "Fail")
        lines.append(f"| {' | '.join(row)} |")

    RESULT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=get_env("DEFAULT_MODEL", "gpt-4o"))
    args = parser.parse_args()

    load_project_env()
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    client = OpenAI(api_key=get_env("OPENAI_API_KEY"))
    cases = load_cases()

    tools_v1 = [
        tool
        for tool in TOOLS_OPENAI
        if tool.get("function", {}).get("name") != "get_top_cpu_rankings"
    ]

    def execute_tool_v1(tool_name: str, tool_input: dict[str, Any]) -> str:
        if tool_name == "get_top_cpu_rankings":
            return json.dumps({"error": "Tool 'get_top_cpu_rankings' khong ton tai."}, ensure_ascii=False)
        return execute_tool(tool_name, tool_input)

    agent_v1 = PCPriceAgent(
        model=args.model,
        system_prompt=AGENT_PROMPT_V1,
        temperature=0,
        tools_openai=tools_v1,
        tool_executor=execute_tool_v1,
    )
    agent_v2 = PCPriceAgent(model=args.model, temperature=0)

    grouped_results: dict[str, list[RunResult]] = {"baseline": [], "agent_v1": [], "agent_v2": []}

    for case in cases:
        baseline_result = call_baseline(client, args.model, case["query"])
        baseline_result.passed, baseline_result.reasons = evaluate_answer(
            baseline_result.answer, case, baseline_result.tools_used
        )
        grouped_results["baseline"].append(baseline_result)

        agent_v1_result = call_agent(agent_v1, case["query"], "agent_v1")
        agent_v1_result.passed, agent_v1_result.reasons = evaluate_answer(
            agent_v1_result.answer, case, agent_v1_result.tools_used
        )
        grouped_results["agent_v1"].append(agent_v1_result)

        agent_v2_result = call_agent(agent_v2, case["query"], "agent_v2")
        agent_v2_result.passed, agent_v2_result.reasons = evaluate_answer(
            agent_v2_result.answer, case, agent_v2_result.tools_used
        )
        grouped_results["agent_v2"].append(agent_v2_result)

    summary = {mode: summarize(results) for mode, results in grouped_results.items()}
    payload = {
        "model": args.model,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cases": cases,
        "summary": summary,
        "results": {
            mode: [asdict(result) for result in results] for mode, results in grouped_results.items()
        },
    }
    RESULT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_summary_markdown(args.model, grouped_results, summary)


if __name__ == "__main__":
    main()
