"""
app.py - Streamlit UI chia 2 cột:
  Trái  → Chatbot Baseline (OpenAI, không có tool)
  Phải  → PC Price Agent   (OpenAI + tool calling + tracking)

Chạy:
    pip install streamlit openai
    streamlit run app.py
"""

from __future__ import annotations

import html
import json
import time

import streamlit as st
from openai import OpenAI

from agent import PCPriceAgent


st.set_page_config(
    page_title="Chatbot vs Agent – PC Price",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
.main-header {
    text-align: center;
    padding: 1.2rem 0 0.5rem;
    border-bottom: 1px solid #e2e8f0;
    margin-bottom: 1.2rem;
}
.main-header h1 { font-size: 1.6rem; font-weight: 600; margin: 0; }
.main-header p  { font-size: 0.9rem; color: #64748b; margin-top: 0.25rem; }
.col-label {
    display: flex; align-items: center; gap: 8px;
    font-size: 0.8rem; font-weight: 700; text-transform: uppercase;
    border-radius: 8px; padding: 8px 12px; margin-bottom: 12px;
}
.col-label-baseline { background: #eef2ff; color: #4338ca; border: 1px solid #c7d2fe; }
.col-label-agent    { background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }
.msg-user {
    background: #4f46e5; color: white;
    padding: 10px 14px; border-radius: 14px 14px 4px 14px;
    margin: 6px 0 6px 20%;
}
.msg-bot {
    background: #f8fafc; color: #0f172a;
    padding: 10px 14px; border-radius: 14px 14px 14px 4px;
    margin: 6px 20% 6px 0; border: 1px solid #e2e8f0;
}
.step-card {
    border-radius: 10px; padding: 10px 14px; margin: 6px 0;
    border-left: 4px solid;
}
.step-thought { background: #fffbeb; border-color: #f59e0b; }
.step-action  { background: #f0fdf4; border-color: #22c55e; }
.step-obs     { background: #eff6ff; border-color: #3b82f6; }
.step-answer  { background: #fdf4ff; border-color: #a855f7; }
.step-label {
    font-size: 0.74rem; font-weight: 700; text-transform: uppercase;
    opacity: .75; margin-bottom: 4px;
}
.product-card {
    background: white; border: 1px solid #e2e8f0; border-radius: 10px;
    padding: 10px 14px; margin: 6px 0;
}
.badge-stock { display:inline-block; padding:2px 8px; border-radius:999px; font-size:0.72rem; font-weight:700; }
.badge-yes { background:#dcfce7; color:#15803d; }
.badge-no  { background:#fee2e2; color:#dc2626; }
.stat-bar {
    display: flex; gap: 12px; flex-wrap: wrap; margin-top: 8px;
    padding: 8px 12px; background: #f8fafc; border-radius: 8px;
    font-size: 0.8rem;
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="main-header">
  <h1>🖥️ Chatbot Baseline vs 🤖 PC Price Agent</h1>
  <p>So sánh trực tiếp chatbot thường và agent có tool calling + tracking</p>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("⚙️ Cấu hình")
    api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    model = st.selectbox("Model", ["gpt-4o", "gpt-4o-mini"])
    st.markdown("---")
    if st.button("🗑️ Xoá lịch sử chat"):
        st.session_state.baseline_history = []
        st.session_state.agent_history = []
        st.rerun()


if "baseline_history" not in st.session_state:
    st.session_state.baseline_history = []
if "agent_history" not in st.session_state:
    st.session_state.agent_history = []


BASELINE_SYSTEM = """Bạn là trợ lý tư vấn mua PC và linh kiện máy tính tại Việt Nam.
Trả lời bằng tiếng Việt, ngắn gọn và hữu ích.
Lưu ý: bạn KHÔNG có công cụ tìm giá thực tế, hãy dùng kiến thức sẵn có."""


def get_client(key: str) -> OpenAI:
    return OpenAI(api_key=key)


def render_step(label: str, css_class: str, content: str) -> None:
    st.markdown(
        f"""
<div class="step-card {css_class}">
  <div class="step-label">{label}</div>
  <div>{content}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_product_cards(obs_json: str) -> None:
    try:
        data = json.loads(obs_json)
        if "results" in data:
            for r in data.get("results", []):
                stock_badge = (
                    '<span class="badge-stock badge-yes">Còn hàng</span>'
                    if r.get("in_stock")
                    else '<span class="badge-stock badge-no">Hết hàng</span>'
                )
                st.markdown(
                    f"""
<div class="product-card">
  <div><b>{html.escape(r['name'])}</b></div>
  <div>💰 {html.escape(r['price'])} &nbsp; {stock_badge}</div>
  <div>🏪 {html.escape(r['shop'])}</div>
  <div>🔗 <a href="{html.escape(r['url'])}" target="_blank">{html.escape(r['url'])}</a></div>
</div>
""",
                    unsafe_allow_html=True,
                )
        elif "checks" in data:
            render_step("🔭 Observation", "step-obs", html.escape(data.get("summary", "")))
            for item in data.get("checks", []):
                icon = "✅" if item.get("compatible") else "❌"
                render_step(
                    "🔧 Compatibility",
                    "step-obs",
                    f"{icon} <b>{html.escape(item['component_pair'])}</b>: {html.escape(item['details'])}",
                )
            if data.get("issues"):
                issues = "<br>".join(f"• {html.escape(issue)}" for issue in data["issues"])
                render_step("⚠️ Issues", "step-obs", issues)
        else:
            render_step("🔭 Observation", "step-obs", f"<pre>{html.escape(json.dumps(data, ensure_ascii=False, indent=2))}</pre>")
    except Exception:
        render_step("🔭 Observation", "step-obs", f"<pre>{html.escape(obs_json[:800])}</pre>")


def call_baseline(client: OpenAI, model: str, history: list[dict], query: str):
    messages = [{"role": "system", "content": BASELINE_SYSTEM}, *history, {"role": "user", "content": query}]
    t0 = time.perf_counter()
    resp = client.chat.completions.create(model=model, messages=messages, max_tokens=800)
    elapsed = (time.perf_counter() - t0) * 1000
    answer = resp.choices[0].message.content or ""
    return answer, resp.usage.prompt_tokens, resp.usage.completion_tokens, elapsed


def run_agent(api_key: str, model: str, query: str):
    agent = PCPriceAgent(api_key=api_key, model=model)
    trace = agent.run(query)
    steps = []
    for step in trace.steps:
        if step.thought:
            steps.append({"type": "thought", "content": step.thought, "ms": step.duration_ms})
        if step.action_tool:
            steps.append({"type": "action", "tool": step.action_tool, "input": step.action_input})
        if step.observation:
            steps.append({"type": "observation", "content": step.observation})
    if trace.final_answer:
        steps.append({"type": "answer", "content": trace.final_answer})
    return steps, trace.final_answer, trace.input_tokens, trace.output_tokens, trace.total_duration_ms


col_left, col_right = st.columns(2, gap="medium")

with col_left:
    st.markdown(
        '<div class="col-label col-label-baseline">💬 Chatbot Baseline <span style="font-weight:400;text-transform:none">— không có tool</span></div>',
        unsafe_allow_html=True,
    )

    for msg in st.session_state.baseline_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="msg-user">{html.escape(msg["content"])}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="msg-bot">{html.escape(msg["content"])}</div>', unsafe_allow_html=True)
            if "stats" in msg:
                s = msg["stats"]
                st.markdown(
                    f'<div class="stat-bar"><span>⏱ <b>{s["ms"]:.0f} ms</b></span><span>📥 <b>{s["in_tok"]}</b></span><span>📤 <b>{s["out_tok"]}</b></span></div>',
                    unsafe_allow_html=True,
                )

    with st.form("form_baseline", clear_on_submit=True):
        q_b = st.text_input("Nhập câu hỏi baseline", placeholder="VD: PC gaming RTX 4070 giá bao nhiêu?", label_visibility="collapsed")
        send_b = st.form_submit_button("Gửi ➤", use_container_width=True)

    if send_b and q_b.strip():
        if not api_key:
            st.error("Vui lòng nhập API Key trong sidebar.")
        else:
            st.session_state.baseline_history.append({"role": "user", "content": q_b})
            with st.spinner("Đang trả lời..."):
                answer, in_tok, out_tok, ms = call_baseline(get_client(api_key), model, st.session_state.baseline_history[:-1], q_b)
            st.session_state.baseline_history.append(
                {
                    "role": "assistant",
                    "content": answer,
                    "stats": {"ms": ms, "in_tok": in_tok, "out_tok": out_tok},
                }
            )
            st.rerun()

with col_right:
    st.markdown(
        '<div class="col-label col-label-agent">🤖 PC Price Agent <span style="font-weight:400;text-transform:none">— Thought → Action → Observation</span></div>',
        unsafe_allow_html=True,
    )

    for msg in st.session_state.agent_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="msg-user">{html.escape(msg["content"])}</div>', unsafe_allow_html=True)
        else:
            for step in msg.get("steps", []):
                if step["type"] == "thought":
                    render_step("💭 Thought", "step-thought", html.escape(step["content"]))
                elif step["type"] == "action":
                    render_step(
                        "⚡ Action",
                        "step-action",
                        f"Tool: <b>{html.escape(step['tool'])}</b><br><pre>{html.escape(json.dumps(step['input'], ensure_ascii=False, indent=2))}</pre>",
                    )
                elif step["type"] == "observation":
                    render_product_cards(step["content"])
                elif step["type"] == "answer":
                    render_step("✅ Final Answer", "step-answer", html.escape(step["content"]))
            if "stats" in msg:
                s = msg["stats"]
                st.markdown(
                    f'<div class="stat-bar"><span>⏱ <b>{s["ms"]:.0f} ms</b></span><span>🔄 <b>{s["steps"]}</b> actions</span><span>📥 <b>{s["in_tok"]}</b></span><span>📤 <b>{s["out_tok"]}</b></span></div>',
                    unsafe_allow_html=True,
                )

    with st.form("form_agent", clear_on_submit=True):
        q_a = st.text_input(
            "Nhập câu hỏi agent",
            placeholder="VD: Sắp xếp card RTX theo giá giảm dần",
            label_visibility="collapsed",
        )
        send_a = st.form_submit_button("Gửi ➤", use_container_width=True)

    if send_a and q_a.strip():
        if not api_key:
            st.error("Vui lòng nhập API Key trong sidebar.")
        else:
            st.session_state.agent_history.append({"role": "user", "content": q_a})
            with st.spinner("Agent đang xử lý..."):
                steps, final, in_tok, out_tok, total_ms = run_agent(api_key, model, q_a)
            st.session_state.agent_history.append(
                {
                    "role": "assistant",
                    "content": final,
                    "steps": steps,
                    "stats": {
                        "ms": total_ms,
                        "steps": len([s for s in steps if s["type"] == "action"]),
                        "in_tok": in_tok,
                        "out_tok": out_tok,
                    },
                }
            )
            st.rerun()
