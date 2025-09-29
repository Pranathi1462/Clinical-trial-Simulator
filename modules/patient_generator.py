import json
import random
from utils.openai_client import OpenAIClient
from modules.synthea_schema import SyntheaSchema

class PatientGenerator:
    def __init__(self):
        self.openai_client = OpenAIClient()
        self.synthea_schema = SyntheaSchema()
    
    def generate_patients(self, count, filters, output_format="json"):
        """
        Generate synthetic patient profiles based on specified filters
        
        Args:
            count (int): Number of patients to generate
            filters (dict): Demographic and clinical filters
            output_format (str): Output format - 'json', 'csv', or 'synthea compatible'
            
        Returns:
            list: Generated patient profiles
        """
        if count <= 0:
            raise ValueError("Patient count must be greater than 0")
        
        if count > 100:
            raise ValueError("Maximum 100 patients can be generated at once")
        
        patients = []
        
        for i in range(count):
            try:
                # Generate individual patient profile
                patient = self._generate_single_patient(filters)
                
                # Format according to requested output format
                if output_format == "synthea compatible":
                    patient = self.synthea_schema.convert_to_synthea_format(patient)
                elif output_format == "csv":
                    patient = self._flatten_for_csv(patient)
                
                patients.append(patient)
                
            except Exception as e:
                print(f"Warning: Failed to generate patient {i+1}: {str(e)}")
                continue
        
        if not patients:
            raise Exception("Failed to generate any patients. Please check your filters and try again.")
        
        return patients
    
    def _generate_single_patient(self, filters):
        """
        Generate a single patient profile using AI
        
        Args:
            filters (dict): Patient generation filters
            
        Returns:
            dict: Patient profile
        """
        # Validate filters
        validated_filters = self._validate_filters(filters)
        
        # Generate patient using OpenAI
        patient_profile = self.openai_client.generate_patient_profile(validated_filters)
        
        # Add generation metadata
        patient_profile["generation_metadata"] = {
            "generated_at": self._get_timestamp(),
            "filters_applied": validated_filters,
            "generator_version": "1.0"
        }
        
        return patient_profile
    
    def _validate_filters(self, filters):
        """
        Validate and standardize patient generation filters
        
        Args:
            filters (dict): Raw filters
            
        Returns:
            dict: Validated filters
        """
        validated = {
            "age_range": filters.get("age_range", [18, 80]),
            "gender": filters.get("gender", ["male", "female"]),
            "ethnicity": filters.get("ethnicity", ["white", "black", "hispanic", "asian"]),
            "conditions": filters.get("conditions", []),
            "exclusion_conditions": filters.get("exclusion_conditions", []),
            "medications": filters.get("medications", []),
            "exclusion_medications": filters.get("exclusion_medications", [])
        }
        
        # Validate age range
        if not isinstance(validated["age_range"], (list, tuple)) or len(validated["age_range"]) != 2:
            validated["age_range"] = [18, 80]
        
        # Ensure minimum age range
        if validated["age_range"][1] - validated["age_range"][0] < 1:
            validated["age_range"] = [18, 80]
        
        # Validate gender options
        valid_genders = ["male", "female", "other"]
        validated["gender"] = [g for g in validated["gender"] if g.lower() in valid_genders]
        if not validated["gender"]:
            validated["gender"] = ["male", "female"]
        
        return validated
    
    def _flatten_for_csv(self, patient):
        """
        Flatten nested patient data for CSV output
        
        Args:
            patient (dict): Patient profile
            
        Returns:
            dict: Flattened patient data
        """
        flattened = {}
        
        # Basic demographics
        demographics = patient.get("demographics", {})
        flattened.update({
            "age": demographics.get("age"),
            "gender": demographics.get("gender"),
            "ethnicity": demographics.get("ethnicity"),
            "weight_kg": demographics.get("weight"),
            "height_cm": demographics.get("height"),
            "bmi": demographics.get("BMI")
        })
        
        # Medical history
        medical_history = patient.get("medical_history", {})
        flattened["conditions"] = "; ".join(medical_history.get("conditions", []))
        
        # Medications
        medications = patient.get("current_medications", [])
        flattened["medications"] = "; ".join([f"{med.get('name')} {med.get('dosage', '')}" for med in medications])
        
        # Vital signs
        vitals = patient.get("vital_signs", {})
        flattened.update({
            "blood_pressure": vitals.get("blood_pressure"),
            "heart_rate": vitals.get("heart_rate"),
            "temperature": vitals.get("temperature"),
            "respiratory_rate": vitals.get("respiratory_rate")
        })
        
        # Contact info
        contact = patient.get("contact_info", {})
        flattened.update({
            "first_name": contact.get("first_name"),
            "last_name": contact.get("last_name"),
            "email": contact.get("email"),
            "phone": contact.get("phone"),
            "address": contact.get("address")
        })
        
        return flattened
    
    def generate_cohort_statistics(self, patients):
        """
        Generate statistical summary of patient cohort
        
        Args:
            patients (list): List of patient profiles
            
        Returns:
            dict: Cohort statistics
        """
        if not patients:
            return {"error": "No patients provided"}
        
        stats = {
            "total_patients": len(patients),
            "demographics": self._analyze_demographics(patients),
            "medical_conditions": self._analyze_conditions(patients),
            "medications": self._analyze_medications(patients)
        }
        
        return stats
    
    def _analyze_demographics(self, patients):
        """Analyze demographic distribution in patient cohort"""
        ages = []
        genders = {}
        ethnicities = {}
        
        for patient in patients:
            demographics = patient.get("demographics", {})
            
            # Age analysis
            age = demographics.get("age")
            if age:
                ages.append(age)
            
            # Gender distribution
            gender = demographics.get("gender")
            if gender:
                genders[gender] = genders.get(gender, 0) + 1
            
            # Ethnicity distribution
            ethnicity = demographics.get("ethnicity")
            if ethnicity:
                ethnicities[ethnicity] = ethnicities.get(ethnicity, 0) + 1
        
        return {
            "age_stats": {
                "mean": sum(ages) / len(ages) if ages else 0,
                "min": min(ages) if ages else 0,
                "max": max(ages) if ages else 0
            },
            "gender_distribution": genders,
            "ethnicity_distribution": ethnicities
        }
    
    def _analyze_conditions(self, patients):
        """Analyze medical conditions distribution"""
        conditions = {}
        
        for patient in patients:
            medical_history = patient.get("medical_history", {})
            patient_conditions = medical_history.get("conditions", [])
            
            for condition in patient_conditions:
                conditions[condition] = conditions.get(condition, 0) + 1
        
        return conditions
    
    def _analyze_medications(self, patients):
        """Analyze medication distribution"""
        medications = {}
        
        for patient in patients:
            patient_medications = patient.get("current_medications", [])
            
            for med in patient_medications:
                med_name = med.get("name") if isinstance(med, dict) else str(med)
                medications[med_name] = medications.get(med_name, 0) + 1
        
        return medications
    
    def _get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
