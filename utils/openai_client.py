import json
import os
from openai import OpenAI

# the newest OpenAI model is "gpt-5" which was released August 7, 2025.
# do not change this unless explicitly requested by the user

class OpenAIClient:
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(api_key=self.api_key)
    
    def extract_protocol_info(self, protocol_text):
        """Extract key information from clinical trial protocol text"""
        prompt = f"""
        Analyze the following clinical trial protocol and extract key information in JSON format.
        
        Extract the following fields:
        - title: study title
        - phase: clinical trial phase
        - primary_endpoint: primary endpoint description
        - secondary_endpoints: list of secondary endpoints
        - study_design: study design type
        - target_enrollment: target number of participants
        - duration: study duration
        - sponsor: study sponsor
        - therapeutic_area: therapeutic area/indication
        - intervention: intervention/treatment description
        
        Protocol text:
        {protocol_text}
        
        Respond with valid JSON only.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-5",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert clinical research analyst. Extract key information from clinical trial protocols and respond only with valid JSON."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    def suggest_optimizations(self, protocol_text):
        """Suggest optimizations for clinical trial protocol"""
        prompt = f"""
        Analyze the following clinical trial protocol and suggest optimizations.
        
        Provide suggestions in the following categories in JSON format:
        - enrollment_strategies: ways to improve patient recruitment
        - endpoint_optimization: suggestions for primary/secondary endpoints
        - study_design_improvements: design optimization recommendations
        - operational_efficiency: operational improvements
        - regulatory_considerations: regulatory optimization suggestions
        - patient_experience: patient-centric improvements
        
        Protocol text:
        {protocol_text}
        
        For each category, provide a list of specific, actionable recommendations.
        Respond with valid JSON only.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-5",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert clinical trial optimization consultant. Provide specific, actionable recommendations in JSON format."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    def extract_eligibility_criteria(self, protocol_text):
        """Extract structured eligibility criteria from protocol text"""
        prompt = f"""
        Extract all inclusion and exclusion criteria from the following clinical trial protocol.
        
        Return the results in JSON format with:
        - inclusion_criteria: array of inclusion criteria statements
        - exclusion_criteria: array of exclusion criteria statements
        - age_requirements: specific age requirements
        - gender_requirements: gender-specific requirements
        - medical_conditions: required or excluded medical conditions
        - medications: medication requirements or restrictions
        - laboratory_requirements: lab value requirements
        
        Protocol text:
        {protocol_text}
        
        Extract each criterion as a clear, standalone statement.
        Respond with valid JSON only.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-5",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert clinical research coordinator. Extract eligibility criteria accurately and comprehensively in JSON format."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    def generate_patient_profile(self, filters):
        """Generate a synthetic patient profile based on filters"""
        prompt = f"""
        Generate a realistic synthetic patient profile based on the following criteria:
        
        Filters: {json.dumps(filters, indent=2)}
        
        Create a comprehensive patient profile in JSON format with:
        - demographics: age, gender, ethnicity, weight, height, BMI
        - medical_history: relevant medical conditions and history
        - current_medications: current medication list with dosages
        - laboratory_values: relevant lab values (within normal ranges unless conditions require otherwise)
        - vital_signs: blood pressure, heart rate, temperature, respiratory rate
        - allergies: drug and environmental allergies
        - social_history: smoking, alcohol, exercise habits
        - insurance_info: insurance type and coverage
        - contact_info: basic contact information (synthetic)
        - emergency_contact: emergency contact information (synthetic)
        
        Ensure the profile is medically consistent and realistic.
        Use synthetic but realistic names, addresses, and contact information.
        Respond with valid JSON only.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-5",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert medical data scientist creating realistic synthetic patient profiles. Ensure all data is medically consistent and follows realistic patterns."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
