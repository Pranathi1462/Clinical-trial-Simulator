
# import json
# import os
# from groq import Groq

# # Groq uses similar structure but requires the GROQ_API_KEY
# # Install: pip install groq

# class GroqClient:
#     def __init__(self):
#         self.api_key = os.environ.get("GROQ_API_KEY")
#         if not self.api_key:
#             raise ValueError("GROQ_API_KEY environment variable is required")
        
#         self.client = Groq(api_key=self.api_key)

#     def _chat_request(self, system_content, user_content):
#         """Internal helper to send chat request to Groq API"""
#         response = self.client.chat.completions.create(
#             model="llama-3.3-70b-versatile",  # Groq’s LLM (adjust if needed)
#             messages=[
#                 {"role": "system", "content": system_content},
#                 {"role": "user", "content": user_content},
#             ],
#         )
#         content = response.choices[0].message.content
#         if not content:
#             raise ValueError("Empty response from Groq API")
#         return content

#     def extract_protocol_info(self, protocol_text):
#         """Extract key information from clinical trial protocol text"""
#         prompt = f"""
#         Analyze the following clinical trial protocol and extract key information in JSON format.

#         Extract the following fields:
#         - title: study title
#         - phase: clinical trial phase
#         - primary_endpoint: primary endpoint description
#         - secondary_endpoints: list of secondary endpoints
#         - study_design: study design type
#         - target_enrollment: target number of participants
#         - duration: study duration
#         - sponsor: study sponsor
#         - therapeutic_area: therapeutic area/indication
#         - intervention: intervention/treatment description

#         Protocol text:
#         {protocol_text}

#         Respond with valid JSON only.
#         """
#         content = self._chat_request(
#             "You are an expert clinical research analyst. Extract key information from clinical trial protocols and respond only with valid JSON.",
#             prompt,
#         )
#         return json.loads(content)

#     def suggest_optimizations(self, protocol_text):
#         """Suggest optimizations for clinical trial protocol"""
#         prompt = f"""
#         Analyze the following clinical trial protocol and suggest optimizations.

#         Provide suggestions in the following categories in JSON format:
#         - enrollment_strategies
#         - endpoint_optimization
#         - study_design_improvements
#         - operational_efficiency
#         - regulatory_considerations
#         - patient_experience

#         Protocol text:
#         {protocol_text}

#         Respond with valid JSON only.
#         """
#         content = self._chat_request(
#             "You are an expert clinical trial optimization consultant. Provide specific, actionable recommendations in JSON format.",
#             prompt,
#         )
#         return json.loads(content)

#     def extract_eligibility_criteria(self, protocol_text):
#         """Extract structured eligibility criteria from protocol text"""
#         prompt = f"""
#         Extract all inclusion and exclusion criteria from the following clinical trial protocol.

#         Return JSON with:
#         - inclusion_criteria
#         - exclusion_criteria
#         - age_requirements
#         - gender_requirements
#         - medical_conditions
#         - medications
#         - laboratory_requirements

#         Protocol text:
#         {protocol_text}

#         Each criterion should be a clear standalone statement.
#         Respond with valid JSON only.
#         """
#         content = self._chat_request(
#             "You are an expert clinical research coordinator. Extract eligibility criteria accurately and comprehensively in JSON format.",
#             prompt,
#         )
#         return json.loads(content)

#     def generate_patient_profile(self, filters):
#         """Generate a synthetic patient profile based on filters"""
#         prompt = f"""
#         Generate a realistic synthetic patient profile based on the following criteria:

#         Filters: {json.dumps(filters, indent=2)}

#         Create JSON with:
#         - demographics
#         - medical_history
#         - current_medications
#         - laboratory_values
#         - vital_signs
#         - allergies
#         - social_history
#         - insurance_info
#         - contact_info
#         - emergency_contact

#         Ensure profile is medically consistent and realistic.
#         Respond with valid JSON only.
#         """
#         content = self._chat_request(
#             "You are an expert medical data scientist creating realistic synthetic patient profiles. Ensure all data is medically consistent and follows realistic patterns.",
#             prompt,
#         )
#         return json.loads(content)

import os
import json
from groq import Groq

class GroqClient:
    def __init__(self):
        self.api_key = os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        self.client = Groq(api_key=self.api_key)

    def _chat_request(self, system_content, user_content):
        """Internal helper to send chat request to Groq API"""
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # ✅ Correct model
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content},
            ],
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from Groq API")
        return content.strip()

    def _safe_json(self, content):
        """Try parsing JSON, fallback to raw text"""
        try:
            return json.loads(content)
        except Exception:
            return {"raw_text": content}

    def extract_protocol_info(self, protocol_text):
        prompt = f"""
        Analyze the following clinical trial protocol and extract key information in JSON format.

        Extract the following fields:
        - title
        - phase
        - primary_endpoint
        - secondary_endpoints
        - study_design
        - target_enrollment
        - duration
        - sponsor
        - therapeutic_area
        - intervention

        Protocol text:
        {protocol_text}

        Respond with valid JSON only.
        """
        content = self._chat_request(
            "You are an expert clinical research analyst. Respond only with JSON.",
            prompt,
        )
        return self._safe_json(content)

    def suggest_optimizations(self, protocol_text):
        prompt = f"""
        Analyze the following clinical trial protocol and suggest optimizations in JSON format.

        Categories:
        - enrollment_strategies
        - endpoint_optimization
        - study_design_improvements
        - operational_efficiency
        - regulatory_considerations
        - patient_experience

        Protocol text:
        {protocol_text}

        Respond with valid JSON only.
        """
        content = self._chat_request(
            "You are an expert clinical trial optimization consultant. Respond only with JSON.",
            prompt,
        )
        return self._safe_json(content)

    def extract_eligibility_criteria(self, protocol_text):
        prompt = f"""
        Extract inclusion and exclusion criteria from the protocol.

        Return JSON with:
        - inclusion_criteria
        - exclusion_criteria
        - age_requirements
        - gender_requirements
        - medical_conditions
        - medications
        - laboratory_requirements

        Protocol text:
        {protocol_text}

        Respond with valid JSON only.
        """
        content = self._chat_request(
            "You are an expert clinical research coordinator. Respond only with JSON.",
            prompt,
        )
        return self._safe_json(content)

    def generate_patient_profile(self, filters):
        prompt = f"""
        Generate a synthetic patient profile using these filters:

        {json.dumps(filters, indent=2)}

        Return JSON with:
        - demographics
        - medical_history
        - current_medications
        - laboratory_values
        - vital_signs
        - allergies
        - social_history
        - insurance_info
        - contact_info
        - emergency_contact

        Ensure medical consistency. Respond with valid JSON only.
        """
        content = self._chat_request(
            "You are an expert medical data scientist. Respond only with JSON.",
            prompt,
        )
        return self._safe_json(content)
