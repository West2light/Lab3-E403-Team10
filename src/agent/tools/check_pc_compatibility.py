from __future__ import annotations

import json
import re
from typing import Any


TOOL_SPEC = {
    "name": "check_pc_compatibility",
    "description": "Kiem tra do tuong thich co ban giua CPU, mainboard, RAM, GPU, PSU va case.",
    "input_schema": {
        "type": "object",
        "properties": {
            "cpu": {"type": "string", "description": "Ten CPU"},
            "motherboard": {"type": "string", "description": "Ten mainboard"},
            "ram": {"type": "string", "description": "Thong tin RAM"},
            "gpu": {"type": "string", "description": "Ten GPU"},
            "psu": {"type": "string", "description": "Nguon may tinh"},
            "case": {"type": "string", "description": "Ten case"},
        },
        "required": ["cpu", "motherboard"],
    },
}


def detect_cpu_platform(cpu: str) -> dict[str, str]:
    text = cpu.lower()
    if "intel" in text or any(token in text for token in ["i3-", "i5-", "i7-", "i9-"]):
        socket = "LGA1700" if any(token in text for token in ["12", "13", "14", "121", "131", "141"]) else "Intel"
        return {"brand": "Intel", "socket": socket}
    if "ryzen" in text or "amd" in text:
        if any(token in text for token in ["7000", "7600", "7700", "7800", "7900", "7950"]):
            return {"brand": "AMD", "socket": "AM5"}
        return {"brand": "AMD", "socket": "AM4"}
    return {"brand": "Unknown", "socket": "Unknown"}


def detect_motherboard_specs(motherboard: str) -> dict[str, str]:
    text = motherboard.lower()
    if any(token in text for token in ["b760", "h610", "z690", "z790", "b660"]):
        socket = "LGA1700"
    elif any(token in text for token in ["b650", "x670", "a620"]):
        socket = "AM5"
    elif any(token in text for token in ["b450", "b550", "x570", "a520"]):
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


def detect_ram_type(ram: str) -> str:
    text = ram.lower()
    if "ddr5" in text:
        return "DDR5"
    if "ddr4" in text:
        return "DDR4"
    return "Unknown"


def estimate_gpu_psu_requirement(gpu: str) -> int:
    text = gpu.lower()
    if "4090" in text:
        return 850
    if any(token in text for token in ["4080", "7900 xtx"]):
        return 750
    if any(token in text for token in ["4070", "7800 xt", "7900 gre"]):
        return 650
    if any(token in text for token in ["4060", "3060", "7600 xt"]):
        return 550
    return 500


def extract_wattage(psu: str) -> int:
    match = re.search(r"(\d{3,4})\s*w", psu.lower())
    return int(match.group(1)) if match else 0


def case_supports_form_factor(case_name: str, form_factor: str) -> bool:
    text = case_name.lower()
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


def run(
    cpu: str,
    motherboard: str,
    ram: str = "",
    gpu: str = "",
    psu: str = "",
    case: str = "",
) -> str:
    cpu_specs = detect_cpu_platform(cpu)
    motherboard_specs = detect_motherboard_specs(motherboard)
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
            "details": (
                f"CPU socket {cpu_specs['socket']} "
                f"{'khop' if cpu_main_ok else 'khong khop'} voi mainboard socket {motherboard_specs['socket']}"
            ),
        }
    )
    if not cpu_main_ok:
        issues.append("CPU va mainboard khac socket.")

    if ram:
        ram_type = detect_ram_type(ram)
        ram_ok = (
            ram_type == "Unknown"
            or motherboard_specs["ram_type"] == "Unknown"
            or ram_type == motherboard_specs["ram_type"]
        )
        checks.append(
            {
                "component_pair": "RAM - Motherboard",
                "compatible": ram_ok,
                "details": (
                    f"RAM {ram_type} "
                    f"{'phu hop' if ram_ok else 'khong phu hop'} voi mainboard ho tro {motherboard_specs['ram_type']}"
                ),
            }
        )
        if not ram_ok:
            issues.append("RAM va mainboard dung khac chuan DDR.")

    if gpu and psu:
        required_wattage = estimate_gpu_psu_requirement(gpu)
        actual_wattage = extract_wattage(psu)
        psu_ok = actual_wattage == 0 or actual_wattage >= required_wattage
        checks.append(
            {
                "component_pair": "GPU - PSU",
                "compatible": psu_ok,
                "details": (
                    f"GPU nen dung nguon toi thieu khoang {required_wattage}W, "
                    f"PSU hien tai: {actual_wattage or 'khong xac dinh'}W"
                ),
            }
        )
        if not psu_ok:
            issues.append("PSU co the khong du cong suat cho GPU.")

    if case:
        case_ok = case_supports_form_factor(case, motherboard_specs["form_factor"])
        checks.append(
            {
                "component_pair": "Case - Motherboard",
                "compatible": case_ok,
                "details": f"Case {'ho tro' if case_ok else 'khong ho tro'} form factor {motherboard_specs['form_factor']}",
            }
        )
        if not case_ok:
            issues.append("Case khong phu hop kich thuoc mainboard.")

    overall = all(item["compatible"] for item in checks) if checks else False
    return json.dumps(
        {
            "overall_compatible": overall,
            "summary": "Cau hinh tuong thich co ban." if overall else "Cau hinh co diem chua tuong thich.",
            "checks": checks,
            "issues": issues,
        },
        ensure_ascii=False,
        indent=2,
    )
