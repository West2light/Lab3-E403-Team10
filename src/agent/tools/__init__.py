from __future__ import annotations

import json
from typing import Any, Callable

from . import check_pc_compatibility, get_top_cpu_rankings, search_pc_price, sort_products


ToolHandler = Callable[..., str]

TOOLS = [
    search_pc_price.TOOL_SPEC,
    sort_products.TOOL_SPEC,
    check_pc_compatibility.TOOL_SPEC,
    get_top_cpu_rankings.TOOL_SPEC,
]

TOOLS_OPENAI = [
    {
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": tool["input_schema"],
        },
    }
    for tool in TOOLS
]

TOOL_HANDLERS: dict[str, ToolHandler] = {
    "search_pc_price": search_pc_price.run,
    "sort_products": sort_products.run,
    "check_pc_compatibility": check_pc_compatibility.run,
    "get_top_cpu_rankings": get_top_cpu_rankings.run,
}


def execute_tool(tool_name: str, tool_input: dict[str, Any]) -> str:
    handler = TOOL_HANDLERS.get(tool_name)
    if handler is None:
        return json.dumps({"error": f"Tool '{tool_name}' khong ton tai."}, ensure_ascii=False)
    return handler(**tool_input)
