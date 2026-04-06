# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Vương Hoàng Giang
- **Student ID**: 2A202600349
- **Date**: 6/4/2026

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implementated**: src/agent/tools.py và cập nhật SYSTEM_PROMPT
- **Code Highlights**: 
[Đã thiết kế và tích hợp tool calculate_psu_wattage cho phép Agent tự động tính toán công suất nguồn.](../../src/agent/tools.py)
- **Documentation**: Tool này được tích hợp vào vòng lặp ReAct thông qua mảng TOOLS_OPENAI. Khi người dùng đưa ra một danh sách linh kiện LLM sẽ tạo ra một Thought phân tích yêu cầu, sau đó kích hoạt Action gọi hàm calculate_psu_wattage với tham số đầu vào là một mảng các linh kiện. Hệ thống Python thực thi hàm, trả về chuỗi JSON chứa mức công suất đề xuất để LLM đọc và tổng hợp thành câu trả lời cuối cùng cho người dùng.

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: [e.g., Agent caught in an infinite loop with `Action: search(None)`]
- **Log Source**: [Link or snippet from `logs/YYYY-MM-DD.log`]
- **Diagnosis**: [Why did the LLM do this? Was it the prompt, the model, or the tool spec?]
- **Solution**: [How did you fix it? (e.g., updated `Thought` examples in the system prompt)]

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: Khối Thought giúp ReAct Agent vượt trội hoàn toàn so với Chatbot thông thường khi xử lý các bài toán gồm nhiều bước. Chatbot thường sẽ có xu hướng "đoán" hoặc "bịa" một mức công suất nguồn ngẫu nhiên. Ngược lại, ReAct Agent nhờ có khối Thought đã biết dừng lại, tách bóc danh sách linh kiện từ câu hỏi, quyết định gọi tool calculate_psu_wattage, rồi mới kết luận. Sự "suy nghĩ chậm" này giúp kết quả chính xác và có cơ sở hơn.
2.  **Reliability**: Tuy nhiên, Agent đôi khi hoạt động tệ hơn Chatbot ở tốc độ phản hồi và sự linh hoạt. Nếu người dùng hỏi những câu mập mờ, một Chatbot thuần túy sẽ ngay lập tức đưa ra các bước chẩn đoán chung chung rất mượt mà. Trong khi đó, ReAct Agent có thể bị "bối rối" và cố gắng gọi tool tính công suất nguồn với một danh sách linh kiện rỗng, dẫn đến lỗi hoặc làm chậm thời gian phản hồi một cách không cần thiết.
3.  **Observation**: Phản hồi từ môi trường đóng vai trò là "mỏ neo" sự thật. Khi tool trả về JSON {"recommended_psu_wattage": 850}, observation này lập tức ép LLM phải dựa vào con số 850W để tư vấn, ngăn chặn triệt để việc LLM tự bịa ra một mức công suất khác.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: Logic tính công suất bằng if/else (như code hiện tại) khó duy trì khi có linh kiện mới ra mắt. Giải pháp là tích hợp việc gọi API từ một cơ sở dữ liệu thực hoặc Vector DB để tra cứu chính xác mức TDP của từng linh kiện riêng biệt thay vì hardcode.
- **Safety**: Cần thêm một lớp tiền xử lý (Input Validation) để giới hạn số lượng linh kiện truyền vào nhằm ngăn chặn việc tấn công làm cạn kiệt tài nguyên tính toán nếu người dùng cố tình chèn hàng ngàn dòng linh kiện rác vào prompt.  
- **Performance**: Áp dụng cơ chế Caching cho Tool. Hàng ngàn người dùng có thể cùng hỏi về một cấu hình quốc dân như "i5 12400F + RTX 3060". Việc lưu lại kết quả của các bộ linh kiện phổ biến này sẽ giúp Agent bỏ qua bước thực thi Tool ở backend, giảm chi phí API và tăng tốc độ phản hồi gần như tức thì.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
