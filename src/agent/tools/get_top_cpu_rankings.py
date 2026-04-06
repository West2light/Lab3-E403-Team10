from __future__ import annotations

import json


TOP_CPU_MOCK_DATA = [
    {
        "rank": 1,
        "name": "AMD Ryzen 9 9950X3D",
        "cpu_mark": 70221,
        "price_usd": 675.59,
        "brand": "AMD",
        "segment": "desktop",
    },
    {
        "rank": 2,
        "name": "Intel Core Ultra 9 285K",
        "cpu_mark": 67325,
        "price_usd": 557.00,
        "brand": "Intel",
        "segment": "desktop",
    },
    {
        "rank": 3,
        "name": "AMD Ryzen 9 9950X",
        "cpu_mark": 65810,
        "price_usd": 519.00,
        "brand": "AMD",
        "segment": "desktop",
    },
    {
        "rank": 4,
        "name": "AMD Ryzen 9 7950X3D",
        "cpu_mark": 62318,
        "price_usd": 512.13,
        "brand": "AMD",
        "segment": "desktop",
    },
    {
        "rank": 5,
        "name": "AMD Ryzen 9 7950X",
        "cpu_mark": 62205,
        "price_usd": 456.08,
        "brand": "AMD",
        "segment": "desktop",
    },
    {
        "rank": 6,
        "name": "Intel Core Ultra 7 265K",
        "cpu_mark": 58701,
        "price_usd": 319.99,
        "brand": "Intel",
        "segment": "desktop",
    },
    {
        "rank": 7,
        "name": "Intel Core i9-14900K",
        "cpu_mark": 58394,
        "price_usd": 519.99,
        "brand": "Intel",
        "segment": "desktop",
    },
    {
        "rank": 8,
        "name": "Intel Core i9-14900KF",
        "cpu_mark": 58289,
        "price_usd": 465.99,
        "brand": "Intel",
        "segment": "desktop",
    },
    {
        "rank": 9,
        "name": "Intel Core i9-13900K",
        "cpu_mark": 58233,
        "price_usd": 539.99,
        "brand": "Intel",
        "segment": "desktop",
    },
    {
        "rank": 10,
        "name": "AMD Ryzen 9 9900X",
        "cpu_mark": 54440,
        "price_usd": 389.99,
        "brand": "AMD",
        "segment": "desktop",
    },
]


TOOL_SPEC = {
    "name": "get_top_cpu_rankings",
    "description": (
        "Lay danh sach cac dong CPU manh nhat hien tai tu mock data da duoc cap nhat. "
        "Dung khi nguoi dung hoi CPU nao manh nhat, top CPU, hoac muon xem bang xep hang CPU."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "So luong CPU toi da can tra ve",
                "default": 10,
            },
            "brand": {
                "type": "string",
                "enum": ["all", "AMD", "Intel"],
                "description": "Loc theo hang CPU neu can",
                "default": "all",
            },
        },
    },
}


def run(limit: int = 10, brand: str = "all") -> str:
    normalized_brand = brand.lower()
    results = TOP_CPU_MOCK_DATA
    if normalized_brand != "all":
        results = [cpu for cpu in results if cpu["brand"].lower() == normalized_brand]

    limited_results = results[: max(1, limit)]
    return json.dumps(
        {
            "ranking_type": "top_cpu",
            "total_found": len(limited_results),
            "results": limited_results,
            "source_note": (
                "Mock data duoc tong hop theo bang xep hang PassMark Common CPUs by CPU Mark, "
                "trang duoc cap nhat ngay 2026-04-06."
            ),
        },
        ensure_ascii=False,
        indent=2,
    )
