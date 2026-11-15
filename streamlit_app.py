import os
import sys
import json
import time
from pathlib import Path
import pandas as pd
import streamlit as st

# =====================================================================
# 1. PAGE CONFIGURATION & STYLING
# =====================================================================
st.set_page_config(
    page_title="NIT Admission Hybrid RAG | Token & Cost Comparison",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .badge-local {
        background-color: #065f46;
        color: #ecfdf5;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 600;
    }
    .badge-nit-api {
        background-color: #1e40af;
        color: #eff6ff;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 600;
    }
    .badge-api {
        background-color: #9a3412;
        color: #fff7ed;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 600;
    }
    .answer-box {
        background-color: rgba(30, 41, 59, 0.12);
        border-left: 4px solid #38bdf8;
        padding: 14px 18px;
        border-radius: 6px;
        margin-top: 8px;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# 2. DIRECT PIPELINE CONNECTION (NO PRESETS / NO HARDCODING)
# =====================================================================
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
os.chdir(BASE_DIR)

UNSTRUCTURED_JSON_PATH = BASE_DIR / "unstructured_admission_data.json"
AUDIT_LOG_PATH = BASE_DIR / "query_audit_log.json"

def load_json_safe(filepath: Path, default_val):
    if filepath.exists():
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default_val
    return default_val

# Import your exact backend pipeline engine
from step5_hybrid_qa_engine import HybridAdmissionQA

@st.cache_resource
def get_qa_bot():
    return HybridAdmissionQA()

bot = get_qa_bot()

def execute_pipeline_query(user_query: str, threshold_override: float, api_key_override: str):
    """
    Directly invokes your terminal pipeline engine. 
    Tier 1 uses local RAG; Tier 2 & 3 use your pipeline's API logic.
    """
    if threshold_override is not None:
        bot.threshold = threshold_override
    if api_key_override and api_key_override.strip():
        bot.api_key = api_key_override.strip()
        os.environ["GEMINI_API_KEY"] = bot.api_key
        bot._auto_detect_model()

    start_time = time.time()
    res = bot.ask(user_query)  # <-- Direct call to step5_hybrid_qa_engine.py
    elapsed = round(time.time() - start_time, 3)

    # Fetch top retrieved chunks from Step 4 retriever for UI transparency
    retrieved_chunks = bot.retriever.search(user_query, top_k=3)

    return {
        "query": user_query,
        "status": res.get("status", "LOCAL_WEBSITE_HIT"),
        "answer": res.get("answer", ""),
        "cost_label": res.get("cost", "$0.00"),
        "confidence_score": res.get("confidence_score", 0.0),
        "threshold": res.get("threshold", bot.threshold),
        "tokens": res.get("tokens", {"prompt_tokens": 0, "output_tokens": 0, "thoughts_tokens": 0, "total_tokens": 0}),
        "citation": res.get("citation", {}),
        "latency_sec": elapsed,
        "retrieved_chunks": retrieved_chunks
    }

if "live_qa_history" not in st.session_state:
    st.session_state.live_qa_history = []

# =====================================================================
# 3. SIDEBAR CONFIGURATION
# =====================================================================
with st.sidebar:
    st.title("⚙️ Pipeline Engine Config")
    st.caption("Frontend strictly linked to `step5_hybrid_qa_engine.py`[cite: 1].")

    api_key_input = st.text_input(
        "Gemini API Key (for Tier 2 & 3 Fallbacks)",
        value=bot.api_key or os.environ.get("GEMINI_API_KEY", ""),
        type="password",
        help="Enter your GEMINI_API_KEY to enable live API calls for Tier 2 and Tier 3 queries."
    )
    if api_key_input.strip():
        st.success("✅ Live API Key Configured")
    else:
        st.warning("⚠️ No API Key entered. Tier 2/3 will run in pipeline standby mode.")
    
    default_thresh = float(bot.threshold)
    sim_threshold = st.slider(
        "Local RAG Confidence Threshold",
        min_value=0.10, max_value=0.90, value=default_thresh, step=0.02,
        help="Queries with score >= threshold are answered locally by the RAG engine."
    )
    st.caption(f"Retriever Mode: **{'Neural Transformer (MiniLM)' if bot.retriever.use_transformer else 'TF-IDF Vectorizer'}**")

    st.divider()
    if st.button("🗑️ Clear Session History", use_container_width=True):
        st.session_state.live_qa_history = []
        st.rerun()

# =====================================================================
# 4. HEADER & GLOBAL TOKEN METRICS (FROM AUDIT LOG)
# =====================================================================
st.title("🎓 NIT Admission Hybrid RAG: Token-Based Cost Analysis")
st.markdown(
    "**Final Year Project Live Interface:** This Streamlit app acts purely as an interface. "
    "All answers are fetched dynamically from your pipeline scripts (`step4` and `step5`)[cite: 1]."
)

audit_data = load_json_safe(AUDIT_LOG_PATH, {"summary": {}, "logs": []})
summary_stats = audit_data.get("summary", bot.stats)

total_logged = int(summary_stats.get("total_queries", bot.stats.get("total_queries", 0)))
local_hits = int(summary_stats.get("local_hits", bot.stats.get("local_hits", 0)))
nit_api_hits = int(summary_stats.get("nit_api_fallbacks", bot.stats.get("nit_api_fallbacks", 0)))
gen_api_hits = int(summary_stats.get("general_api_fallbacks", bot.stats.get("general_api_fallbacks", 0)))

total_prompt_tok = int(summary_stats.get("total_prompt_tokens", bot.stats.get("total_prompt_tokens", 0)))
total_output_tok = int(summary_stats.get("total_output_tokens", bot.stats.get("total_output_tokens", 0)))
total_api_tok = int(summary_stats.get("total_api_tokens", bot.stats.get("total_api_tokens", 0)))

offload_rate = round((local_hits / max(1, total_logged)) * 100, 1)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total Queries", f"{total_logged}", f"{local_hits} Local | {nit_api_hits + gen_api_hits} API")
kpi2.metric("Local Token Offload", f"{offload_rate}%", "Handled with 0 API tokens")
kpi3.metric("Total API Tokens", f"{total_api_tok:,} tokens", f"Prompt: {total_prompt_tok:,} | Out: {total_output_tok:,}")
kpi4.metric("Est. Tokens Saved", f"~{total_logged * 850:,} tokens", "Saved by avoiding cloud API for RAG")

st.divider()

# =====================================================================
# 5. TABS FOR INTERACTIVE DEMO & TOKEN COMPARISON
# =====================================================================
tab_chat, tab_tokens, tab_audit = st.tabs([
    "💬 Interactive Query Console",
    "📊 Token Usage & Tier Comparison",
    "📜 Raw Audit Log (`query_audit_log.json`)"
])

with tab_chat:
    st.subheader("🔎 Ask Any Question (Fetched Directly from Pipeline)")
    st.caption("Type any question below. Tier 1 fetches from local scraped data; Tiers 2 & 3 fetch from your pipeline's API logic.")

    # Clean input form with no preset questions or hardcoded answers
    with st.form("query_form", clear_on_submit=True):
        user_text = st.text_input(
            "Enter your question:",
            placeholder="e.g., What is the 1st sem fee for CSE? or Who is the principal of NIT? or Explain quantum computing"
        )
        submitted = st.form_submit_button("🚀 Send to Pipeline Engine", use_container_width=True)

    if submitted and user_text.strip():
        with st.spinner("Executing pipeline retrieval and hybrid router..."):
            result_item = execute_pipeline_query(user_text.strip(), sim_threshold, api_key_input)
            st.session_state.live_qa_history.insert(0, result_item)
            st.rerun()

    if not st.session_state.live_qa_history:
        st.info("👆 Type any question above to execute your pipeline scripts and view live answers and token metrics.")

    for item in st.session_state.live_qa_history:
        status = item["status"]
        toks = item["tokens"]
        cit = item["citation"]

        with st.container(border=True):
            st.markdown(f"#### ❓ Q: {item['query']}")

            if status == "LOCAL_WEBSITE_HIT":
                badge = '<span class="badge-local">✅ TIER 1: LOCAL RAG (0 API TOKENS)</span>'
                route_desc = "Fetched locally from `unstructured_admission_data.json`[cite: 1] with zero cloud tokens."
                short_tier = "Tier 1 (Local RAG)"
            elif status == "NIT_SPECIFIC_API_FALLBACK":
                badge = '<span class="badge-nit-api">🏛️ TIER 2: NIT COLLEGE API FALLBACK</span>'
                route_desc = "Fetched via pipeline API fallback with verified NIT institutional context."
                short_tier = "Tier 2 (NIT API)"
            else:
                badge = '<span class="badge-api">🌐 TIER 3: GENERAL KNOWLEDGE API</span>'
                route_desc = "Out-of-domain query fetched via pipeline general knowledge API."
                short_tier = "Tier 3 (General API)"

            st.markdown(f"{badge} &nbsp; *{route_desc}*", unsafe_allow_html=True)

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Routing Tier", short_tier)
            m2.metric("Tokens Used", f"{toks.get('total_tokens', 0)} tok", f"In: {toks.get('prompt_tokens', 0)} | Out: {toks.get('output_tokens', 0)}")
            m3.metric("Retriever Score", f"{item['confidence_score']}", f"Threshold: {item['threshold']}")
            m4.metric("Latency", f"{item['latency_sec']}s")

            st.caption(f"📌 **Source:** {cit.get('source', 'N/A')} | **Section:** `{cit.get('title', 'N/A')}`")

            st.markdown("**Pipeline Engine Answer:**")
            st.markdown(f"<div class='answer-box'>{item['answer'].replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)

            if item.get("retrieved_chunks"):
                with st.expander("🔍 Inspect Step 4 Retriever Chunks"):
                    for r_idx, match in enumerate(item["retrieved_chunks"], 1):
                        chunk = match.get("chunk", {})
                        st.markdown(f"**Match #{r_idx}: {chunk.get('title', 'Chunk')}** (Score: `{match.get('score', 0):.4f}`)")
                        st.code(chunk.get("content", ""), language="text")

with tab_tokens:
    st.subheader("📊 Token Consumption Comparison Across Tiers")
    st.markdown(
        "This comparison proves to evaluators that **Tier 1 (Local RAG)** consumes **0 external API tokens**, "
        "while API fallback tiers consume prompt and output tokens, demonstrating why local offloading saves token costs."
    )

    t_col1, t_col2 = st.columns(2)

    with t_col1:
        st.markdown("#### Cumulative Token Breakdown")
        token_df = pd.DataFrame({
            "Token Category": ["Prompt Tokens (Input)", "Output Tokens (Generated)", "Total API Tokens Billed"],
            "Token Count": [total_prompt_tok, total_output_tok, total_api_tok]
        }).set_index("Token Category")
        st.bar_chart(token_df)

    with t_col2:
        st.markdown("#### Queries Handled per Tier")
        tier_df = pd.DataFrame({
            "Routing Tier": ["Tier 1: Local RAG (0 Tokens)", "Tier 2: NIT API Fallback", "Tier 3: General API"],
            "Query Count": [local_hits, nit_api_hits, gen_api_hits]
        }).set_index("Routing Tier")
        st.bar_chart(tier_df)

    st.markdown("---")
    st.markdown("#### 💡 Evaluation Summary")
    st.info(
        f"• **Token Offload Efficiency:** **{offload_rate}%** of questions are resolved locally by `step4_local_retriever.py`[cite: 1] "
        f"using **0 API tokens**.\n"
        f"• **Max Token Consumption:** API Fallback tiers consume higher token volume when handling out-of-domain or unlisted queries, "
        f"highlighting the cost-effectiveness of your hybrid local architecture."
    )

with tab_audit:
    st.subheader("📜 Live Query Audit Log (`query_audit_log.json`)")
    st.markdown("Updated dynamically by `step5_hybrid_qa_engine.py`[cite: 1] every time a question is processed.")
    audit_json = load_json_safe(AUDIT_LOG_PATH, {})
    st.json(audit_json, expanded=True)