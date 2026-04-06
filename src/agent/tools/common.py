from __future__ import annotations

import re
from typing import Any


MOCK_DB: dict[str, list[dict[str, Any]]] = {
    "default": [
        {
            "name": "PC Gaming RTX 4070 / Ryzen 7 7700X / 32GB RAM",
            "price": "32.990.000 d",
            "shop": "GeForce.vn",
            "url": "https://geforce.vn/may-tinh-bo/pc-gaming-rtx4070-r7-7700x",
            "in_stock": True,
        },
        {
            "name": "May tinh dong bo Intel Core i5-13400 / RTX 3060 / 16GB",
            "price": "18.500.000 d",
            "shop": "Phong Vu",
            "url": "https://phongvu.vn/p/may-tinh-intel-i5-13400-rtx3060",
            "in_stock": True,
        },
        {
            "name": "PC Van phong Intel Core i3-13100 / 8GB / SSD 256GB",
            "price": "7.990.000 d",
            "shop": "The Gioi Di Dong",
            "url": "https://www.thegioididong.com/tin-tuc/pc-van-phong-i3-13100",
            "in_stock": True,
        },
        {
            "name": "Gaming PC AMD Ryzen 9 7900X / RX 7900 XTX / 64GB DDR5",
            "price": "58.000.000 d",
            "shop": "Hoang Ha Mobile",
            "url": "https://hoanghamobile.com/pc-gaming/r9-7900x-rx7900xtx",
            "in_stock": False,
        },
        {
            "name": "Mini PC Intel NUC Core i7-1360P / 16GB / 512GB SSD",
            "price": "14.500.000 d",
            "shop": "FPT Shop",
            "url": "https://fptshop.com.vn/may-tinh/mini-pc-intel-nuc-i7-1360p",
            "in_stock": True,
        },
    ],
    "laptop": [
        {
            "name": "Laptop Dell XPS 15 9530 / Core i7-13700H / RTX 4060 / 32GB",
            "price": "45.990.000 d",
            "shop": "Dell Viet Nam",
            "url": "https://www.dell.com/vi-vn/shop/laptops/xps-15-laptop/spd/xps-15-9530-laptop",
            "in_stock": True,
        },
        {
            "name": "Laptop ASUS ROG Zephyrus G14 / Ryzen 9 / RTX 4060",
            "price": "38.500.000 d",
            "shop": "ASUS Store",
            "url": "https://www.asus.com/vn/laptops/for-gaming/rog-zephyrus/asus-rog-zephyrus-g14-2024/",
            "in_stock": True,
        },
        {
            "name": "Laptop MacBook Pro 14 M3 Pro 18GB/512GB",
            "price": "52.990.000 d",
            "shop": "Apple Viet Nam",
            "url": "https://www.apple.com/vn/shop/buy-mac/macbook-pro/14-inch",
            "in_stock": True,
        },
    ],
    "ram": [
        {
            "name": "RAM Kingston Fury Beast DDR5 32GB (2x16GB) 5600MHz",
            "price": "2.890.000 d",
            "shop": "Phong Vu",
            "url": "https://phongvu.vn/p/ram-kingston-fury-beast-ddr5-32gb-5600mhz",
            "in_stock": True,
        },
        {
            "name": "RAM Corsair Vengeance DDR5 64GB (2x32GB) 6000MHz",
            "price": "5.490.000 d",
            "shop": "GeForce.vn",
            "url": "https://geforce.vn/ram/corsair-vengeance-ddr5-64gb-6000mhz",
            "in_stock": True,
        },
    ],
    "rtx": [
        {
            "name": "VGA NVIDIA GeForce RTX 4070 SUPER 12GB GDDR6X",
            "price": "16.990.000 d",
            "shop": "GeForce.vn",
            "url": "https://geforce.vn/vga/rtx-4070-super",
            "in_stock": True,
        },
        {
            "name": "VGA ASUS ROG STRIX RTX 4080 SUPER 16GB OC",
            "price": "28.500.000 d",
            "shop": "Phong Vu",
            "url": "https://phongvu.vn/p/vga-asus-rog-strix-rtx4080-super-16gb",
            "in_stock": True,
        },
    ],
}


def pick_dataset(query: str) -> list[dict[str, Any]]:
    normalized_query = query.lower()
    if any(
        keyword in normalized_query
        for keyword in ["pc gaming", "bo pc", "may tinh", "danh sach pc", "cau hinh pc"]
    ):
        return MOCK_DB["default"]
    if any(keyword in normalized_query for keyword in ["laptop", "macbook", "notebook", "xps", "rog", "zephyrus"]):
        return MOCK_DB["laptop"]
    if any(keyword in normalized_query for keyword in ["ram", "ddr", "memory"]):
        return MOCK_DB["ram"]
    if any(keyword in normalized_query for keyword in ["rtx", "rx ", "vga", "gpu", "card man hinh"]):
        return MOCK_DB["rtx"]
    return MOCK_DB["default"]


def price_to_int(price_str: str) -> int:
    digits = re.sub(r"[^\d]", "", price_str)
    return int(digits) if digits else 0
