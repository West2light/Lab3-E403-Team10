# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Phạm Anh Dũng
- **Student ID**: 2A202600251
- **Date**: 06/04/2026

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implementated**: `src/tools/sort_product.py`
- **Code Highlights**: 
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
- **Documentation**: 
Tool sort_products được xây dựng để cho phép agent sắp xếp danh sách sản phẩm theo giá thay vì chỉ tìm kiếm và liệt kê thô. Tool này đặc biệt hữu ích khi người dùng hỏi theo các dạng như:
 - xếp từ rẻ đến đắt
 - sắp xếp theo giá giảm dần
 - cho tôi sản phẩm đắt nhất
 - hiển thị các laptop theo thứ tự giá
Nhờ đó, agent không chỉ dừng ở bước retrieval mà còn có thêm một bước xử lý dữ liệu, đúng tinh thần của ReAct Agent.

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: 
Lỗi khi agent không sử dụng tool sort_product, mặc dù câu hỏi của người dùng yêu cầu rõ ràng việc sắp xếp.
- **Log Source**: [Link or snippet from `logs/YYYY-MM-DD.log`]
- **Diagnosis**:
Nguyên nhân ở thiết kế prompt. Ban đầu system_prompt có rule ` Luôn dùng tool `search_pc_price` để tìm kiếm trước khi trả lời `.
- **Solution**:
Phân vai rõ ràng cho từng tool:
 "Dùng tool `search_pc_price` để tìm sản phẩm. 
  Dùng tool `sort_products` khi người dùng muốn sắp xếp theo giá tăng dần hoặc giảm dần.
  Dùng tool `check_pc_compatibility` khi người dùng muốn kiểm tra CPU, mainboard, RAM, GPU, PSU, case có tương thích hay không.
  Dùng tool `get_top_cpu_rankings` khi người dùng hỏi CPU mạnh nhất, top CPU, hoặc muốn xem bảng xếp hạng CPU hiện tại."

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: 
ReAct Agent vượt trội hơn chatbot ở điểm: có bước `Thought`, có khả năng chia nhỏ vấn đề, xử lý theo các tool được lập trình sẵn. Trong khi đó, chatbot trả lời trực tiếp, sẽ có xu hướng "đoán" hoặc "bịa".
2.  **Reliability**: 
Agent có thể kém hơn chatbot nếu như system_prompt thiết kế chưa tốt, mô tả tool không rõ ràng dẫn đến tool không được sử dụng. ReAct Agent có nhiều loop, nhiều call LLM khiến cho tốc độ phản hồi và độ linh hoạt thấp hơn chatbot
- 
3.  **Observation**: 
Observation là phần quan trọng nhất giúp agent học từ môi trường và điều chỉnh hành vi. Cung cấp dữ liệu thực (ground truth) và là input cho bước reasoning tiếp theo giúp output chính xác, nhất quán hơn.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: 
Khi số lượng sản phẩm lớn, việc sort trực tiếp trong memory như hiện tại sẽ không còn tối ưu. Khi đó nên chuyển việc sắp xếp xuống tầng database hoặc search engine, ví dụ dùng truy vấn có ORDER BY price ASC/DESC, để giảm tải cho agent layer.
- **Safety**: 
Bổ sung lớp validation dữ liệu trước khi sort: kiểm tra trường giá có parse được không, có thiếu dữ liệu không, và có cần loại bỏ các sản phẩm không hợp lệ khỏi kết quả hay không.
- **Performance**: 
Trong hệ thống lớn hơn, sort_products nên là một tool chuyên biệt cho bước “re-rank/sort”, còn bước retrieve nên do tool khác đảm nhiệm. Thiết kế tách pha này sẽ giúp hệ thống hiệu quả hơn và rõ vai trò hơn.

---

