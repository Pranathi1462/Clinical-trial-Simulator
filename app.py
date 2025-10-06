# app.py
import streamlit as st
import pandas as pd

from modules.protocol_parser import parse_protocol
from modules.eligibility_extractor import struct_to_form
from modules.patient_generator import generate_patients
from modules.protocol_optimizer import ProtocolOptimizer

st.set_page_config(page_title="Protocol → Optimizer → Eligibility → Synthetic Patient Generator", layout="wide")

st.title("Clinical Trial Protocol Generator + Optimizer + Synthetic Patient Generator (MVP)")

st.markdown("""
Paste a short clinical trial concept or protocol summary below.  
Then press **Generate Protocols** → **Optimize** → **Generate Patients**.
""")

# --- Sample Protocol ---
with st.expander("📘 Sample Protocol (click to view)"):
    st.code("""Multiple Sclerosis prevention trial
Inclusion: Age between 18 and 45, clinically isolated syndrome, EBV negative preferred.
Exclusion: Prior EBV vaccination, immunosuppressant use in past 6 months.
Sample size n=200
Primary endpoint: Time to first clinical relapse over 12 months.
""")

# --- User Input ---
protocol_text = st.text_area("✍️ Enter protocol concept", height=180)

# --- Generate Full Protocol Drafts ---
if st.button("🚀 Generate Full Protocol Drafts"):
    try:
        from os import getenv
        groq_key = getenv("GROQ_API_KEY")
        optimizer = ProtocolOptimizer(api_key=groq_key)
        drafts = optimizer.generate_full_protocol(protocol_text, n_options=3, include_references=True)
        st.session_state['drafts'] = drafts
        st.success(f"✅ Generated {len(drafts)} protocol drafts successfully!")
        for i, d in enumerate(drafts):
            st.subheader(f"Draft {i+1}")
            st.json(d)
    except Exception as e:
        st.error(f"❌ Failed to generate protocols: {e}")

# --- Optimize Protocols ---
if 'drafts' in st.session_state and st.button("⚙️ Optimize Protocol Drafts"):
    try:
        optimizer = ProtocolOptimizer(api_key=None)  # Key is already set via env
        optimized = []
        for draft in st.session_state['drafts']:
            optimized.extend(optimizer.generate_full_protocol(str(draft), n_options=1))
        st.session_state['optimized'] = optimized
        st.success(f"Optimized {len(optimized)} drafts.")
    except Exception as e:
        st.error(f"❌ Optimization failed: {e}")

# --- Display Optimized Results ---
if 'optimized' in st.session_state:
    st.subheader("Optimized Protocol Drafts")
    for i, p in enumerate(st.session_state['optimized']):
        with st.expander(f"Optimized Draft {i+1}"):
            st.json(p)

# --- Parse Eligibility and Generate Patients ---
if protocol_text and st.button("🧬 Parse Eligibility & Generate Patients"):
    try:
        parsed = parse_protocol(protocol_text)
        form = struct_to_form(parsed)
        st.session_state['parsed'] = parsed

        st.subheader("Eligibility Criteria")
        with st.form("eligibility_form"):
            age_min = st.number_input("Minimum Age", value=form['age_min'])
            age_max = st.number_input("Maximum Age", value=form['age_max'])
            biomarkers = st.text_input("Biomarkers (comma-separated)", value=",".join(form['biomarkers']))
            exclusions = st.text_area("Exclusion Criteria", value="\n".join(form['exclusions']))
            n_patients = st.number_input("Number of synthetic patients", min_value=10, max_value=2000, value=50)
            submit = st.form_submit_button("Generate Patients")

        if submit:
            criteria = {
                "age_min": int(age_min),
                "age_max": int(age_max),
                "biomarkers": [b.strip() for b in biomarkers.split(",") if b.strip()],
                "exclusions": [e.strip() for e in exclusions.splitlines() if e.strip()]
            }
            df = generate_patients(criteria, n=int(n_patients), seed=42)
            st.success(f"Generated {len(df)} synthetic patients!")
            st.dataframe(df.head(50))
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV", csv, "synthetic_patients.csv", "text/csv")

    except Exception as e:
        st.error(f"❌ Failed to parse or generate patients: {e}")