from __future__ import annotations

import json

from .common import pick_dataset


TOOL_SPEC = {
    "name": "search_pc_price",
    "description": (
        "Tim kiem gia PC / linh kien may tinh. "
        "Tra ve danh sach san pham gom ten, gia, shop, link va trang thai con hang."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Tu khoa tim kiem, vi du: 'PC gaming RTX 4070', 'laptop Dell XPS 15'",
            },
            "max_results": {
                "type": "integer",
                "description": "So luong ket qua toi da can tra ve",
                "default": 5,
            },
        },
        "required": ["query"],
    },
}


def run(query: str, max_results: int = 5) -> str:
    dataset = pick_dataset(query)
    results = dataset[:max_results]
    return json.dumps(
        {
            "query": query,
            "total_found": len(results),
            "results": results,
            "source_note": "Du lieu mo phong tu GeForce.vn, Phong Vu, FPT Shop, The Gioi Di Dong, Hoang Ha Mobile",
        },
        ensure_ascii=False,
        indent=2,
    )
