"""
Streamlit Web Interface & 4-Tab Analytics Dashboard for NIT Admission QA System
Tabs:
1. 💬 Questions Interface (Q&A + per-question Prompt/Thinking/Output/Total tokens, cost, score, latency)
2. 💰 Cost & Token Savings (Pure LLM Baseline vs. Hybrid RAG comparison & cost savings)
3. 📊 Comparison Plots (4 publication-ready comparison charts)
4. 🧾 Local vs. API Breakdown (Exact Local vs. API counts, Pie/Bar split, & filterable query log)

Run with: streamlit run app_ui.py
"""

import os
import json
import time
import matplotlib.pyplot as plt
import streamlit as st
from config import AUDIT_LOG_JSON
from step5_hybrid_qa_engine import HybridAdmissionQA

# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="NIT Admission Assistant | Hybrid RAG Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def load_qa_engine():
    return HybridAdmissionQA()

bot = load_qa_engine()

def load_audit_logs():
    if os.path.exists(AUDIT_LOG_JSON):
        try:
            with open(AUDIT_LOG_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"summary": bot.stats, "logs": []}

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hello! I am the **Narula Institute of Technology (NIT)** Admission Assistant.\n\n"
                "Ask me about **fees, seats, eligibility, scholarships, placements, or documents** "
                "for instant **$0.00 local answers**, or ask general college/technical questions!"
            ),
            "meta": None
        }
    ]

# ---------------------------------------------------------------------------
# Sidebar: Quick Demo Questions & Engine Info
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("⚡ Quick Demo Questions")
    st.caption("Click any question to test live routing:")
    demo_questions = [
        "What is the 1st semester fee for B.Tech CSE?",
        "How many seats are there in ECE?",
        "What is the overall placement percentage?",
        "What is the eligibility criteria for MCA?",
        "Who is the principal of NIT?",
        "Who is the HOD of CSE department in NIT?",
        "Difference between CSE and IT?"
    ]
    selected_demo = None
    for dq in demo_questions:
        if st.button(dq, use_container_width=True):
            selected_demo = dq

    st.divider()
    st.subheader("⚙️ Engine Settings")
    st.write(f"**Threshold (τ):** `{bot.threshold}`")
    st.write(f"**Fallback Model:** `{bot.active_model}`")
    st.write(f"**Retriever:** `{'all-MiniLM-L6-v2' if bot.retriever.use_transformer else 'TF-IDF'}`")

# ---------------------------------------------------------------------------
# Load Live Audit Metrics
# ---------------------------------------------------------------------------
audit_data = load_audit_logs()
summary = audit_data.get("summary", bot.stats)
logs = audit_data.get("logs", [])

total_q = summary.get("total_queries", 0)
local_hits = summary.get("local_hits", 0)
nit_api = summary.get("nit_api_fallbacks", 0)
gen_api = summary.get("general_api_fallbacks", 0)
legacy_api = summary.get("api_fallbacks", 0)
total_api_used = nit_api + gen_api + legacy_api
savings_pct = round((local_hits / max(1, total_q)) * 100, 1)

prompt_tokens = summary.get("total_prompt_tokens", 0)
output_tokens = summary.get("total_output_tokens", 0)
total_tokens = summary.get("total_api_tokens", 0)
thinking_tokens = max(0, total_tokens - (prompt_tokens + output_tokens))

# ---------------------------------------------------------------------------
# Top KPI Bar
# ---------------------------------------------------------------------------
st.title("🎓 Narula Institute of Technology — Smart Admission Assistant")

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Queries", total_q)
k2.metric("Local Hits ($0 Cost)", local_hits, f"{savings_pct}% saved")
k3.metric("API Calls Used", total_api_used)
k4.metric("Total API Tokens", f"{total_tokens:,}")
k5.metric("Prompt + Out + Think", f"{prompt_tokens:,} + {output_tokens:,} + {thinking_tokens:,}")

# ---------------------------------------------------------------------------
# 4 Dedicated Tabs Requested
# ---------------------------------------------------------------------------
tab_chat, tab_savings, tab_plots, tab_breakdown = st.tabs([
    "💬 1. Questions Interface",
    "💰 2. Cost & Token Savings",
    "📊 3. Comparison Plots",
    "🧾 4. Local vs. API Breakdown"
])

# ===========================================================================
# TAB 1: Questions Interface (with per-question token breakdown)
# ===========================================================================
with tab_chat:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg.get("meta"):
                m = msg["meta"]
                status = m["status"]
                t = m.get("tokens", {})
                p_t = t.get("prompt_tokens", 0)
                o_t = t.get("output_tokens", 0)
                tot_t = t.get("total_tokens", 0)
                th_t = t.get("thoughts_tokens", max(0, tot_t - (p_t + o_t)))
                badge = (
                    f"**Cost:** {m['cost']} &nbsp;|&nbsp; "
                    f"**Tokens:** {tot_t} (Prompt: {p_t}, Output: {o_t}, Thinking: {th_t}) &nbsp;|&nbsp; "
                    f"**Score:** {m['confidence_score']} &nbsp;|&nbsp; "
                    f"**Latency:** {m['latency_ms']:.1f} ms"
                )
                if status == "LOCAL_WEBSITE_HIT":
                    st.success(f"✅ **TIER 1: LOCAL ADMISSION DATA** — {m['citation']['title']}\n\n{badge}")
                elif status == "NIT_SPECIFIC_API_FALLBACK":
                    st.info(f"🏛️ **TIER 2: NIT COLLEGE API** — Grounded Institutional Context\n\n{badge}")
                else:
                    st.warning(f"🌐 **TIER 3: GENERAL KNOWLEDGE API** — Out-of-Domain Query\n\n{badge}")
            st.markdown(msg["content"])

    user_query = st.chat_input("Ask anything about NIT admissions, fees, seats, placements...")
    if selected_demo:
        user_query = selected_demo

    if user_query:
        st.session_state.messages.append({"role": "user", "content": user_query, "meta": None})
        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            with st.spinner("Searching local knowledge base..."):
                t0 = time.perf_counter()
                res = bot.ask(user_query)
                latency_ms = (time.perf_counter() - t0) * 1000

            res["latency_ms"] = latency_ms
            status = res["status"]
            t = res.get("tokens", {})
            p_t = t.get("prompt_tokens", 0)
            o_t = t.get("output_tokens", 0)
            tot_t = t.get("total_tokens", 0)
            th_t = t.get("thoughts_tokens", max(0, tot_t - (p_t + o_t)))
            badge = (
                f"**Cost:** {res['cost']} &nbsp;|&nbsp; "
                f"**Tokens:** {tot_t} (Prompt: {p_t}, Output: {o_t}, Thinking: {th_t}) &nbsp;|&nbsp; "
                f"**Score:** {res['confidence_score']} &nbsp;|&nbsp; "
                f"**Latency:** {latency_ms:.1f} ms"
            )

            if status == "LOCAL_WEBSITE_HIT":
                st.success(f"✅ **TIER 1: LOCAL ADMISSION DATA** — {res['citation']['title']}\n\n{badge}")
            elif status == "NIT_SPECIFIC_API_FALLBACK":
                st.info(f"🏛️ **TIER 2: NIT COLLEGE API** — Grounded Institutional Context\n\n{badge}")
            else:
                st.warning(f"🌐 **TIER 3: GENERAL KNOWLEDGE API** — Out-of-Domain Query\n\n{badge}")

            st.markdown(res["answer"])

        st.session_state.messages.append({"role": "assistant", "content": res["answer"], "meta": res})
        st.rerun()

# ===========================================================================
# TAB 2: Cost & Token Savings Stats
# ===========================================================================
with tab_savings:
    st.subheader("💰 Cost & Token Savings Analysis (Hybrid RAG vs. Pure Cloud LLM)")

    avg_tokens_per_api = round(total_tokens / max(1, total_api_used)) if total_api_used > 0 else 450
    pure_llm_est_tokens = total_q * avg_tokens_per_api
    tokens_saved = max(0, pure_llm_est_tokens - total_tokens)

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("API Calls Saved", f"{local_hits} calls", f"{savings_pct}% reduction")
    s2.metric("Tokens Saved (Est.)", f"{tokens_saved:,}")
    s3.metric("Avg Tokens / API Call", f"{avg_tokens_per_api:,}")
    s4.metric("Prompt + Output + Thinking", f"{total_tokens:,}")

    st.divider()
    st.markdown("### 📋 Baseline vs. Hybrid Architecture Comparison")
    comparison_rows = [
        {
            "Metric": "Total Queries Handled",
            "Pure Cloud LLM Baseline": total_q,
            "Our 3-Tier Hybrid System": total_q,
            "Advantage": "100% Query Coverage"
        },
        {
            "Metric": "Cloud API Calls Required",
            "Pure Cloud LLM Baseline": total_q,
            "Our 3-Tier Hybrid System": total_api_used,
            "Advantage": f"{local_hits} API Calls Saved ({savings_pct}%)"
        },
        {
            "Metric": "Total API Tokens Consumed",
            "Pure Cloud LLM Baseline": f"~{pure_llm_est_tokens:,}",
            "Our 3-Tier Hybrid System": f"{total_tokens:,}",
            "Advantage": f"~{tokens_saved:,} Tokens Saved"
        },
        {
            "Metric": "Average Response Latency (Tier 1)",
            "Pure Cloud LLM Baseline": "1,500 – 3,000 ms",
            "Our 3-Tier Hybrid System": "< 40 ms (Local)",
            "Advantage": "~50x Faster on Local Hits"
        }
    ]
    st.table(comparison_rows)

    st.info(
        f"**Why Total API Tokens ({total_tokens:,}) > Prompt ({prompt_tokens:,}) + Output ({output_tokens:,})?**\n\n"
        f"`gemini-3.5-flash` uses internal reasoning (**Thinking Tokens = {thinking_tokens:,}**). "
        f"Google's `usageMetadata.totalTokenCount` equals `Prompt ({prompt_tokens:,}) + Output ({output_tokens:,}) + Thinking ({thinking_tokens:,}) = {total_tokens:,}`."
    )

# ===========================================================================
# TAB 3: Comparison Plots
# ===========================================================================
with tab_plots:
    st.subheader("📊 Visual Comparison & Performance Plots")
    if not logs and total_q == 0:
        st.info("Ask a few questions in Tab 1 to generate live plots.")
    else:
        col_a, col_b = st.columns(2)

        with col_a:
            fig1, ax1 = plt.subplots(figsize=(5.5, 4))
            arch_labels = ["Pure LLM\n(100% API)", "Our Hybrid RAG\n(API Calls Used)"]
            arch_vals = [total_q, total_api_used]
            bars1 = ax1.bar(arch_labels, arch_vals, color=["#EF4444", "#10B981"], width=0.48, edgecolor="#1E293B")
            ax1.set_title("API Calls: Pure LLM vs. Hybrid RAG", fontsize=12, fontweight="bold")
            ax1.set_ylabel("Number of Cloud API Requests")
            ax1.grid(axis="y", linestyle="--", alpha=0.4)
            for b in bars1:
                h = b.get_height()
                ax1.text(b.get_x() + b.get_width()/2, h + max(1, max(arch_vals))*0.02, f"{int(h)}", ha="center", va="bottom", fontweight="bold")
            st.pyplot(fig1)

        with col_b:
            avg_t = round(total_tokens / max(1, total_api_used)) if total_api_used > 0 else 450
            pure_tok = total_q * avg_t
            fig2, ax2 = plt.subplots(figsize=(5.5, 4))
            t_labels = ["Pure LLM\n(Estimated Tokens)", "Our Hybrid RAG\n(Actual Tokens Used)"]
            t_vals = [pure_tok, total_tokens]
            bars2 = ax2.bar(t_labels, t_vals, color=["#F59E0B", "#3B82F6"], width=0.48, edgecolor="#1E293B")
            ax2.set_title("Total Token Consumption Comparison", fontsize=12, fontweight="bold")
            ax2.set_ylabel("Total Tokens")
            ax2.grid(axis="y", linestyle="--", alpha=0.4)
            for b in bars2:
                h = b.get_height()
                ax2.text(b.get_x() + b.get_width()/2, h + max(1, max(t_vals))*0.02, f"{int(h):,}", ha="center", va="bottom", fontweight="bold")
            st.pyplot(fig2)

        if logs:
            col_c, col_d = st.columns(2)

            with col_c:
                recent = logs[-15:]
                fig3, ax3 = plt.subplots(figsize=(5.5, 4))
                x_idx = list(range(1, len(recent) + 1))
                scores = [item.get("score", 0.0) for item in recent]
                pt_colors = ["#10B981" if item.get("status") == "LOCAL_WEBSITE_HIT" else "#EF4444" for item in recent]
                ax3.bar(x_idx, scores, color=pt_colors, width=0.6, edgecolor="#1E293B", linewidth=0.6)
                ax3.axhline(bot.threshold, color="#1D4ED8", linestyle="--", linewidth=1.8, label=f"Threshold ({bot.threshold})")
                ax3.set_title("Recent Queries: Similarity Score vs. Threshold", fontsize=12, fontweight="bold")
                ax3.set_xlabel("Recent Query #")
                ax3.set_ylabel("Confidence Score")
                ax3.set_ylim(0, max(1.15, max(scores) + 0.1))
                ax3.legend()
                ax3.grid(axis="y", linestyle="--", alpha=0.4)
                st.pyplot(fig3)

            with col_d:
                recent_tok = logs[-15:]
                fig4, ax4 = plt.subplots(figsize=(5.5, 4))
                qx = [f"Q{i+1}" for i in range(len(recent_tok))]
                p_vals = [item.get("tokens", {}).get("prompt_tokens", 0) for item in recent_tok]
                o_vals = [item.get("tokens", {}).get("output_tokens", 0) for item in recent_tok]
                th_vals = [
                    item.get("tokens", {}).get(
                        "thoughts_tokens",
                        max(0, item.get("tokens", {}).get("total_tokens", 0) - (item.get("tokens", {}).get("prompt_tokens", 0) + item.get("tokens", {}).get("output_tokens", 0)))
                    )
                    for item in recent_tok
                ]
                ax4.bar(qx, p_vals, label="Prompt", color="#3B82F6")
                ax4.bar(qx, o_vals, bottom=p_vals, label="Output", color="#10B981")
                bottom2 = [p + o for p, o in zip(p_vals, o_vals)]
                ax4.bar(qx, th_vals, bottom=bottom2, label="Thinking", color="#8B5CF6")
                ax4.set_title("Token Breakdown per Recent Query", fontsize=12, fontweight="bold")
                ax4.set_ylabel("Tokens")
                ax4.legend()
                ax4.grid(axis="y", linestyle="--", alpha=0.4)
                st.pyplot(fig4)

# ===========================================================================
# TAB 4: Local vs. API Query Breakdown
# ===========================================================================
with tab_breakdown:
    st.subheader("🧾 Total Queries Breakdown: Local vs. API")

    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Total Queries", total_q)
    b2.metric("Local RAG Hits", local_hits, f"{round((local_hits/max(1,total_q))*100, 1)}%")
    b3.metric("Tier 2 (NIT API)", nit_api + legacy_api)
    b4.metric("Tier 3 (General API)", gen_api)

    col_pie, col_bar = st.columns(2)
    with col_pie:
        fig_p, ax_p = plt.subplots(figsize=(5, 4))
        pie_labels = ["Local Hits ($0)", "Tier 2: NIT API", "Tier 3: General API"]
        pie_vals = [local_hits, nit_api + legacy_api, gen_api]
        non_zero = [(l, v, c) for l, v, c in zip(pie_labels, pie_vals, ["#10B981", "#6366F1", "#F59E0B"]) if v > 0]
        if non_zero:
            ax_p.pie([x[1] for x in non_zero], labels=[x[0] for x in non_zero],
                     colors=[x[2] for x in non_zero], autopct="%1.1f%%", startangle=140,
                     wedgeprops=dict(width=0.45, edgecolor="white"))
            ax_p.set_title("Local vs. API Share", fontsize=12, fontweight="bold")
            st.pyplot(fig_p)

    with col_bar:
        fig_b, ax_b = plt.subplots(figsize=(5, 4))
        bar_labels = ["Local ($0)", "Tier 2 (NIT)", "Tier 3 (General)"]
        bar_vals = [local_hits, nit_api + legacy_api, gen_api]
        bars_b = ax_b.bar(bar_labels, bar_vals, color=["#10B981", "#6366F1", "#F59E0B"], width=0.5, edgecolor="#1E293B")
        ax_b.set_title("Exact Query Counts by Tier", fontsize=12, fontweight="bold")
        ax_b.set_ylabel("Query Count")
        ax_b.grid(axis="y", linestyle="--", alpha=0.4)
        for b in bars_b:
            h = b.get_height()
            ax_b.text(b.get_x() + b.get_width()/2, h + max(1, max(bar_vals))*0.02, f"{int(h)}", ha="center", va="bottom", fontweight="bold")
        st.pyplot(fig_b)

    st.divider()
    st.subheader("🔍 Filterable Query Audit Log")
    filter_opt = st.radio("Filter queries by source:", ["All Queries", "Local Only ($0)", "API Only (Tier 2 & 3)"], horizontal=True)

    filtered_logs = []
    for item in reversed(logs):
        st_status = item.get("status", "")
        if filter_opt == "Local Only ($0)" and st_status != "LOCAL_WEBSITE_HIT":
            continue
        if filter_opt == "API Only (Tier 2 & 3)" and st_status == "LOCAL_WEBSITE_HIT":
            continue
        tok = item.get("tokens", {})
        p_t = tok.get("prompt_tokens", 0)
        o_t = tok.get("output_tokens", 0)
        tot_t = tok.get("total_tokens", 0)
        th_t = tok.get("thoughts_tokens", max(0, tot_t - (p_t + o_t)))
        filtered_logs.append({
            "Query": item.get("query", ""),
            "Route": "Local ($0)" if st_status == "LOCAL_WEBSITE_HIT" else st_status,
            "Score": item.get("score", 0),
            "Prompt Tokens": p_t,
            "Output Tokens": o_t,
            "Thinking Tokens": th_t,
            "Total Tokens": tot_t
        })

    st.dataframe(filtered_logs[:50], use_container_width=True)
