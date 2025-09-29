import re
import json
from utils.openai_client import OpenAIClient

class EligibilityExtractor:
    def __init__(self):
        self.openai_client = OpenAIClient()
    
    def extract_criteria(self, protocol_text):
        """
        Extract structured eligibility criteria from clinical trial protocol text
        
        Args:
            protocol_text (str): Clinical trial protocol text
            
        Returns:
            dict: Structured eligibility criteria
        """
        if not protocol_text or not protocol_text.strip():
            raise ValueError("Protocol text cannot be empty")
        
        try:
            # Use AI to extract structured criteria
            ai_extracted = self.openai_client.extract_eligibility_criteria(protocol_text)
            
            # Apply rule-based validation and enhancement
            enhanced_criteria = self._enhance_with_rules(protocol_text, ai_extracted)
            
            # Structure the final output
            structured_criteria = {
                "inclusion_criteria": enhanced_criteria.get("inclusion_criteria", []),
                "exclusion_criteria": enhanced_criteria.get("exclusion_criteria", []),
                "age_requirements": enhanced_criteria.get("age_requirements", {}),
                "gender_requirements": enhanced_criteria.get("gender_requirements", {}),
                "medical_conditions": enhanced_criteria.get("medical_conditions", {}),
                "medications": enhanced_criteria.get("medications", {}),
                "laboratory_requirements": enhanced_criteria.get("laboratory_requirements", {}),
                "extraction_metadata": {
                    "extracted_at": self._get_timestamp(),
                    "text_length": len(protocol_text),
                    "ai_confidence": self._calculate_confidence(enhanced_criteria),
                    "extraction_method": "ai_enhanced_with_rules"
                }
            }
            
            return structured_criteria
            
        except Exception as e:
            raise Exception(f"Failed to extract eligibility criteria: {str(e)}")
    
    def _enhance_with_rules(self, protocol_text, ai_extracted):
        """
        Enhance AI-extracted criteria with rule-based improvements
        
        Args:
            protocol_text (str): Original protocol text
            ai_extracted (dict): AI-extracted criteria
            
        Returns:
            dict: Enhanced criteria
        """
        enhanced = ai_extracted.copy()
        
        # Apply rule-based enhancements
        enhanced.update(self._extract_age_patterns(protocol_text))
        enhanced.update(self._extract_lab_value_patterns(protocol_text))
        enhanced.update(self._extract_medication_patterns(protocol_text))
        
        # Validate and clean criteria
        enhanced["inclusion_criteria"] = self._clean_criteria_list(enhanced.get("inclusion_criteria", []))
        enhanced["exclusion_criteria"] = self._clean_criteria_list(enhanced.get("exclusion_criteria", []))
        
        return enhanced
    
    def _extract_age_patterns(self, text):
        """Extract age-related patterns using regex"""
        age_patterns = {
            "minimum_age": r"(?:age|aged?)\s*(?:≥|>=|greater than or equal to|at least)\s*(\d+)",
            "maximum_age": r"(?:age|aged?)\s*(?:≤|<=|less than or equal to|up to|maximum)\s*(\d+)",
            "age_range": r"(?:age|aged?)\s*(?:between\s*)?(\d+)\s*(?:to|-|and)\s*(\d+)"
        }
        
        age_requirements = {}
        text_lower = text.lower()
        
        for pattern_name, pattern in age_patterns.items():
            matches = re.findall(pattern, text_lower)
            if matches:
                if pattern_name == "age_range":
                    age_requirements["minimum_age"] = int(matches[0][0])
                    age_requirements["maximum_age"] = int(matches[0][1])
                else:
                    age_requirements[pattern_name] = int(matches[0])
        
        return {"age_requirements": age_requirements}
    
    def _extract_lab_value_patterns(self, text):
        """Extract laboratory value requirements using regex"""
        lab_patterns = {
            "hemoglobin": r"hemoglobin\s*(?:≥|>=|>)\s*([\d.]+)",
            "creatinine": r"creatinine\s*(?:≤|<=|<)\s*([\d.]+)",
            "platelets": r"platelets?\s*(?:≥|>=|>)\s*([\d,]+)",
            "white_blood_cells": r"(?:wbc|white blood cells?)\s*(?:≥|>=|>)\s*([\d,]+)",
            "liver_enzymes": r"(?:alt|ast|liver enzymes?)\s*(?:≤|<=|<)\s*([\d.]+)"
        }
        
        lab_requirements = {}
        text_lower = text.lower()
        
        for lab_name, pattern in lab_patterns.items():
            matches = re.findall(pattern, text_lower)
            if matches:
                lab_requirements[lab_name] = matches[0].replace(",", "")
        
        return {"laboratory_requirements": lab_requirements}
    
    def _extract_medication_patterns(self, text):
        """Extract medication-related requirements"""
        medication_keywords = {
            "required": [
                "must be on", "requires", "receiving", "taking", 
                "stable dose", "established therapy"
            ],
            "prohibited": [
                "cannot take", "must not", "prohibited", "excluded",
                "contraindicated", "forbidden"
            ]
        }
        
        medications = {"required": [], "prohibited": []}
        text_lower = text.lower()
        
        # Look for common medication patterns
        med_patterns = [
            r"(\w+(?:\s+\w+)*)\s*(?:therapy|treatment|medication)",
            r"(?:receiving|taking|on)\s+(\w+(?:\s+\w+)*)",
            r"stable\s+(?:dose\s+of\s+)?(\w+(?:\s+\w+)*)"
        ]
        
        for pattern in med_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                if any(keyword in text_lower for keyword in medication_keywords["required"]):
                    medications["required"].append(match.strip())
                elif any(keyword in text_lower for keyword in medication_keywords["prohibited"]):
                    medications["prohibited"].append(match.strip())
        
        return {"medications": medications}
    
    def _clean_criteria_list(self, criteria_list):
        """Clean and standardize criteria list"""
        if not isinstance(criteria_list, list):
            return []
        
        cleaned = []
        for criterion in criteria_list:
            if isinstance(criterion, str) and criterion.strip():
                # Remove extra whitespace and normalize
                clean_criterion = re.sub(r'\s+', ' ', criterion.strip())
                # Ensure proper capitalization
                clean_criterion = clean_criterion[0].upper() + clean_criterion[1:] if clean_criterion else ""
                if clean_criterion and clean_criterion not in cleaned:
                    cleaned.append(clean_criterion)
        
        return cleaned
    
    def _calculate_confidence(self, criteria):
        """Calculate extraction confidence score"""
        total_criteria = 0
        filled_criteria = 0
        
        for key, value in criteria.items():
            if key in ["inclusion_criteria", "exclusion_criteria"]:
                total_criteria += 1
                if isinstance(value, list) and value:
                    filled_criteria += 1
            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    total_criteria += 1
                    if sub_value:
                        filled_criteria += 1
        
        return filled_criteria / total_criteria if total_criteria > 0 else 0.0
    
    def validate_criteria_completeness(self, criteria):
        """
        Validate completeness of extracted criteria
        
        Args:
            criteria (dict): Extracted criteria
            
        Returns:
            dict: Validation results
        """
        validation = {
            "is_complete": True,
            "missing_sections": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Check for essential sections
        essential_sections = ["inclusion_criteria", "exclusion_criteria"]
        for section in essential_sections:
            if not criteria.get(section):
                validation["missing_sections"].append(section)
                validation["is_complete"] = False
        
        # Check for age requirements
        if not criteria.get("age_requirements"):
            validation["warnings"].append("No age requirements found")
            validation["recommendations"].append("Consider adding age restrictions")
        
        # Check for medical conditions
        if not criteria.get("medical_conditions"):
            validation["warnings"].append("No specific medical condition requirements found")
        
        return validation
    
    def export_criteria_to_standard_format(self, criteria, format_type="ich_gcp"):
        """
        Export criteria to standardized clinical trial formats
        
        Args:
            criteria (dict): Extracted criteria
            format_type (str): Target format ('ich_gcp', 'fda', 'ema')
            
        Returns:
            dict: Formatted criteria
        """
        if format_type == "ich_gcp":
            return self._format_ich_gcp(criteria)
        elif format_type == "fda":
            return self._format_fda(criteria)
        elif format_type == "ema":
            return self._format_ema(criteria)
        else:
            raise ValueError(f"Unsupported format type: {format_type}")
    
    def _format_ich_gcp(self, criteria):
        """Format criteria according to ICH-GCP guidelines"""
        formatted = {
            "study_population": {
                "inclusion_criteria": criteria.get("inclusion_criteria", []),
                "exclusion_criteria": criteria.get("exclusion_criteria", [])
            },
            "demographic_requirements": {
                "age": criteria.get("age_requirements", {}),
                "gender": criteria.get("gender_requirements", {})
            },
            "medical_requirements": {
                "conditions": criteria.get("medical_conditions", {}),
                "medications": criteria.get("medications", {}),
                "laboratory_values": criteria.get("laboratory_requirements", {})
            }
        }
        return formatted
    
    def _format_fda(self, criteria):
        """Format criteria according to FDA guidelines"""
        # Similar to ICH-GCP but with FDA-specific structure
        return self._format_ich_gcp(criteria)
    
    def _format_ema(self, criteria):
        """Format criteria according to EMA guidelines"""
        # Similar to ICH-GCP but with EMA-specific structure
        return self._format_ich_gcp(criteria)
    
    def _get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
