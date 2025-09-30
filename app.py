# app.py
import streamlit as st
import pandas as pd
from modules.protocol_parser import parse_protocol
from modules.eligibility_extractor import struct_to_form
from modules.patient_generator import generate_patients
from modules.protocol_optimizer import optimize_protocol

st.set_page_config(page_title="Protocol + Synthetic Patient Prototype", layout="wide")

st.title("Protocol → Optimizer → Eligibility → Synthetic Patient Generator (MVP)")

st.markdown("Paste a trial protocol text (short) and press Parse → Optimize → Generate patients.")

with st.expander("Sample protocol (click to view)"):
    st.code("""Multiple Sclerosis prevention trial
Inclusion: Age between 18 and 45, clinically isolated syndrome, EBV negative preferred.
Exclusion: Prior EBV vaccination, immunosuppressant use in past 6 months.
Sample size n=200
Primary endpoint: Time to first clinical relapse over 12 months.
""")

# 1) Input protocol
protocol_text = st.text_area("Protocol text", height=180)

if st.button("Parse protocol"):
    parsed = parse_protocol(protocol_text)
    st.session_state['parsed'] = parsed
    st.write("Parsed:")
    st.json(parsed)

# 2) Optimize
if 'parsed' in st.session_state:
    parsed = st.session_state['parsed']
    if st.button("Optimize and propose 3 protocols"):
        proposals = optimize_protocol(parsed, pool_size=18, pick_k=3)
        st.session_state['proposals'] = proposals

# Show proposals
if 'proposals' in st.session_state:
    st.subheader("Protocol proposals (select one)")
    cols = st.columns(len(st.session_state['proposals']))
    selected_idx = None
    for i, p in enumerate(st.session_state['proposals']):
        with cols[i]:
            st.write(f"### Proposal {i+1}")
            st.write(f"- Sample size: {p['sample_size']}")
            st.write(f"- Randomization ratio (control:treatment): {p['rand_ratio']}")
            st.write(f"- Looseness score: {p['looseness']}")
            st.write(f"- Combined score: {p['score']:.3f}")
            if st.button(f"Select Proposal {i+1}", key=f"sel_{i}"):
                st.session_state['selected_proposal'] = p

# 3) Show editable eligibility form from selected proposal (uses parsed)
if 'selected_proposal' in st.session_state and 'parsed' in st.session_state:
    st.subheader("Editable Eligibility (prefilled from parsed protocol)")
    parsed = st.session_state['parsed']
    form = struct_to_form(parsed)
    with st.form("elig_form"):
        age_min = st.number_input("Min age", value=form['age_min'])
        age_max = st.number_input("Max age", value=form['age_max'])
        biomarker_list = form['biomarkers']
        biomarkers_str = st.text_input("Biomarkers (comma-separated)", value=",".join(biomarker_list))
        exclusions = st.text_area("Exclusions (one per line)", value="\n".join(form['exclusions']))
        num_patients = st.number_input("Number of synthetic patients to generate", min_value=1, max_value=2000, value=50)
        submit = st.form_submit_button("Generate synthetic patients")

    if submit:
        criteria = {
            "age_min": int(age_min),
            "age_max": int(age_max),
            "biomarkers": [b.strip() for b in biomarkers_str.split(",") if b.strip()],
            "exclusions": [l.strip() for l in exclusions.splitlines() if l.strip()]
        }
        df = generate_patients(criteria, n=int(num_patients), seed=42)
        st.success(f"Generated {len(df)} synthetic patients")
        st.dataframe(df.head(50))
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(label="Download CSV", data=csv, file_name="synthetic_patients.csv", mime="text/csv")

