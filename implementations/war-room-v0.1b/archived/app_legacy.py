"""
Four Horsemen War Room — Legacy Console
Runs the original 5-role pipeline defined in run_legacy.py
"""

import subprocess, sys
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="War Room — Legacy Edition", layout="wide")
st.title("⚙️  Four Horsemen War Room (Legacy Edition)")
st.caption("Runs the original Strategist → Analyst → Producer → Courier → Critic pipeline")

prompt = st.text_area(
    "Objective / Task",
    height=180,
    placeholder="Enter campaign objective or transcript..."
)

# resolve absolute path so Streamlit always finds run_legacy.py
LEGACY_PATH = Path(__file__).resolve().parent / "run_legacy.py"

if st.button("Run Legacy War Room"):
    with st.spinner("Executing legacy 5-role chain..."):
        cmd = [sys.executable, str(LEGACY_PATH)]
        if prompt.strip():
            cmd.append(prompt)
        subprocess.run(cmd)
        st.success("✅ Legacy run complete — check `/logs/` for output.")

st.sidebar.header("Legacy War Room Info")
st.sidebar.markdown("Uses **run_legacy.py** directly via subprocess.")
st.sidebar.markdown("Outputs stored in `/logs/` (Markdown + KPI CSV).")
