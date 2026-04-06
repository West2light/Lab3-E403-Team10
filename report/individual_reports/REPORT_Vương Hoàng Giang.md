# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Vương Hoàng Giang
- **Student ID**: 2A202600349
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implementated**: `src/telemetry/logger.py`, `scripts/evaluate_chatbot_vs_agent.py`, `report/group_report/artifacts/evaluation_cases.json`
- **Code Highlights**: Xây dựng benchmark có thể chạy lại để so sánh `baseline`, `agent_v1`, `agent_v2`; bổ sung test case theo đúng tinh thần hướng dẫn gồm câu hỏi đơn giản, truy vấn cần tool, và truy vấn multi-step. Đồng thời sửa logger để in UTF-8 ổn định trên Windows console.
- **Documentation**: Benchmark script chạy từng case cho 3 mode, chấm pass/fail theo keyword và expected tool, rồi xuất `evaluation_results.json` và `evaluation_summary.md`. Structured logging đóng vai trò nền tảng cho phần RCA trong group report.

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: Script benchmark ban đầu bị lỗi `UnicodeEncodeError` khi console logger in tiếng Việt trên Windows, làm gián đoạn quá trình sinh artifact.
- **Log Source**: lỗi xuất hiện khi chạy `python scripts/evaluate_chatbot_vs_agent.py`
- **Diagnosis**: File log JSON ghi UTF-8 ổn, nhưng console handler dùng encoding mặc định của terminal nên không encode được một số ký tự tiếng Việt.
- **Solution**: Cập nhật `src/telemetry/logger.py` để `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` trước khi gắn console handler. Sau khi sửa, benchmark chạy hết và tạo ra file artifact đầy đủ cho report.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: Từ góc nhìn đánh giá, ReAct có thể đo được rõ ràng hơn vì mỗi bước có trace, còn chatbot chỉ có output cuối nên khó biết nó “nghĩ” sai ở đâu.
2.  **Reliability**: Agent có thể kém chatbot ở cost và latency, nhưng bù lại dễ kiểm soát và dễ debug hơn nhiều.
3.  **Observation**: Observation không chỉ giúp model ra quyết định mà còn giúp con người kiểm toán toàn bộ pipeline sau khi chạy benchmark.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: Mở rộng benchmark suite thành nhiều file scenario theo nhóm task và chạy tự động trong CI
- **Safety**: Gắn thêm rubric đánh giá hallucination và invalid tool usage thay vì chỉ match keyword
- **Performance**: Ghi riêng latency per-step, latency per-tool, và token ratio để tối ưu theo từng loại truy vấn

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
