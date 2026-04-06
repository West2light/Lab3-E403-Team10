import logging
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from logging.handlers import RotatingFileHandler


class JsonFormatter(logging.Formatter):
    """
    Formatter ghi log dưới dạng JSON – chuẩn industry cho structured logging.
    Mỗi dòng log là một JSON object, dễ dàng parse và phân tích.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        # Nếu có exception, thêm traceback vào log
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        # Nếu có extra data (ví dụ từ log_event), thêm vào JSON
        if hasattr(record, "event_data"):
            log_entry["event_type"] = getattr(record, "event_type", "UNKNOWN")
            log_entry["data"] = record.event_data
        return json.dumps(log_entry, ensure_ascii=False, default=str)


class ConsoleFormatter(logging.Formatter):
    """
    Formatter cho console với màu sắc giúp dễ đọc khi phát triển.
    """

    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[1;31m", # Bold Red
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return (
            f"{color}[{timestamp}] "
            f"{record.levelname:<8} "
            f"| {record.name} "
            f"| {record.getMessage()}{self.RESET}"
        )


class IndustryLogger:
    """
    Structured logger theo chuẩn industry:
    - Ghi log ra file dạng JSON (structured logging) với RotatingFileHandler
    - Ghi log ra console với format dễ đọc và có màu
    - Hỗ trợ log rotation để tránh file log quá lớn
    - Hỗ trợ UTF-8 encoding cho tiếng Việt
    - Tự động tạo thư mục logs nếu chưa có
    """

    def __init__(
        self,
        name: str = "AI-Lab-Agent",
        log_dir: Optional[str] = None,
        log_level: int = logging.DEBUG,
        max_bytes: int = 5 * 1024 * 1024,  # 5 MB mỗi file
        backup_count: int = 5,              # Giữ tối đa 5 file backup
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        
        # Tự động tìm thư mục gốc của project (cách thư mục telemetry 2 cấp: src/telemetry)
        if log_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__)) 
            project_root = os.path.dirname(os.path.dirname(current_dir)) 
            self.log_dir = os.path.join(project_root, "logs")
        else:
            self.log_dir = log_dir

        # Tránh thêm handler trùng lặp nếu logger đã được khởi tạo
        if self.logger.handlers:
            return

        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)

        # ── File Handler: JSON structured log với rotation ──────────────
        log_file = os.path.join(
            self.log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log"
        )
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)  # Ghi tất cả level vào file
        file_handler.setFormatter(JsonFormatter())
        self.logger.addHandler(file_handler)

        # ── Console Handler: format dễ đọc với màu sắc ─────────────────
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)  # Console chỉ hiển thị INFO+
        console_handler.setFormatter(ConsoleFormatter())
        self.logger.addHandler(console_handler)

        # Log khởi tạo thành công
        self.logger.info(
            f"Logger initialized – log file: {log_file}"
        )

    # ── Structured event logging ────────────────────────────────────────

    def log_event(self, event_type: str, data: Dict[str, Any]):
        """
        Ghi một event có cấu trúc (structured log).
        Event sẽ được ghi dưới dạng JSON với event_type và data.
        """
        extra = {"event_type": event_type, "event_data": data}
        self.logger.info(
            f"[EVENT:{event_type}] {json.dumps(data, ensure_ascii=False, default=str)}",
            extra=extra,
        )

    # ── Convenience methods cho từng log level ──────────────────────────

    def debug(self, msg: str, **kwargs):
        """Ghi log DEBUG – thông tin chi tiết cho phát triển/debug."""
        self.logger.debug(msg, **kwargs)

    def info(self, msg: str, **kwargs):
        """Ghi log INFO – thông tin hoạt động bình thường."""
        self.logger.info(msg, **kwargs)

    def warning(self, msg: str, **kwargs):
        """Ghi log WARNING – cảnh báo, không phải lỗi."""
        self.logger.warning(msg, **kwargs)

    def error(self, msg: str, exc_info: bool = True, **kwargs):
        """Ghi log ERROR – lỗi xảy ra, kèm traceback nếu có."""
        self.logger.error(msg, exc_info=exc_info, **kwargs)

    def critical(self, msg: str, exc_info: bool = True, **kwargs):
        """Ghi log CRITICAL – lỗi nghiêm trọng."""
        self.logger.critical(msg, exc_info=exc_info, **kwargs)

    # ── Agent-specific logging helpers ──────────────────────────────────

    def log_agent_step(
        self,
        step_index: int,
        thought: str,
        action_tool: str = "",
        action_input: Optional[Dict] = None,
        observation: str = "",
        duration_ms: float = 0.0,
    ):
        """Ghi log một bước trong vòng lặp ReAct Agent."""
        self.log_event("AGENT_STEP", {
            "step_index": step_index,
            "thought": thought,
            "action_tool": action_tool,
            "action_input": action_input or {},
            "observation": observation[:500] if observation else "",
            "duration_ms": round(duration_ms, 2),
        })

    def log_agent_complete(
        self,
        user_query: str,
        total_steps: int,
        total_duration_ms: float,
        input_tokens: int = 0,
        output_tokens: int = 0,
        model: str = "",
    ):
        """Ghi log khi Agent hoàn thành xử lý."""
        self.log_event("AGENT_COMPLETE", {
            "user_query": user_query,
            "total_steps": total_steps,
            "total_duration_ms": round(total_duration_ms, 2),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "model": model,
        })

    def log_tool_call(self, tool_name: str, inputs: Dict[str, Any], result: str, duration_ms: float = 0.0):
        """Ghi log khi gọi tool."""
        self.log_event("TOOL_CALL", {
            "tool": tool_name,
            "inputs": inputs,
            "result_preview": result[:300] if result else "",
            "duration_ms": round(duration_ms, 2),
        })

    def log_error_event(self, error_type: str, message: str, details: Optional[Dict] = None):
        """Ghi log lỗi dạng structured event."""
        self.log_event("ERROR", {
            "error_type": error_type,
            "message": message,
            "details": details or {},
        })


# ── Global logger instance ──────────────────────────────────────────────
logger = IndustryLogger()
