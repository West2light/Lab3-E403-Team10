# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: 2A202600201
- **Student ID**: Nguyễn Quốc Nam
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

Trong bài thực hành này, tôi đã xây dựng toàn bộ hệ thống từ đầu gồm 4 file chính: `tools.py`, `agent.py`, `chatbot.py` và `app.py` — triển khai đầy đủ vòng lặp ReAct Agent với tool calling, tracking và giao diện so sánh trực tiếp với chatbot baseline.

### Modules Implemented

1. `src/agent/tools.py` — Định nghĩa Tool và Mock Data
2. `src/agent/agent.py` — Vòng lặp ReAct Agent
3. `src/agent/chatbot.py` — Giao diện CLI
4. `src/agent/app.py` — Giao diện Streamlit so sánh 2 cột

---

### Code Highlights

#### `tools.py` — Tool Schema + Mock Database

Định nghĩa tool `search_pc_price` với hai schema song song:

- **`TOOLS`** (Anthropic format): sử dụng `input_schema` theo chuẩn Anthropic Messages API.
- **`TOOLS_OPENAI`** (OpenAI format): bọc trong `{"type": "function", "function": {...}}` theo chuẩn OpenAI Chat Completions API.

Mock database `_MOCK_DB` phân loại sản phẩm theo 4 nhóm (`default`, `laptop`, `ram`, `rtx`) và hàm `_pick_dataset()` tự động routing từ khóa tìm kiếm sang đúng dataset. Hàm `execute_tool()` đóng vai trò dispatcher, dễ mở rộng thêm tool mới mà không cần sửa agent.

```python
# Ví dụ dispatcher — thêm tool mới chỉ cần thêm elif
def execute_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "search_pc_price":
        return _search_pc_price(**tool_input)
    return json.dumps({"error": f"Tool '{tool_name}' không tồn tại."})
```

---

#### `agent.py` — Vòng lặp ReAct với OpenAI

Triển khai class `PCPriceAgent` chạy vòng lặp **Thought → Action → Observation** tối đa `MAX_ITERATIONS = 5` lần. Hai dataclass `Step` và `AgentTrace` lưu toàn bộ trạng thái từng bước:

```
Step(step_index, thought, action_tool, action_input, observation, duration_ms)
AgentTrace(user_query, steps[], final_answer, total_duration_ms, input_tokens, output_tokens)
```

**Stopping condition:** Model trả về `finish_reason == "stop"` (không còn tool call) hoặc vượt `MAX_ITERATIONS`.

**Safety boundaries:**
- Chỉ gọi tool có trong `TOOLS_OPENAI`, không thực thi code động.
- Mọi input/output đều được lưu vào `AgentTrace` để audit sau.

Callback `on_step` cho phép UI nhận dữ liệu realtime mà không cần polling:

```python
trace = agent.run(user_query, on_step=lambda step: print(step))
```

---

#### `chatbot.py` — CLI với ANSI Color Tracking

Giao diện dòng lệnh hiển thị từng bước của Agent với màu sắc phân biệt:

| Bước | Màu | Ký hiệu |
|---|---|---|
| Thought | Vàng | 💭 |
| Action | Tím | ⚡ |
| Observation | Xanh lá | 🔭 |
| Final Answer | Xanh cyan | ✅ |

Cuối mỗi lượt hiển thị thống kê: tổng thời gian (ms), số bước, tokens in/out.

---

#### `app.py` — Streamlit UI So Sánh 2 Cột

Giao diện web chia đôi màn hình để so sánh trực tiếp:

**Cột trái — Chatbot Baseline:** Gọi thẳng `gpt-4o` không có tool. Trả lời dựa trên kiến thức huấn luyện sẵn, không có dữ liệu giá thực tế.

**Cột phải — PC Price Agent:** Chạy vòng lặp ReAct đầy đủ, hiển thị từng bước có màu:
- 💭 Thought (nền vàng nhạt)
- ⚡ Action (nền xanh lá nhạt) với tên tool + query
- 🔭 Observation dạng product cards (tên, giá, shop, link, tình trạng kho)
- ✅ Final Answer (nền tím nhạt)

Cả hai cột đều hiển thị thống kê token và thời gian phản hồi.

**Fix lỗi `proxies`:** Phiên bản `httpx >= 0.28` bỏ tham số `proxies` khiến OpenAI SDK cũ crash. Giải pháp là truyền thẳng `httpx.Client()` sạch:

```python
from openai import OpenAI
import httpx

def get_client(key: str) -> OpenAI:
    return OpenAI(
        api_key=key,
        http_client=httpx.Client(),  # bypass proxy detection
    )
```

---

## II. Debugging Case Study (10 Points)

### Case Study 1: Lỗi `proxies` — httpx Version Conflict

**Problem:** Chạy `app.py` bị crash ngay khi khởi tạo `OpenAI()`:
```
Client.__init__() got an unexpected keyword argument 'proxies'
File "app.py", line 163, in get_client
    return OpenAI(api_key=key)
```

**Diagnosis:** OpenAI SDK tự động truyền `proxies=` vào `httpx.Client()` nhưng `httpx >= 0.28` đã xoá tham số này → `TypeError` khi khởi tạo. Lỗi xảy ra ở tầng HTTP client, không liên quan đến logic agent.

**Solution:** Truyền `http_client=httpx.Client()` thủ công để OpenAI SDK bỏ qua bước tạo client nội bộ có `proxies`. Đây là workaround chính thức được OpenAI khuyến nghị khi gặp xung đột version.

---

### Case Study 2: Agent Dùng `import openai` Thay Vì `import anthropic`

**Problem:** File `agent.py` ban đầu import sai thư viện:
```python
import openai
self.client = openai.OpenAI()
```
Trong khi phần gọi API `client.messages.create(system=...)` lại theo cú pháp Anthropic.

**Diagnosis:** Copy nhầm template từ phiên bản Anthropic sang, chỉ thay một phần mà không cập nhật toàn bộ. Lỗi không bị phát hiện tại thời điểm import vì cả hai thư viện đều cài đặt trong môi trường.

**Solution:** Chuyển hoàn toàn sang OpenAI SDK với 3 thay đổi cốt lõi:

| Điểm | Anthropic | OpenAI |
|---|---|---|
| Client | `anthropic.Anthropic()` | `openai.OpenAI()` |
| Gọi API | `client.messages.create(system=...)` | `client.chat.completions.create(messages=[{"role":"system",...}])` |
| Stopping | `stop_reason == "end_turn"` | `finish_reason == "stop"` |
| Tool result | `type: "tool_result"` trong user message | `role: "tool"` message riêng |

---

### Case Study 3: Tool Schema Không Tương Thích Giữa Hai Provider

**Problem:** Tool schema viết cho Anthropic (`input_schema`) không hoạt động với OpenAI API, gây lỗi `400 Bad Request`.

**Diagnosis:** Anthropic và OpenAI dùng cấu trúc schema khác nhau hoàn toàn. Anthropic dùng trực tiếp `input_schema` ở root, còn OpenAI yêu cầu bọc trong `{"type": "function", "function": {..., "parameters": ...}}`.

**Solution:** Tách thành hai schema riêng trong `tools.py` — `TOOLS` cho Anthropic và `TOOLS_OPENAI` cho OpenAI — dùng cùng một `execute_tool()` dispatcher ở tầng thực thi.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

**Reasoning:** Khối `Thought` giúp Agent vượt trội hoàn toàn so với Chatbot baseline ở các câu query cần dữ liệu thực tế. Khi hỏi "PC gaming RTX 4070 giá bao nhiêu?", Chatbot chỉ ước tính từ dữ liệu huấn luyện ("khoảng 28–35 triệu") trong khi Agent gọi tool và trả về đúng giá, shop, link, tình trạng kho. Sự khác biệt càng rõ với các query phức hợp đòi hỏi nhiều bước suy luận.

**Reliability:** ReAct Agent bộc lộ hạn chế ở các câu chitchat đơn giản. Nó có xu hướng "nghĩ" quá nhiều trước khi trả lời, thậm chí cố gọi tool không cần thiết, dẫn đến latency cao hơn baseline 2–3 lần chỉ để chào lại. Đây là điểm mà chatbot đơn thuần chiếm ưu thế rõ ràng.

**Observation:** Sự khác biệt căn bản nhất nằm ở khả năng **self-correction**. Nhờ nhìn vào `Observation`, nếu tool trả về kết quả rỗng, `Thought` tiếp theo của Agent sẽ tự điều chỉnh query thay vì bịa số liệu như Chatbot. Đây là yếu tố quan trọng nhất khi xây dựng hệ thống AI đáng tin cậy cho domain tư vấn sản phẩm.

---

## IV. Future Improvements (5 Points)

**Scalability:** Thay mock database bằng real-time scraper (Phong Vũ, GeForce.vn) hoặc tích hợp Google Custom Search API. Áp dụng Vector Database (Chroma, Pinecone) để RAG tool descriptions thay vì nạp toàn bộ vào prompt — giảm token consumption khi số lượng tool tăng lên.

**Safety:** Thêm **Semantic Router** ở đầu vào: một classifier nhẹ phân loại câu hỏi trước khi quyết định route sang Chatbot (chitchat) hay Agent (query cần tool). Tránh lãng phí API call cho những câu hỏi đơn giản không cần tool calling.

**Performance:** Triển khai **streaming response** trong Streamlit — hiển thị từng token ngay khi model sinh ra thay vì đợi toàn bộ response. Kết hợp với `async` để hai cột có thể gọi API song song thay vì tuần tự.

**Observability:** Xây dựng module logging cấu trúc (structured logging) lưu toàn bộ `AgentTrace` ra file JSON theo ngày. Mỗi entry gồm timestamp, query, steps, token usage và latency — phục vụ phân tích bottleneck và debug khi Agent bị loop vô hạn.

---