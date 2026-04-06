# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Lê Trung
- **Student ID**: 2A202600174
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implementated**: `src/agent/tools/check_pc_compatibility.py`
- **Code Highlights**: Xây dựng tool `check_pc_compatibility` để kiểm tra socket CPU-mainboard, chuẩn RAM, công suất PSU cho GPU, và form factor case. Ngoài ra còn refactor file `tools.py` monolithic thành package `src/agent/tools/` để dễ bảo trì và mở rộng.
- **Documentation**: Tool compatibility trả về JSON có `overall_compatible`, `summary`, `checks`, `issues`. Việc tách tool thành package giúp registry, dispatcher, mock data, và business logic được phân tách rõ ràng trong ReAct loop.

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: Với cấu hình `Ryzen 7 7700X + MSI B760M DDR4 + DDR5 32GB`, chatbot thường trả lời chung chung, còn hệ thống cũ khó mở rộng khi logic compatibility nằm lẫn trong một file lớn.
- **Log Source**: `logs/2026-04-06.log`, các event `TOOL_CALL`, `AGENT_STEP`, `AGENT_COMPLETE` cho case compatibility
- **Diagnosis**: Vấn đề chính là maintainability. Khi tool spec, dispatcher, mock data và helper cùng nằm trong một file, việc sửa một luật compatibility rất dễ ảnh hưởng phần khác.
- **Solution**: Tách tool thành module riêng, giữ helper detect socket/DDR/PSU trong `check_pc_compatibility.py`, còn registry ở `__init__.py`. Sau refactor, benchmark case compatibility pass ổn định.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: `Thought` giúp agent nhận ra truy vấn compatibility là bài toán luật logic chứ không chỉ là tư vấn bằng cảm tính.
2.  **Reliability**: Nếu logic tool viết sơ sài hoặc tool spec không rõ, agent có thể đưa ra câu trả lời sai nhưng trông rất thuyết phục.
3.  **Observation**: Observation dạng `checks` và `issues` làm bước trả lời cuối có cấu trúc hơn rất nhiều so với chatbot.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: Tách luật compatibility ra thành data rules hoặc knowledge base thay vì hard-code hoàn toàn trong Python
- **Safety**: Bổ sung confidence score cho từng check để tránh khẳng định quá mức với các linh kiện khó nhận diện
- **Performance**: Cache kết quả cho các cấu hình phổ biến và thêm chuẩn hóa tên linh kiện trước khi kiểm tra

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
