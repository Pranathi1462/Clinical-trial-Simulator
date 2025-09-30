import streamlit as st
import json
from modules.protocol_parser import ProtocolParser
from modules.patient_generator import PatientGenerator
from modules.eligibility_extractor import EligibilityExtractor
from modules.clinicaltrials_api import ClinicalTrialsAPI

def main():
    st.set_page_config(
        page_title="Clinical Trial AI Simulator",
        page_icon="🏥",
        layout="wide"
    )
    
    st.title("🏥 Clinical Trial AI Simulator")
    st.markdown("Advanced AI-powered tools for clinical trial analysis and patient simulation")
    
    # Initialize session state
    if 'api_key_set' not in st.session_state:
        st.session_state.api_key_set = False
    
    # Check for OpenAI API key
    api_key = st.text_input("Enter OpenAI API Key:", type="password", key="openai_key")
    if api_key:
        import os
        os.environ["GROQ_API_KEY"] = api_key
        st.session_state.api_key_set = True
        st.success("API Key set successfully!")
    
    if not st.session_state.api_key_set:
        st.warning("Please enter your OpenAI API key to use the AI features.")
        return
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    module = st.sidebar.selectbox(
        "Select Module:",
        ["Protocol Parser", "Patient Generator", "Eligibility Extractor"]
    )
    
    # Module routing
    if module == "Protocol Parser":
        protocol_parser_module()
    elif module == "Patient Generator":
        patient_generator_module()
    elif module == "Eligibility Extractor":
        eligibility_extractor_module()

def protocol_parser_module():
    st.header("📋 Protocol Parser & Optimizer")
    st.markdown("Extract key information from clinical trial protocols and get AI-powered optimization suggestions.")
    
    # Initialize parser
    parser = ProtocolParser()
    
    # Tab layout
    tab1, tab2 = st.tabs(["Manual Input", "ClinicalTrials.gov"])
    
    with tab1:
        st.subheader("Manual Protocol Input")
        protocol_text = st.text_area(
            "Enter Clinical Trial Protocol Text:",
            height=300,
            placeholder="Paste your clinical trial protocol text here..."
        )
        
        if st.button("Parse & Optimize Protocol", key="parse_manual"):
            if protocol_text:
                with st.spinner("Analyzing protocol with AI..."):
                    try:
                        result = parser.parse_protocol(protocol_text)
                        
                        # Display results
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("📊 Extracted Information")
                            st.json(result['extracted_info'])
                        
                        with col2:
                            st.subheader("💡 Optimization Suggestions")
                            st.json(result['optimizations'])
                    
                    except Exception as e:
                        st.error(f"Error processing protocol: {str(e)}")
            else:
                st.warning("Please enter protocol text.")
    
    with tab2:
        st.subheader("ClinicalTrials.gov Integration")
        nct_id = st.text_input(
            "Enter NCT ID:",
            placeholder="e.g., NCT04567890"
        )
        
        if st.button("Fetch & Analyze", key="fetch_analyze"):
            if nct_id:
                with st.spinner("Fetching protocol from ClinicalTrials.gov..."):
                    try:
                        api = ClinicalTrialsAPI()
                        protocol_data = api.fetch_study(nct_id)
                        
                        if protocol_data:
                            st.success(f"Successfully fetched study: {protocol_data.get('title', 'Unknown Title')}")
                            
                            # Parse the fetched protocol
                            with st.spinner("Analyzing protocol with AI..."):
                                protocol_text = api.format_study_for_analysis(protocol_data)
                                result = parser.parse_protocol(protocol_text)
                                
                                # Display results
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.subheader("📊 Extracted Information")
                                    st.json(result['extracted_info'])
                                
                                with col2:
                                    st.subheader("💡 Optimization Suggestions")
                                    st.json(result['optimizations'])
                        else:
                            st.error("Failed to fetch study data.")
                    
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                st.warning("Please enter an NCT ID.")

def patient_generator_module():
    st.header("👥 Synthetic Patient Generator")
    st.markdown("Generate realistic patient profiles with customizable demographic and clinical filters.")
    
    generator = PatientGenerator()
    
    # Filters section
    st.subheader("🔧 Patient Filters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Demographics**")
        age_range = st.slider("Age Range", 0, 100, (20, 80))
        gender = st.multiselect("Gender", ["male", "female", "other"], default=["male", "female"])
        ethnicity = st.multiselect(
            "Ethnicity", 
            ["white", "black", "hispanic", "asian", "other"],
            default=["white", "black", "hispanic", "asian"]
        )
    
    with col2:
        st.markdown("**Clinical Conditions**")
        conditions = st.text_area(
            "Medical Conditions (one per line):",
            placeholder="diabetes\nhypertension\nasthma"
        )
        
        exclusion_conditions = st.text_area(
            "Exclusion Conditions (one per line):",
            placeholder="pregnancy\nactive cancer"
        )
    
    with col3:
        st.markdown("**Medications**")
        medications = st.text_area(
            "Required Medications (one per line):",
            placeholder="metformin\nlisinopril"
        )
        
        exclusion_medications = st.text_area(
            "Exclusion Medications (one per line):",
            placeholder="warfarin\nimmuno suppressants"
        )
    
    # Generation parameters
    st.subheader("⚙️ Generation Parameters")
    col1, col2 = st.columns(2)
    
    with col1:
        num_patients = st.number_input("Number of Patients", min_value=1, max_value=100, value=10)
    
    with col2:
        output_format = st.selectbox("Output Format", ["JSON", "CSV", "Synthea Compatible"])
    
    # Generate patients
    if st.button("Generate Patients", key="generate_patients"):
        filters = {
            "age_range": age_range,
            "gender": gender,
            "ethnicity": ethnicity,
            "conditions": [c.strip() for c in conditions.split('\n') if c.strip()],
            "exclusion_conditions": [c.strip() for c in exclusion_conditions.split('\n') if c.strip()],
            "medications": [m.strip() for m in medications.split('\n') if m.strip()],
            "exclusion_medications": [m.strip() for m in exclusion_medications.split('\n') if m.strip()]
        }
        
        with st.spinner("Generating synthetic patients..."):
            try:
                patients = generator.generate_patients(num_patients, filters, output_format.lower())
                
                st.success(f"Successfully generated {len(patients)} patients!")
                
                # Display results
                if output_format == "JSON":
                    st.subheader("Generated Patients (JSON)")
                    st.json(patients)
                elif output_format == "CSV":
                    st.subheader("Generated Patients (CSV)")
                    import pandas as pd
                    df = pd.DataFrame(patients)
                    st.dataframe(df)
                    
                    # Download button
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name="synthetic_patients.csv",
                        mime="text/csv"
                    )
                else:  # Synthea Compatible
                    st.subheader("Generated Patients (Synthea Compatible)")
                    st.json(patients)
                    
                    # Download button
                    json_str = json.dumps(patients, indent=2)
                    st.download_button(
                        label="Download JSON",
                        data=json_str,
                        file_name="synthea_patients.json",
                        mime="application/json"
                    )
            
            except Exception as e:
                st.error(f"Error generating patients: {str(e)}")

def eligibility_extractor_module():
    st.header("✅ Eligibility Criteria Extractor")
    st.markdown("Extract and structure inclusion/exclusion criteria from clinical trial protocols.")
    
    extractor = EligibilityExtractor()
    
    # Tab layout
    tab1, tab2 = st.tabs(["Manual Input", "ClinicalTrials.gov"])
    
    with tab1:
        st.subheader("Manual Protocol Input")
        protocol_text = st.text_area(
            "Enter Clinical Trial Protocol Text:",
            height=300,
            placeholder="Paste protocol text containing eligibility criteria..."
        )
        
        if st.button("Extract Criteria", key="extract_manual"):
            if protocol_text:
                with st.spinner("Extracting eligibility criteria..."):
                    try:
                        criteria = extractor.extract_criteria(protocol_text)
                        
                        # Display results
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("✅ Inclusion Criteria")
                            if criteria['inclusion_criteria']:
                                for i, criterion in enumerate(criteria['inclusion_criteria'], 1):
                                    st.write(f"{i}. {criterion}")
                            else:
                                st.info("No inclusion criteria found.")
                        
                        with col2:
                            st.subheader("❌ Exclusion Criteria")
                            if criteria['exclusion_criteria']:
                                for i, criterion in enumerate(criteria['exclusion_criteria'], 1):
                                    st.write(f"{i}. {criterion}")
                            else:
                                st.info("No exclusion criteria found.")
                        
                        # Structured output
                        st.subheader("📋 Structured Output")
                        st.json(criteria)
                        
                        # Download button
                        json_str = json.dumps(criteria, indent=2)
                        st.download_button(
                            label="Download Criteria JSON",
                            data=json_str,
                            file_name="eligibility_criteria.json",
                            mime="application/json"
                        )
                    
                    except Exception as e:
                        st.error(f"Error extracting criteria: {str(e)}")
            else:
                st.warning("Please enter protocol text.")
    
    with tab2:
        st.subheader("ClinicalTrials.gov Integration")
        nct_id = st.text_input(
            "Enter NCT ID:",
            placeholder="e.g., NCT04567890",
            key="nct_eligibility"
        )
        
        if st.button("Fetch & Extract", key="fetch_extract"):
            if nct_id:
                with st.spinner("Fetching study from ClinicalTrials.gov..."):
                    try:
                        api = ClinicalTrialsAPI()
                        protocol_data = api.fetch_study(nct_id)
                        
                        if protocol_data:
                            st.success(f"Successfully fetched study: {protocol_data.get('title', 'Unknown Title')}")
                            
                            # Extract criteria
                            with st.spinner("Extracting eligibility criteria..."):
                                protocol_text = api.format_study_for_analysis(protocol_data)
                                criteria = extractor.extract_criteria(protocol_text)
                                
                                # Display results
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.subheader("✅ Inclusion Criteria")
                                    if criteria['inclusion_criteria']:
                                        for i, criterion in enumerate(criteria['inclusion_criteria'], 1):
                                            st.write(f"{i}. {criterion}")
                                    else:
                                        st.info("No inclusion criteria found.")
                                
                                with col2:
                                    st.subheader("❌ Exclusion Criteria")
                                    if criteria['exclusion_criteria']:
                                        for i, criterion in enumerate(criteria['exclusion_criteria'], 1):
                                            st.write(f"{i}. {criterion}")
                                    else:
                                        st.info("No exclusion criteria found.")
                                
                                # Structured output
                                st.subheader("📋 Structured Output")
                                st.json(criteria)
                                
                                # Download button
                                json_str = json.dumps(criteria, indent=2)
                                st.download_button(
                                    label="Download Criteria JSON",
                                    data=json_str,
                                    file_name=f"eligibility_criteria_{nct_id}.json",
                                    mime="application/json"
                                )
                        else:
                            st.error("Failed to fetch study data.")
                    
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                st.warning("Please enter an NCT ID.")

if __name__ == "__main__":
    main()
