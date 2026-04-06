"""
app.py - Streamlit UI chia 2 cột:
  Trái  → Chatbot Baseline (OpenAI gpt-4o, không có tool)
  Phải  → PC Price Agent   (OpenAI gpt-4o + tool calling + tracking)

Chạy:
    pip install streamlit openai
    streamlit run app.py
"""

import json
import time
import streamlit as st
from openai import OpenAI

from tools import TOOLS_OPENAI, execute_tool

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Chatbot vs Agent – PC Price",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=DM+Sans:wght@400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

/* Header */
.main-header {
    text-align: center;
    padding: 1.2rem 0 0.5rem;
    border-bottom: 1px solid #e2e8f0;
    margin-bottom: 1.2rem;
}
.main-header h1 { font-size: 1.6rem; font-weight: 600; margin: 0; color: #1a202c; }
.main-header p  { font-size: 0.85rem; color: #718096; margin: 0.3rem 0 0; }

/* Column labels */
.col-label {
    display: flex; align-items: center; gap: 8px;
    font-size: 0.78rem; font-weight: 600; letter-spacing: .06em;
    text-transform: uppercase; padding: 6px 12px;
    border-radius: 6px; margin-bottom: 12px;
}
.col-label-baseline { background: #eef2ff; color: #4f46e5; border: 1px solid #c7d2fe; }
.col-label-agent    { background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; }

/* Chat messages */
.msg-user {
    background: #4f46e5; color: #fff;
    padding: 10px 14px; border-radius: 14px 14px 4px 14px;
    margin: 6px 0 6px 20%; font-size: 0.9rem; line-height: 1.5;
}
.msg-bot {
    background: #f8fafc; color: #1e293b;
    padding: 10px 14px; border-radius: 14px 14px 14px 4px;
    margin: 6px 20% 6px 0; font-size: 0.9rem; line-height: 1.5;
    border: 1px solid #e2e8f0;
}

/* Agent step cards */
.step-card {
    border-radius: 10px; padding: 10px 14px;
    margin: 6px 0; font-size: 0.85rem; line-height: 1.6;
    border-left: 3px solid;
}
.step-thought  { background: #fffbeb; border-color: #f59e0b; color: #78350f; }
.step-action   { background: #f0fdf4; border-color: #22c55e; color: #14532d; }
.step-obs      { background: #eff6ff; border-color: #3b82f6; color: #1e3a8a; }
.step-answer   { background: #fdf4ff; border-color: #a855f7; color: #581c87; }

.step-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: .08em;
    opacity: .7; margin-bottom: 4px;
}

/* Product card */
.product-card {
    background: #fff; border: 1px solid #e2e8f0;
    border-radius: 10px; padding: 10px 14px; margin: 6px 0;
    font-size: 0.85rem;
}
.product-card .pname  { font-weight: 600; color: #1e293b; margin-bottom: 4px; }
.product-card .pprice { color: #16a34a; font-weight: 600; font-size: 0.95rem; }
.product-card .pshop  { color: #64748b; font-size: 0.8rem; }
.product-card .plink  { font-size: 0.8rem; }
.badge-stock   { display:inline-block; padding:1px 8px; border-radius:99px; font-size:0.72rem; font-weight:600; }
.badge-yes     { background:#dcfce7; color:#15803d; }
.badge-no      { background:#fee2e2; color:#dc2626; }

/* Token stats */
.stat-bar {
    display: flex; gap: 12px; flex-wrap: wrap;
    margin-top: 8px; padding: 8px 12px;
    background: #f8fafc; border-radius: 8px;
    font-size: 0.78rem; color: #64748b;
}
.stat-bar span b { color: #1e293b; }

/* Spinner override */
div[data-testid="stSpinner"] { margin: 8px 0; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1>🖥️ Chatbot Baseline &nbsp;vs&nbsp; 🤖 PC Price Agent</h1>
  <p>So sánh trực tiếp: ChatGPT thuần &nbsp;|&nbsp; Agent với Tool Calling + Tracking</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# SIDEBAR – API KEY
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Cấu hình")
    api_key = st.text_input("OpenAI API Key", type="password",
                            placeholder="sk-proj-...")
    model = st.selectbox("Model", ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"])
    st.markdown("---")
    if st.button("🗑️ Xoá lịch sử chat"):
        st.session_state.baseline_history = []
        st.session_state.agent_history    = []
        st.rerun()
    st.caption("Mỗi cột giữ lịch sử chat riêng.")

# ─────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────
if "baseline_history" not in st.session_state:
    st.session_state.baseline_history = []   # list[dict] {role, content}
if "agent_history" not in st.session_state:
    st.session_state.agent_history    = []   # list[dict] {role, content, steps?}

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
BASELINE_SYSTEM = """Bạn là trợ lý tư vấn mua PC và linh kiện máy tính tại Việt Nam.
Trả lời bằng tiếng Việt, ngắn gọn và hữu ích.
Lưu ý: bạn KHÔNG có công cụ tìm giá thực tế, hãy dùng kiến thức sẵn có."""

AGENT_SYSTEM = """Bạn là AI Agent chuyên tìm kiếm giá PC, laptop và linh kiện máy tính tại Việt Nam.
- Luôn dùng tool `search_pc_price` để tìm kiếm trước khi trả lời.
- Trình bày kết quả rõ ràng: tên sản phẩm, giá, shop, link.
- KHÔNG bịa đặt giá hay link sản phẩm."""


def get_client(key: str) -> OpenAI:
    return OpenAI(api_key=key)


def render_product_cards(obs_json: str):
    """Parse JSON observation và render product cards."""
    try:
        data = json.loads(obs_json)
        results = data.get("results", [])
        for r in results:
            stock_badge = (
                '<span class="badge-stock badge-yes">Còn hàng</span>'
                if r.get("in_stock") else
                '<span class="badge-stock badge-no">Hết hàng</span>'
            )
            st.markdown(f"""
            <div class="product-card">
              <div class="pname">{r['name']}</div>
              <div class="pprice">💰 {r['price']} &nbsp;{stock_badge}</div>
              <div class="pshop">🏪 {r['shop']}</div>
              <div class="plink">🔗 <a href="{r['url']}" target="_blank">{r['url']}</a></div>
            </div>
            """, unsafe_allow_html=True)
    except Exception:
        st.code(obs_json[:600])


def render_step(label: str, css_class: str, content: str):
    st.markdown(f"""
    <div class="step-card {css_class}">
      <div class="step-label">{label}</div>
      {content}
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# CHATBOT BASELINE LOGIC
# ─────────────────────────────────────────────────────────────
def call_baseline(client: OpenAI, model: str, history: list, query: str):
    messages = [{"role": "system", "content": BASELINE_SYSTEM}]
    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": query})

    t0 = time.perf_counter()
    resp = client.chat.completions.create(model=model, messages=messages, max_tokens=800)
    elapsed = (time.perf_counter() - t0) * 1000

    answer = resp.choices[0].message.content
    return answer, resp.usage.prompt_tokens, resp.usage.completion_tokens, elapsed


# ─────────────────────────────────────────────────────────────
# AGENT LOGIC
# ─────────────────────────────────────────────────────────────
def call_agent(client: OpenAI, model: str, history: list, query: str):
    """ReAct loop: Thought → Action → Observation → Final Answer."""
    messages = [{"role": "system", "content": AGENT_SYSTEM}]
    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": query})

    steps = []
    total_in = total_out = 0
    t_start = time.perf_counter()
    MAX_ITER = 5

    for i in range(MAX_ITER):
        t0 = time.perf_counter()
        resp = client.chat.completions.create(
            model=model, tools=TOOLS_OPENAI,
            tool_choice="auto", messages=messages, max_tokens=1000,
        )
        msg           = resp.choices[0].message
        finish_reason = resp.choices[0].finish_reason
        total_in  += resp.usage.prompt_tokens
        total_out += resp.usage.completion_tokens
        elapsed = (time.perf_counter() - t0) * 1000

        thought = msg.content or ""

        if finish_reason == "stop":
            steps.append({"type": "answer", "content": thought, "ms": elapsed})
            final = thought
            break

        if not msg.tool_calls:
            steps.append({"type": "answer", "content": thought or "[Không có hành động]", "ms": elapsed})
            final = thought
            break

        steps.append({"type": "thought", "content": thought, "ms": elapsed})
        messages.append(msg)

        for tc in msg.tool_calls:
            tool_name  = tc.function.name
            tool_input = json.loads(tc.function.arguments)
            steps.append({"type": "action", "tool": tool_name, "input": tool_input})

            obs = execute_tool(tool_name, tool_input)
            steps.append({"type": "observation", "content": obs})
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": obs})
    else:
        final = "[Đã đạt giới hạn vòng lặp]"

    total_ms = (time.perf_counter() - t_start) * 1000
    return steps, final, total_in, total_out, total_ms


# ─────────────────────────────────────────────────────────────
# TWO COLUMNS LAYOUT
# ─────────────────────────────────────────────────────────────
col_left, col_right = st.columns(2, gap="medium")

# ════════════════════════════════
# LEFT – BASELINE CHATBOT
# ════════════════════════════════
with col_left:
    st.markdown('<div class="col-label col-label-baseline">💬 Chatbot Baseline <span style="font-weight:400;text-transform:none;margin-left:4px">— không có tool</span></div>', unsafe_allow_html=True)

    # Render history
    chat_box_b = st.container()
    with chat_box_b:
        for msg in st.session_state.baseline_history:
            if msg["role"] == "user":
                st.markdown(f'<div class="msg-user">{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="msg-bot">{msg["content"]}</div>', unsafe_allow_html=True)
                if "stats" in msg:
                    s = msg["stats"]
                    st.markdown(f'<div class="stat-bar"><span>⏱ <b>{s["ms"]:.0f}ms</b></span><span>📥 <b>{s["in_tok"]}</b> tokens in</span><span>📤 <b>{s["out_tok"]}</b> tokens out</span></div>', unsafe_allow_html=True)

    # Input
    with st.form("form_baseline", clear_on_submit=True):
        q_b = st.text_input("Nhập câu hỏi...", placeholder="VD: PC gaming RTX 4070 giá bao nhiêu?", label_visibility="collapsed")
        send_b = st.form_submit_button("Gửi ➤", use_container_width=True)

    if send_b and q_b.strip():
        if not api_key:
            st.error("Vui lòng nhập API Key trong sidebar.")
        else:
            st.session_state.baseline_history.append({"role": "user", "content": q_b})
            with st.spinner("Đang trả lời..."):
                answer, in_tok, out_tok, ms = call_baseline(
                    get_client(api_key), model,
                    st.session_state.baseline_history[:-1], q_b
                )
            st.session_state.baseline_history.append({
                "role": "assistant", "content": answer,
                "stats": {"ms": ms, "in_tok": in_tok, "out_tok": out_tok}
            })
            st.rerun()

# ════════════════════════════════
# RIGHT – AGENT
# ════════════════════════════════
with col_right:
    st.markdown('<div class="col-label col-label-agent">🤖 PC Price Agent <span style="font-weight:400;text-transform:none;margin-left:4px">— Thought → Action → Observation</span></div>', unsafe_allow_html=True)

    # Render history
    chat_box_a = st.container()
    with chat_box_a:
        for msg in st.session_state.agent_history:
            if msg["role"] == "user":
                st.markdown(f'<div class="msg-user">{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                # Render steps
                for step in msg.get("steps", []):
                    if step["type"] == "thought" and step["content"]:
                        render_step("💭 Thought", "step-thought", step["content"])
                    elif step["type"] == "action":
                        inp = step.get("input", {})
                        render_step("⚡ Action",  "step-action",
                                    f"Tool: <b>{step['tool']}</b> &nbsp;|&nbsp; query: <i>{inp.get('query','')}</i>")
                    elif step["type"] == "observation":
                        st.markdown('<div class="step-label" style="color:#1e3a8a;padding:4px 0 2px">🔭 Observation — kết quả tìm kiếm</div>', unsafe_allow_html=True)
                        render_product_cards(step["content"])
                    elif step["type"] == "answer":
                        render_step("✅ Final Answer", "step-answer", step["content"])

                if "stats" in msg:
                    s = msg["stats"]
                    st.markdown(f'<div class="stat-bar"><span>⏱ <b>{s["ms"]:.0f}ms</b></span><span>🔄 <b>{s["steps"]}</b> bước</span><span>📥 <b>{s["in_tok"]}</b> in</span><span>📤 <b>{s["out_tok"]}</b> out</span></div>', unsafe_allow_html=True)

    # Input
    with st.form("form_agent", clear_on_submit=True):
        q_a = st.text_input("Nhập câu hỏi...", placeholder="VD: Tìm laptop Dell XPS giá tốt nhất", label_visibility="collapsed")
        send_a = st.form_submit_button("Gửi ➤", use_container_width=True)

    if send_a and q_a.strip():
        if not api_key:
            st.error("Vui lòng nhập API Key trong sidebar.")
        else:
            st.session_state.agent_history.append({"role": "user", "content": q_a})
            with st.spinner("Agent đang xử lý..."):
                steps, final, in_tok, out_tok, total_ms = call_agent(
                    get_client(api_key), model,
                    [{"role": h["role"], "content": h["content"]}
                     for h in st.session_state.agent_history[:-1]],
                    q_a
                )
            st.session_state.agent_history.append({
                "role": "assistant",
                "content": final,
                "steps": steps,
                "stats": {
                    "ms": total_ms,
                    "steps": len([s for s in steps if s["type"] == "action"]),
                    "in_tok": in_tok,
                    "out_tok": out_tok,
                }
            })
            st.rerun()