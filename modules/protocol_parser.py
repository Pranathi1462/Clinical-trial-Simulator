import json
from utils.groq_client import GroqClient

class ProtocolParser:
    def __init__(self):
        self.groq_client = GroqClient()
    
    def parse_protocol(self, protocol_text):
        """
        Parse clinical trial protocol text and extract key information with optimization suggestions
        
        Args:
            protocol_text (str): Raw clinical trial protocol text
            
        Returns:
            dict: Contains extracted information and optimization suggestions
        """
        if not protocol_text or not protocol_text.strip():
            raise ValueError("Protocol text cannot be empty")
        
        try:
            # Extract key information
            extracted_info = self.groq_client.extract_protocol_info(protocol_text)
            
            # Get optimization suggestions
            optimizations = self.groq_client.suggest_optimizations(protocol_text)
            
            return {
                "extracted_info": extracted_info,
                "optimizations": optimizations,
                "status": "success",
                "text_length": len(protocol_text),
                "processing_timestamp": self._get_timestamp()
            }
        
        except Exception as e:
            raise Exception(f"Failed to parse protocol: {str(e)}")
    
    def validate_protocol_structure(self, protocol_text):
        """
        Validate that protocol text contains essential sections
        
        Args:
            protocol_text (str): Protocol text to validate
            
        Returns:
            dict: Validation results
        """
        essential_sections = [
            "objective", "endpoint", "inclusion", "exclusion", 
            "design", "population", "intervention", "safety"
        ]
        
        found_sections = []
        missing_sections = []
        
        for section in essential_sections:
            if any(keyword in protocol_text.lower() for keyword in [section, section.replace("_", " ")]):
                found_sections.append(section)
            else:
                missing_sections.append(section)
        
        return {
            "is_valid": len(missing_sections) <= 2,  # Allow up to 2 missing sections
            "found_sections": found_sections,
            "missing_sections": missing_sections,
            "completeness_score": len(found_sections) / len(essential_sections)
        }
    
    def extract_study_phases(self, protocol_text):
        """
        Extract and categorize study phases from protocol text
        
        Args:
            protocol_text (str): Protocol text
            
        Returns:
            dict: Study phase information
        """
        phase_keywords = {
            "phase_1": ["phase i", "phase 1", "first-in-human", "dose escalation"],
            "phase_2": ["phase ii", "phase 2", "proof of concept", "dose finding"],
            "phase_3": ["phase iii", "phase 3", "pivotal", "confirmatory"],
            "phase_4": ["phase iv", "phase 4", "post-marketing", "surveillance"]
        }
        
        detected_phases = []
        for phase, keywords in phase_keywords.items():
            if any(keyword in protocol_text.lower() for keyword in keywords):
                detected_phases.append(phase)
        
        return {
            "detected_phases": detected_phases,
            "primary_phase": detected_phases[0] if detected_phases else "unknown",
            "is_multi_phase": len(detected_phases) > 1
        }
    
    def _get_timestamp(self):
        """Get current timestamp for processing records"""
        from datetime import datetime
        return datetime.now().isoformat()
