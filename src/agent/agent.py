"""
agent.py - Vòng lặp Agent: Thought → Action → Observation
Sử dụng OpenAI API với tool calling.
Tracking đầy đủ từng bước, tách biệt khỏi UI.
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from openai import OpenAI

from tools import TOOLS_OPENAI, execute_tool


SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.append(str(SRC_ROOT))

from telemetry.logger import logger


@dataclass
class Step:
    """Một bước trong vòng lặp Agent."""

    step_index: int
    thought: str = ""
    action_tool: str = ""
    action_input: dict = field(default_factory=dict)
    observation: str = ""
    duration_ms: float = 0.0


@dataclass
class AgentTrace:
    """Toàn bộ trace của một lần chạy Agent."""

    user_query: str
    steps: list[Step] = field(default_factory=list)
    final_answer: str = ""
    total_duration_ms: float = 0.0
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0


class PCPriceAgent:
    """
    AI Agent tìm kiếm giá PC theo vòng lặp ReAct:
    Thought → Action → Observation → ... → Final Answer
    """

    DEFAULT_MODEL = "gpt-4o"
    DEFAULT_MAX_ITERATIONS = 5

    SYSTEM_PROMPT = """Bạn là AI Agent chuyên tìm kiếm giá PC, laptop và linh kiện máy tính tại Việt Nam.

## ROLE & RULES
- Trả lời bằng tiếng Việt, thân thiện và chuyên nghiệp.
- Dùng tool `search_pc_price` để tìm sản phẩm.
- Dùng tool `sort_products` khi người dùng muốn sắp xếp theo giá tăng dần hoặc giảm dần.
- Dùng tool `check_pc_compatibility` khi người dùng muốn kiểm tra CPU, mainboard, RAM, GPU, PSU, case có tương thích hay không.
- Trình bày kết quả rõ ràng: tên sản phẩm, giá, shop, link.
- Nếu không tìm thấy sản phẩm phù hợp, hãy thông báo thẳng thắn.
- KHÔNG bịa đặt giá hay link sản phẩm.

## OUTPUT FORMAT
Sau khi có kết quả từ tool, trả lời theo định dạng:
1. Tóm tắt ngắn về tìm kiếm
2. Danh sách sản phẩm hoặc kết quả kiểm tra tương thích
3. Gợi ý / lời khuyên nếu cần

## STOPPING CONDITION
Dừng sau khi đã có đủ thông tin từ tool và đưa ra câu trả lời hoàn chỉnh."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
    ):
        self.client = OpenAI(api_key=api_key) if api_key else OpenAI()
        self.model = model or self.DEFAULT_MODEL
        self.max_iterations = max_iterations

    def run(self, user_query: str, on_step: Optional[Callable[[Step], None]] = None) -> AgentTrace:
        trace = AgentTrace(user_query=user_query, model=self.model)
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_query},
        ]

        start_total = time.perf_counter()

        for iteration in range(self.max_iterations):
            step = Step(step_index=iteration + 1)
            t0 = time.perf_counter()

            response = self.client.chat.completions.create(
                model=self.model,
                tools=TOOLS_OPENAI,
                tool_choice="auto",
                messages=messages,
            )

            msg = response.choices[0].message
            finish_reason = response.choices[0].finish_reason

            trace.input_tokens += response.usage.prompt_tokens
            trace.output_tokens += response.usage.completion_tokens
            step.thought = msg.content or ""

            if finish_reason == "stop":
                step.duration_ms = (time.perf_counter() - t0) * 1000
                trace.steps.append(step)
                logger.log_agent_step(
                    step_index=step.step_index,
                    thought=step.thought,
                    action_tool=step.action_tool,
                    action_input=step.action_input,
                    observation=step.observation,
                    duration_ms=step.duration_ms,
                )
                if on_step:
                    on_step(step)
                trace.final_answer = step.thought
                break

            if not msg.tool_calls:
                step.thought = step.thought or "[Agent không quyết định được hành động]"
                step.duration_ms = (time.perf_counter() - t0) * 1000
                trace.steps.append(step)
                logger.log_agent_step(
                    step_index=step.step_index,
                    thought=step.thought,
                    action_tool=step.action_tool,
                    action_input=step.action_input,
                    observation=step.observation,
                    duration_ms=step.duration_ms,
                )
                if on_step:
                    on_step(step)
                trace.final_answer = step.thought
                break

            messages.append(msg)

            for tool_call in msg.tool_calls:
                step.action_tool = tool_call.function.name
                step.action_input = json.loads(tool_call.function.arguments)
                tool_t0 = time.perf_counter()
                observation_raw = execute_tool(step.action_tool, step.action_input)
                tool_duration_ms = (time.perf_counter() - tool_t0) * 1000
                step.observation = observation_raw
                logger.log_tool_call(
                    tool_name=step.action_tool,
                    inputs=step.action_input,
                    result=observation_raw,
                    duration_ms=tool_duration_ms,
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": observation_raw,
                    }
                )

            step.duration_ms = (time.perf_counter() - t0) * 1000
            trace.steps.append(step)
            logger.log_agent_step(
                step_index=step.step_index,
                thought=step.thought,
                action_tool=step.action_tool,
                action_input=step.action_input,
                observation=step.observation,
                duration_ms=step.duration_ms,
            )
            if on_step:
                on_step(step)
        else:
            trace.final_answer = "[Đã đạt giới hạn vòng lặp]"

        trace.total_duration_ms = (time.perf_counter() - start_total) * 1000
        if not trace.final_answer and trace.steps:
            trace.final_answer = trace.steps[-1].thought or "[Không có kết quả cuối cùng]"
        logger.log_agent_complete(
            user_query=user_query,
            total_steps=len(trace.steps),
            total_duration_ms=trace.total_duration_ms,
            input_tokens=trace.input_tokens,
            output_tokens=trace.output_tokens,
            model=trace.model,
        )
        return trace
