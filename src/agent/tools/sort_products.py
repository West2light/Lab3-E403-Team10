from __future__ import annotations

import json

from .common import pick_dataset, price_to_int


TOOL_SPEC = {
    "name": "sort_products",
    "description": (
        "Sap xep danh sach san pham theo gia tang dan hoac giam dan. "
        "Dung khi nguoi dung muon tim re nhat, dat nhat, hoac sort theo gia."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Tu khoa san pham can sap xep",
            },
            "sort_order": {
                "type": "string",
                "enum": ["asc", "desc"],
                "description": "asc: tang dan, desc: giam dan",
                "default": "asc",
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


def run(query: str, sort_order: str = "asc", max_results: int = 5) -> str:
    dataset = pick_dataset(query)
    reverse = sort_order.lower() == "desc"
    results = sorted(
        dataset,
        key=lambda item: price_to_int(item.get("price", "0")),
        reverse=reverse,
    )[:max_results]
    return json.dumps(
        {
            "query": query,
            "sort_order": sort_order,
            "total_found": len(results),
            "results": results,
            "source_note": "Du lieu mo phong da duoc sap xep theo gia",
        },
        ensure_ascii=False,
        indent=2,
    )
