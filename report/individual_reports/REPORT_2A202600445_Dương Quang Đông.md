# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Dương Quang Đông
- **Student ID**: 2A202600445
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

_Trong bài thực hành này, tôi đã tham gia phát triển và hoàn thiện hệ thống Tool cũng như module Telemetry cho tác nhân ReAct._

- **Modules Implemented**:
  1. `src/agent/tools/get_top_cpu_rankings.py` (Công cụ truy xuất dữ liệu)
  2. `src/telemetry/logger.py` (Hệ thống tracking và logging)

- **Code Highlights**:
  - `get_top_cpu_rankings.py`: Xây dựng một danh sách dữ liệu giả lập (mock data) chứa thông tin xếp hạng CPU mạnh nhất (như Ryzen 9 9950X3D, Core i9-14900K). Tool được định nghĩa chi tiết qua `TOOL_SPEC`, hỗ trợ tham số `limit` (giới hạn số lượng) và `brand` (lọc theo nhà sản xuất).
  - `logger.py`: Triển khai `IndustryLogger` để hỗ trợ Structured Logging. Toàn bộ chu trình `Thought` -> `Action` -> `Observation` của Agent được ghi vào thư mục `logs/` dạng file JSON để dễ dàng query/parse sau này (thông qua hàm `log_agent_step` và `log_tool_call`). Console log cũng được tuỳ biến màu sắc.

- **Documentation**:
  - Tool lấy top CPU cho phép ReAct Agent tương tác với môi trường bên ngoài để trả lời các truy vấn giá và sức mạnh linh kiện (vd: "CPU AMD nào mạnh nhất?"), tránh hiện tượng ảo giác (hallucination) thường gặp ở baseline Chatbot.
  - Hệ thống `logger` đóng vai trò cốt lõi trong việc theo dõi luồng suy luận của agent, giúp team phân tích Token Usage, Latency và Debug quá trình ReAct Loop bị đứt gãy.

---

## II. Debugging Case Study (10 Points)

_Phân tích một lỗi điển hình gặp phải thông qua log ghi nhận được từ hệ thống._

- **Problem Description**: Agent bị mắc kẹt vào một vòng lặp vô hạn (Infinite Loop). Thay vì gọi được công cụ, model liên tục trả về `Thought` nhưng không trích xuất được `Action`, khiến số bước chạy đụng tới `max_iterations = 5` và ngắt.
- **Log Source**: File `logs/2026-04-06.log` báo dạng `PARSE_ERROR`.
  ````json
  {
    "event_type": "ERROR",
    "data": {
      "error_type": "PARSE_ERROR",
      "message": "Failed to parse tool call from output: ```json\\n{\\\"Action\\\": \\\"get_top_cpu_rankings\\\"}... ```"
    }
  }
  ````
- **Diagnosis**: Từ log, nhận thấy LLM đã trả về một khối định dạng JSON bị bọc bởi markdown backticks ` ```json `, dẫn đến hàm regex parsing hoặc JSON parsing bị lỗi không trích xuất được tên công cụ. Đây là lỗi phổ biến do prompt không áp đặt định dạng đầu ra đủ cứng rắn.
- **Solution**: Đã tiến hành điều chỉnh `SYSTEM_PROMPT` trong module AI Agent (e.g `agent.py`). Cụ thể bổ sung chặt chẽ chỉ dẫn định dạng:
  _"Output raw text only. NO markdown, NO code blocks. Exactly follow the Action: tool_name(arguments) format."_
  Đồng thời xây dựng thêm cơ chế chặn lỗi (try-catch) nhẹ để dọn dẹp các ký hiệu markdown không mong muốn trước khi parse JSON.

_Analyze a specific failure event you encountered during the lab using the logging system._

### Case Study 1: Out-of-Scope Query Handling

- **Problem Description**: Người dùng hỏi "Thời tiết hôm nay thế nào" - một câu hỏi hoàn toàn nằm ngoài phạm vi của Agent tư vấn PC.
- **Log Source**: `logs/2026-04-06.log` (timestamp: 14:51:09)

```json
{
  "user_query": "Thời tiết hôm nay thế nào",
  "total_steps": 1,
  "thought": "Xin lỗi, nhưng tôi không thể cung cấp thông tin thời tiết hiện tại..."
}
```

- **Diagnosis**: Agent xử lý đúng - không gọi tool không liên quan và từ chối lịch sự. Điều này cho thấy SYSTEM_PROMPT đã định nghĩa rõ phạm vi hoạt động.
- **Solution**: Không cần fix - đây là hành vi mong đợi. Agent nhận diện câu hỏi ngoài scope và trả lời phù hợp mà không lãng phí token vào việc gọi tool.

### Case Study 2: Ambiguous Query với Context Shift

- **Problem Description**: Người dùng hỏi "Thời tiết hôm nay có thích hợp để mua PC không?" - câu hỏi kết hợp topic ngoài scope (thời tiết) với topic trong scope (mua PC).
- **Log Source**: `logs/2026-04-06.log` (timestamp: 14:51:36)

```json
{
  "user_query": "Thời tiết hôm nay có thích hợp để mua PC không ?",
  "thought": "Mua PC không phụ thuộc vào thời tiết mà phụ thuộc nhiều hơn vào nhu cầu sử dụng, ngân sách và các chương trình khuyến mãi đang có..."
}
```

- **Diagnosis**: Agent thông minh nhận ra ý định thực sự của người dùng là hỏi về mua PC, không phải hỏi thời tiết. Nó đã redirect câu trả lời về topic PC một cách tự nhiên.
- **Solution**: Đây là ví dụ về "soft rejection" - Agent không từ chối thẳng mà khéo léo chuyển hướng cuộc trò chuyện về đúng domain expertise của nó.

### Case Study 3: Vague Query Without Sufficient Context

- **Problem Description**: Người dùng chỉ gõ "dưới 10 củ" mà không cung cấp context về loại sản phẩm.
- **Log Source**: `logs/2026-04-06.log` (timestamp: 14:52:07)

```json
{
  "user_query": "dưới 10 củ",
  "total_steps": 1,
  "thought": "Bạn đang tìm kiếm sản phẩm gì dưới 10 triệu đồng? Đó có thể là PC, laptop, hay linh kiện máy tính cụ thể nào khác?"
}
```

- **Diagnosis**: Agent nhận biết câu query thiếu thông tin và chủ động hỏi lại thay vì đoán mò. Tuy nhiên, Agent không gọi tool `sort_products` với filter giá, có thể là do thiếu context về loại sản phẩm.
- **Solution**: Đây là hành vi đúng. Trong tương lai có thể thêm multi-turn memory để Agent nhớ context từ các câu trước (ví dụ: người dùng đã nói "tư vấn mua PC" ở câu trước).

### Case Study 4: Single-Word Query Edge Case

- **Problem Description**: Người dùng chỉ gõ "PC" - query cực ngắn và không rõ ý định.
- **Log Source**: `logs/2026-04-06.log` (timestamp: 14:52:22)

```json
{
  "user_query": "PC",
  "total_steps": 1,
  "total_duration_ms": 1370.89
}
```

- **Diagnosis**: Agent phản hồi nhanh (1.37s) và hỏi lại để clarify. Điểm đáng chú ý là nó KHÔNG cố gắng gọi `search_products` hay `sort_products` với keyword "PC" đơn thuần - tránh việc trả về kết quả không liên quan.
- **Solution**: Hành vi phù hợp. Có thể cải thiện bằng cách thêm quick suggestions như "Bạn muốn xem PC gaming hay PC văn phòng?".

### Case Study 5: Successful Tool Chain Execution

- **Problem Description**: Người dùng hỏi "PC hiện tại giá cao nhất là bao nhiêu?" - query rõ ràng, có thể action được.
- **Log Source**: `logs/2026-04-06.log` (timestamp: 14:22:59 - 14:23:52)

```json
{
  "step_index": 1,
  "action_tool": "sort_products",
  "action_input": { "query": "PC", "sort_order": "desc", "max_results": 1 },
  "duration_ms": 1848.3
}
```

- **Diagnosis**: Đây là flow lý tưởng của ReAct Agent:
  1. **Step 1**: Parse query → Quyết định gọi `sort_products` với `sort_order: desc` để lấy giá cao nhất
  2. **Step 2**: Nhận observation từ tool → Tổng hợp thành câu trả lời tự nhiên
- **Solution**: Không cần fix - đây là benchmark case cho các query khác. Total duration ~4.6s cho 2 steps là acceptable performance.

---

### ReAct Agent Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER INPUT                                         │
│                    "PC hiện tại giá cao nhất là bao nhiêu?"                  │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 1: THOUGHT                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ LLM phân tích: "Người dùng muốn biết PC đắt nhất. Cần sort theo    │    │
│  │ giá giảm dần và lấy 1 kết quả."                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 1: ACTION                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Tool: sort_products                                                  │    │
│  │ Input: {"query": "PC", "sort_order": "desc", "max_results": 1}      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 1: OBSERVATION                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ {                                                                    │    │
│  │   "results": [{                                                      │    │
│  │     "name": "Gaming PC AMD Ryzen 9 7900X / RX 7900 XTX / 64GB",     │    │
│  │     "price": "58.000.000 đ",                                        │    │
│  │     "shop": "Hoàng Hà Mobile",                                      │    │
│  │     "in_stock": false                                               │    │
│  │   }]                                                                 │    │
│  │ }                                                                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 2: THOUGHT (Final Answer)                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ LLM tổng hợp: "PC có giá cao nhất là 58.000.000đ, là Gaming PC     │    │
│  │ AMD Ryzen 9 7900X với RX 7900 XTX và 64GB DDR5 RAM."               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FINAL RESPONSE                                     │
│  "PC hiện tại có giá cao nhất là **58.000.000 đ**. Đó là mẫu Gaming PC      │
│  AMD Ryzen 9 7900X / RX 7900 XTX / 64GB DDR5, được bán tại Hoàng Hà Mobile."│
└─────────────────────────────────────────────────────────────────────────────┘
```

### Performance Metrics từ Log

| Metric             | Value      |
| ------------------ | ---------- |
| Total Steps        | 2          |
| Total Duration     | 4633.35 ms |
| Input Tokens       | 1342       |
| Output Tokens      | 206        |
| Model              | gpt-4o     |
| Tool Call Duration | 1848.3 ms  |

---

### Multi-Tool Workflow: Top CPU Rankings

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   USER INPUT     │────▶│  TOOL CALL       │────▶│   FINAL ANSWER   │
│ "top cpu mạnh    │     │ get_top_cpu_     │     │  Top 10 CPU với  │
│  nhất hiện tại"  │     │ rankings(10)     │     │  benchmark scores│
└──────────────────┘     └──────────────────┘     └──────────────────┘
        │                        │                        │
        │                        │                        │
   1392.3ms                 6636.32ms                Total: 8031.45ms
  (LLM thinking)          (LLM formatting)          (2 steps)
```

## III. Personal Insights: Chatbot vs ReAct (10 Points)

_Reflect on the reasoning capability difference._

1.  **Reasoning**: Khối `Thought` giúp Agent vượt trội hoàn toàn so với Chatbot baseline ở các câu query phức hợp ("Tra CPU mạnh nhất hiện nay rồi so nó với CPU xếp thứ 2"). Agent học được cách "nghĩ" ra các đầu việc cần làm (1. Tìm ranking, 2. Bóc tách dữ liệu top 1 & top 2, 3. So sánh) và thi hành chuỗi lệnh, trong khi Chatbot thường chỉ sinh ra text từ pre-trained weight (thường là outdated data).
2.  **Reliability**: Trong các trường hợp hội thoại thông thường (chit-chat như "Chào bạn", "Agent làm được gì"), ReAct Agent lại bộc lộ hạn chế. Nó có xu hướng "nhầm tưởng" phải dùng công cụ, đi suy luận rườm rà (thậm chí gây lỗi parse) dẫn tới Latency (độ trễ) tăng cao bất thường chỉ để chào lại. Ở đây, baseline Chatbot chạy nhanh và chính xác hơn.
3.  **Observation**: Sự khác biệt lớn nhất nằm ở Feedback. Nhờ việc "nhìn" vào `Observation`, ReAct Agent có khả năng "tự sửa lỗi" (Self-Correction). Ví dụ, nếu nó gọi tool lọc CPU thương hiệu "Nvidia" và Observation báo không có trường tin nào, `Thought` kế tiếp của model sẽ là "Không có hãng Nvidia trong mảng CPU, phải đổi lại thành AMD hoặc Intel" thay vì cứng đầu nói dối người dùng.

---

## IV. Future Improvements (5 Points)

_How would you scale this for a production-level AI agent system?_

- **Scalability**: Cần ứng dụng Vector Database (như Chroma hay Pinecone) để lưu trữ descriptions của Tool. Thay vì nạp toàn bộ Tool vào Prompt ngay từ đầu (gây tốn Token và giảm Context Window), hệ thống sẽ _Retrieval Augmented Generation (RAG)_ lấy từ database ra những công cụ phù hợp với mô tả truy vấn.
- **Safety**: Xây dựng kiến trúc đồ thị (như LangGraph) để thêm một bước Guardrails / Supervisor AI nhằm đánh giá độ rủi ro hoặc ngắt vòng lặp ngay khi thấy Agent lặp lại y chang một hành động liên tiếp 2 lần, chống lãng phí API Cost.
- **Performance**: Triển khai thiết kế "Semantic Router". Một module phân loại chi phí thấp ở đầu vào sẽ phán đoán xem câu hỏi có thật sự cần dùng Tool không. Nếu chỉ là chitchat, luồng sẽ rẽ sang Chatbot đơn thuần (tiết kiệm LLM Call). Nếu phức tạp mới cấp quyền chạy module ReAct Agent.

---
