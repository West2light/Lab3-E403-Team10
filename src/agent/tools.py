"""
tools.py - Định nghĩa các tools mà Agent có thể sử dụng.
Hỗ trợ cả schema cho OpenAI API và hàm thực thi mock.
"""

from __future__ import annotations

import json
import re
from typing import Any

# ─────────────────────────────────────────────
# TOOL SCHEMAS
# ─────────────────────────────────────────────

TOOLS = [
    {
        "name": "search_pc_price",
        "description": (
            "Tìm kiếm giá PC / linh kiện máy tính. "
            "Trả về danh sách sản phẩm gồm tên, giá, shop, link và trạng thái còn hàng."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Từ khóa tìm kiếm, ví dụ: 'PC gaming RTX 4070', 'laptop Dell XPS 15'",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Số lượng kết quả tối đa cần trả về",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "sort_products",
        "description": (
            "Sắp xếp danh sách sản phẩm theo giá tăng dần hoặc giảm dần. "
            "Dùng khi người dùng muốn tìm rẻ nhất, đắt nhất, hoặc sort theo giá."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Từ khóa sản phẩm cần sắp xếp",
                },
                "sort_order": {
                    "type": "string",
                    "enum": ["asc", "desc"],
                    "description": "asc: tăng dần, desc: giảm dần",
                    "default": "asc",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Số lượng kết quả tối đa cần trả về",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "check_pc_compatibility",
        "description": (
            "Kiểm tra độ tương thích cơ bản giữa CPU, mainboard, RAM, GPU, PSU và case."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cpu": {"type": "string", "description": "Tên CPU"},
                "motherboard": {"type": "string", "description": "Tên mainboard"},
                "ram": {"type": "string", "description": "Thông tin RAM"},
                "gpu": {"type": "string", "description": "Tên GPU"},
                "psu": {"type": "string", "description": "Nguồn máy tính"},
                "case": {"type": "string", "description": "Tên case"},
            },
            "required": ["cpu", "motherboard"],
        },
    },
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

# ─────────────────────────────────────────────
# MOCK DATABASE
# ─────────────────────────────────────────────

_MOCK_DB: dict[str, list[dict[str, Any]]] = {
    "default": [
        {
            "name": "PC Gaming RTX 4070 / Ryzen 7 7700X / 32GB RAM",
            "price": "32.990.000 đ",
            "shop": "GeForce.vn",
            "url": "https://geforce.vn/may-tinh-bo/pc-gaming-rtx4070-r7-7700x",
            "in_stock": True,
        },
        {
            "name": "Máy tính đồng bộ Intel Core i5-13400 / RTX 3060 / 16GB",
            "price": "18.500.000 đ",
            "shop": "Phong Vũ",
            "url": "https://phongvu.vn/p/may-tinh-intel-i5-13400-rtx3060",
            "in_stock": True,
        },
        {
            "name": "PC Văn phòng Intel Core i3-13100 / 8GB / SSD 256GB",
            "price": "7.990.000 đ",
            "shop": "Thế Giới Di Động",
            "url": "https://www.thegioididong.com/tin-tuc/pc-van-phong-i3-13100",
            "in_stock": True,
        },
        {
            "name": "Gaming PC AMD Ryzen 9 7900X / RX 7900 XTX / 64GB DDR5",
            "price": "58.000.000 đ",
            "shop": "Hoàng Hà Mobile",
            "url": "https://hoanghamobile.com/pc-gaming/r9-7900x-rx7900xtx",
            "in_stock": False,
        },
        {
            "name": "Mini PC Intel NUC Core i7-1360P / 16GB / 512GB SSD",
            "price": "14.500.000 đ",
            "shop": "FPT Shop",
            "url": "https://fptshop.com.vn/may-tinh/mini-pc-intel-nuc-i7-1360p",
            "in_stock": True,
        },
    ],
    "laptop": [
        {
            "name": "Laptop Dell XPS 15 9530 / Core i7-13700H / RTX 4060 / 32GB",
            "price": "45.990.000 đ",
            "shop": "Dell Việt Nam",
            "url": "https://www.dell.com/vi-vn/shop/laptops/xps-15-laptop/spd/xps-15-9530-laptop",
            "in_stock": True,
        },
        {
            "name": "Laptop ASUS ROG Zephyrus G14 / Ryzen 9 / RTX 4060",
            "price": "38.500.000 đ",
            "shop": "ASUS Store",
            "url": "https://www.asus.com/vn/laptops/for-gaming/rog-zephyrus/asus-rog-zephyrus-g14-2024/",
            "in_stock": True,
        },
        {
            "name": "Laptop MacBook Pro 14 M3 Pro 18GB/512GB",
            "price": "52.990.000 đ",
            "shop": "Apple Việt Nam",
            "url": "https://www.apple.com/vn/shop/buy-mac/macbook-pro/14-inch",
            "in_stock": True,
        },
    ],
    "ram": [
        {
            "name": "RAM Kingston Fury Beast DDR5 32GB (2x16GB) 5600MHz",
            "price": "2.890.000 đ",
            "shop": "Phong Vũ",
            "url": "https://phongvu.vn/p/ram-kingston-fury-beast-ddr5-32gb-5600mhz",
            "in_stock": True,
        },
        {
            "name": "RAM Corsair Vengeance DDR5 64GB (2x32GB) 6000MHz",
            "price": "5.490.000 đ",
            "shop": "GeForce.vn",
            "url": "https://geforce.vn/ram/corsair-vengeance-ddr5-64gb-6000mhz",
            "in_stock": True,
        },
    ],
    "rtx": [
        {
            "name": "VGA NVIDIA GeForce RTX 4070 SUPER 12GB GDDR6X",
            "price": "16.990.000 đ",
            "shop": "GeForce.vn",
            "url": "https://geforce.vn/vga/rtx-4070-super",
            "in_stock": True,
        },
        {
            "name": "VGA ASUS ROG STRIX RTX 4080 SUPER 16GB OC",
            "price": "28.500.000 đ",
            "shop": "Phong Vũ",
            "url": "https://phongvu.vn/p/vga-asus-rog-strix-rtx4080-super-16gb",
            "in_stock": True,
        },
    ],
}


def _pick_dataset(query: str) -> list[dict[str, Any]]:
    q = query.lower()
    if any(k in q for k in ["laptop", "macbook", "notebook", "xps", "rog", "zephyrus"]):
        return _MOCK_DB["laptop"]
    if any(k in q for k in ["ram", "ddr", "memory"]):
        return _MOCK_DB["ram"]
    if any(k in q for k in ["rtx", "rx ", "vga", "gpu", "card màn hình", "card man hinh"]):
        return _MOCK_DB["rtx"]
    return _MOCK_DB["default"]


def _price_to_int(price_str: str) -> int:
    digits = re.sub(r"[^\d]", "", price_str)
    return int(digits) if digits else 0


# ─────────────────────────────────────────────
# DISPATCHER
# ─────────────────────────────────────────────

def execute_tool(tool_name: str, tool_input: dict[str, Any]) -> str:
    if tool_name == "search_pc_price":
        return _search_pc_price(**tool_input)
    if tool_name == "sort_products":
        return _sort_products(**tool_input)
    if tool_name == "check_pc_compatibility":
        return _check_pc_compatibility(**tool_input)
    return json.dumps({"error": f"Tool '{tool_name}' không tồn tại."}, ensure_ascii=False)


# ─────────────────────────────────────────────
# TOOL IMPLEMENTATIONS
# ─────────────────────────────────────────────

def _search_pc_price(query: str, max_results: int = 5) -> str:
    dataset = _pick_dataset(query)
    results = dataset[:max_results]
    return json.dumps(
        {
            "query": query,
            "total_found": len(results),
            "results": results,
            "source_note": "Dữ liệu mô phỏng từ GeForce.vn, Phong Vũ, FPT Shop, Thế Giới Di Động, Hoàng Hà Mobile",
        },
        ensure_ascii=False,
        indent=2,
    )


def _sort_products(query: str, sort_order: str = "asc", max_results: int = 5) -> str:
    dataset = _pick_dataset(query)
    reverse = sort_order.lower() == "desc"
    results = sorted(dataset, key=lambda item: _price_to_int(item.get("price", "0")), reverse=reverse)[:max_results]
    return json.dumps(
        {
            "query": query,
            "sort_order": sort_order,
            "total_found": len(results),
            "results": results,
            "source_note": "Dữ liệu mô phỏng đã được sắp xếp theo giá",
        },
        ensure_ascii=False,
        indent=2,
    )


def _detect_cpu_platform(cpu: str) -> dict[str, str]:
    text = cpu.lower()
    if "intel" in text or any(k in text for k in ["i3-", "i5-", "i7-", "i9-"]):
        socket = "LGA1700" if any(k in text for k in ["12", "13", "14", "121", "131", "141"]) else "Intel"
        return {"brand": "Intel", "socket": socket}
    if "ryzen" in text or "amd" in text:
        if any(k in text for k in ["7000", "7600", "7700", "7800", "7900", "7950"]):
            return {"brand": "AMD", "socket": "AM5"}
        return {"brand": "AMD", "socket": "AM4"}
    return {"brand": "Unknown", "socket": "Unknown"}


def _detect_motherboard_specs(motherboard: str) -> dict[str, str]:
    text = motherboard.lower()
    if any(k in text for k in ["b760", "h610", "z690", "z790", "b660"]):
        socket = "LGA1700"
    elif any(k in text for k in ["b650", "x670", "a620"]):
        socket = "AM5"
    elif any(k in text for k in ["b450", "b550", "x570", "a520"]):
        socket = "AM4"
    else:
        socket = "Unknown"

    ram_type = "DDR5" if "ddr5" in text else "DDR4" if "ddr4" in text else "Unknown"
    if "itx" in text:
        form_factor = "ITX"
    elif "matx" in text or "micro-atx" in text:
        form_factor = "mATX"
    else:
        form_factor = "ATX"
    return {"socket": socket, "ram_type": ram_type, "form_factor": form_factor}


def _detect_ram_type(ram: str) -> str:
    text = ram.lower()
    if "ddr5" in text:
        return "DDR5"
    if "ddr4" in text:
        return "DDR4"
    return "Unknown"


def _estimate_gpu_psu_requirement(gpu: str) -> int:
    text = gpu.lower()
    if "4090" in text:
        return 850
    if any(k in text for k in ["4080", "7900 xtx"]):
        return 750
    if any(k in text for k in ["4070", "7800 xt", "7900 gre"]):
        return 650
    if any(k in text for k in ["4060", "3060", "7600 xt"]):
        return 550
    return 500


def _extract_wattage(psu: str) -> int:
    match = re.search(r"(\d{3,4})\s*w", psu.lower())
    return int(match.group(1)) if match else 0


def _case_supports_form_factor(case: str, form_factor: str) -> bool:
    text = case.lower()
    if not text:
        return True
    if "e-atx" in text:
        return True
    if "atx" in text:
        return form_factor in {"ATX", "mATX", "ITX"}
    if "matx" in text or "micro-atx" in text:
        return form_factor in {"mATX", "ITX"}
    if "itx" in text:
        return form_factor == "ITX"
    return True


def _check_pc_compatibility(
    cpu: str,
    motherboard: str,
    ram: str = "",
    gpu: str = "",
    psu: str = "",
    case: str = "",
) -> str:
    cpu_specs = _detect_cpu_platform(cpu)
    motherboard_specs = _detect_motherboard_specs(motherboard)
    checks: list[dict[str, Any]] = []
    issues: list[str] = []

    cpu_main_ok = (
        cpu_specs["socket"] != "Unknown"
        and motherboard_specs["socket"] != "Unknown"
        and cpu_specs["socket"] == motherboard_specs["socket"]
    )
    checks.append(
        {
            "component_pair": "CPU - Motherboard",
            "compatible": cpu_main_ok,
            "details": f"CPU socket {cpu_specs['socket']} {'khớp' if cpu_main_ok else 'không khớp'} với mainboard socket {motherboard_specs['socket']}",
        }
    )
    if not cpu_main_ok:
        issues.append("CPU và mainboard khác socket.")

    if ram:
        ram_type = _detect_ram_type(ram)
        ram_ok = ram_type == "Unknown" or motherboard_specs["ram_type"] == "Unknown" or ram_type == motherboard_specs["ram_type"]
        checks.append(
            {
                "component_pair": "RAM - Motherboard",
                "compatible": ram_ok,
                "details": f"RAM {ram_type} {'phù hợp' if ram_ok else 'không phù hợp'} với mainboard hỗ trợ {motherboard_specs['ram_type']}",
            }
        )
        if not ram_ok:
            issues.append("RAM và mainboard dùng khác chuẩn DDR.")

    if gpu and psu:
        required_wattage = _estimate_gpu_psu_requirement(gpu)
        actual_wattage = _extract_wattage(psu)
        psu_ok = actual_wattage == 0 or actual_wattage >= required_wattage
        checks.append(
            {
                "component_pair": "GPU - PSU",
                "compatible": psu_ok,
                "details": f"GPU nên dùng nguồn tối thiểu khoảng {required_wattage}W, PSU hiện tại: {actual_wattage or 'không xác định'}W",
            }
        )
        if not psu_ok:
            issues.append("PSU có thể không đủ công suất cho GPU.")

    if case:
        case_ok = _case_supports_form_factor(case, motherboard_specs["form_factor"])
        checks.append(
            {
                "component_pair": "Case - Motherboard",
                "compatible": case_ok,
                "details": f"Case {'hỗ trợ' if case_ok else 'không hỗ trợ'} form factor {motherboard_specs['form_factor']}",
            }
        )
        if not case_ok:
            issues.append("Case không phù hợp kích thước mainboard.")

    overall = all(item["compatible"] for item in checks) if checks else False
    return json.dumps(
        {
            "overall_compatible": overall,
            "summary": "Cấu hình tương thích cơ bản." if overall else "Cấu hình có điểm chưa tương thích.",
            "checks": checks,
            "issues": issues,
        },
        ensure_ascii=False,
        indent=2,
    )
