"""
AxProtocol Operator Console with ENFORCEMENT METRICS
Now displays TAES scores, IRD trends, and ledger integrity.
"""

import streamlit as st
from run_axp import run_chain, log_session, MODEL, TIER, DOMAIN
from ledger import get_last_n_entries, verify_hash_chain
from taes_evaluation import check_cognitive_disalignment
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="AxProtocol Operator Console", layout="wide")
st.title("⚙️  AxProtocol Operator Console — v2.3 ENFORCED")
st.caption(f"Running in **{TIER}** mode  →  using **{MODEL}**  →  domain: **{DOMAIN}**")

# Sidebar: System status
st.sidebar.header("🔐 System Status")

# Check ledger integrity
integrity = verify_hash_chain()
if integrity['valid']:
    st.sidebar.success(f"✅ Ledger integrity verified ({integrity['entries']} entries)")
else:
    st.sidebar.error(f"❌ Ledger compromised: {len(integrity['broken'])} broken hashes")

# Check cognitive disalignment
disalignment = check_cognitive_disalignment()
if disalignment['alert']:
    st.sidebar.warning(f"⚠️ {disalignment['reason']}")
else:
    st.sidebar.info(f"✅ IRD avg: {disalignment.get('avg_ird', 'N/A')}")

# Recent ledger entries
st.sidebar.subheader("Recent Activity")
recent = get_last_n_entries(5)
for entry in recent:
    st.sidebar.text(f"[{entry['id']}] {entry['role_name']}")

st.sidebar.markdown("---")
st.sidebar.markdown("**Logs:** `logs/sessions/`  \n**Ledger:** `logs/ledger/audit_ledger.db`  \n**IRD:** `logs/ird_log.csv`")

# Main interface
prompt = st.text_area(
    "Objective / Transcript",
    height=180,
    placeholder="Enter campaign objective, transcript, or query..."
)

col1, col2 = st.columns([3, 1])
with col1:
    run_button = st.button("🚀 Run AxProtocol War Room", type="primary")
with col2:
    domain = st.selectbox("Domain", ["marketing", "ops", "code", "creative"], index=0)

if run_button:
    if not prompt.strip():
        st.warning("Please enter an objective or transcript first.")
    else:
        import os
        os.environ['DOMAIN'] = domain

        with st.spinner("Executing AxProtocol reasoning chain with full enforcement..."):
            s, a, p_rev, c_rev, crit, results = run_chain(prompt)
            log_file = log_session(prompt, s, a, p_rev, c_rev, crit, results)

            st.success("✅ AxProtocol chain complete — check /logs/ for output.")

            # Display TAES metrics
            st.markdown("---")
            st.subheader("📊 TAES Evaluation Summary")

            taes_data = []
            for role_key in ['strategist', 'analyst', 'producer_revised', 'courier_revised']:
                if role_key in results and 'taes' in results[role_key]:
                    taes = results[role_key]['taes']
                    taes_data.append({
                        'Role': taes['role_name'],
                        'IV': taes['integrity_vector'],
                        'IRD': taes['ird'],
                        'RRP Required': '⚠️' if taes['requires_rrp'] else '✅'
                    })

            if taes_data:
                st.dataframe(pd.DataFrame(taes_data), use_container_width=True)

            # Display outputs
            st.markdown("---")

            tab1, tab2, tab3 = st.tabs(["📝 Producer", "📅 Courier", "🔍 Critic"])

            with tab1:
                st.markdown("### Producer [Revised]")
                st.write(p_rev)
                if 'producer_revised' in results:
                    taes = results['producer_revised']['taes']
                    st.caption(f"TAES → IV: {taes['integrity_vector']}, IRD: {taes['ird']}")

            with tab2:
                st.markdown("### Courier [Revised]")
                st.write(c_rev)
                if 'courier_revised' in results:
                    taes = results['courier_revised']['taes']
                    st.caption(f"TAES → IV: {taes['integrity_vector']}, IRD: {taes['ird']}")

            with tab3:
                st.markdown("### Critic Summary")
                st.write(crit)

# IRD trend visualization
st.markdown("---")
st.subheader("📈 IRD Trend (Last 30 Executions)")

ird_path = Path("logs/ird_log.csv")
if ird_path.exists():
    try:
        df = pd.read_csv(ird_path)
        df_recent = df.tail(30)
        st.line_chart(df_recent[['ird']])

        avg_ird = df_recent['ird'].mean()
        if avg_ird > 0.4:
            st.error(f"⚠️ Cognitive Disalignment Alert: Average IRD = {avg_ird:.3f}")
        else:
            st.success(f"✅ IRD healthy: {avg_ird:.3f}")
    except Exception as e:
        st.warning(f"Could not load IRD data: {e}")
else:
    st.info("No IRD data yet. Run a chain to start collecting metrics.")