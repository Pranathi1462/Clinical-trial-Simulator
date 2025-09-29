import json
import uuid
from datetime import datetime, timedelta
import random

class SyntheaSchema:
    """
    Schema converter for Synthea-compatible patient data format
    Based on FHIR R4 patient resource structure used by Synthea
    """
    
    def __init__(self):
        self.resource_type = "Patient"
        self.fhir_version = "4.0.1"
    
    def convert_to_synthea_format(self, patient_profile):
        """
        Convert patient profile to Synthea-compatible FHIR format
        
        Args:
            patient_profile (dict): Patient profile from generator
            
        Returns:
            dict: Synthea-compatible patient resource
        """
        if not patient_profile:
            raise ValueError("Patient profile is required")
        
        demographics = patient_profile.get("demographics", {})
        contact_info = patient_profile.get("contact_info", {})
        
        # Generate unique identifiers
        patient_id = str(uuid.uuid4())
        
        synthea_patient = {
            "resourceType": self.resource_type,
            "id": patient_id,
            "meta": {
                "versionId": "1",
                "lastUpdated": datetime.now().isoformat() + "Z",
                "profile": [
                    "http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"
                ]
            },
            "identifier": self._generate_identifiers(),
            "active": True,
            "name": self._convert_name(contact_info),
            "telecom": self._convert_telecom(contact_info),
            "gender": self._convert_gender(demographics.get("gender")),
            "birthDate": self._calculate_birth_date(demographics.get("age")),
            "address": self._convert_address(contact_info),
            "maritalStatus": self._generate_marital_status(),
            "multipleBirthBoolean": False,
            "communication": self._generate_communication(),
            "extension": self._generate_extensions(demographics, patient_profile)
        }
        
        # Add optional fields if available
        if demographics.get("ethnicity"):
            synthea_patient["extension"].extend(self._generate_ethnicity_extension(demographics["ethnicity"]))
        
        if demographics.get("race"):
            synthea_patient["extension"].extend(self._generate_race_extension(demographics["race"]))
        
        return synthea_patient
    
    def _generate_identifiers(self):
        """Generate FHIR identifiers for the patient"""
        return [
            {
                "use": "usual",
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "MR",
                            "display": "Medical Record Number"
                        }
                    ],
                    "text": "Medical Record Number"
                },
                "system": "http://hospital.smarthealthit.org",
                "value": f"MRN{random.randint(100000, 999999)}"
            },
            {
                "use": "usual",
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "SS",
                            "display": "Social Security Number"
                        }
                    ],
                    "text": "Social Security Number"
                },
                "system": "http://hl7.org/fhir/sid/us-ssn",
                "value": f"{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"
            }
        ]
    
    def _convert_name(self, contact_info):
        """Convert name information to FHIR format"""
        first_name = contact_info.get("first_name", "John")
        last_name = contact_info.get("last_name", "Doe")
        
        return [
            {
                "use": "official",
                "family": last_name,
                "given": [first_name]
            }
        ]
    
    def _convert_telecom(self, contact_info):
        """Convert contact information to FHIR telecom format"""
        telecom = []
        
        if contact_info.get("phone"):
            telecom.append({
                "system": "phone",
                "value": contact_info["phone"],
                "use": "home"
            })
        
        if contact_info.get("email"):
            telecom.append({
                "system": "email",
                "value": contact_info["email"],
                "use": "home"
            })
        
        return telecom
    
    def _convert_gender(self, gender):
        """Convert gender to FHIR administrative gender"""
        gender_mapping = {
            "male": "male",
            "female": "female",
            "other": "other",
            "unknown": "unknown"
        }
        
        return gender_mapping.get(str(gender).lower(), "unknown")
    
    def _calculate_birth_date(self, age):
        """Calculate birth date from age"""
        if not age:
            age = 35  # Default age
        
        try:
            age = int(age)
        except (ValueError, TypeError):
            age = 35
        
        # Calculate approximate birth date
        today = datetime.now()
        birth_year = today.year - age
        
        # Random month and day
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)  # Safe day for all months
        
        birth_date = datetime(birth_year, birth_month, birth_day)
        return birth_date.strftime("%Y-%m-%d")
    
    def _convert_address(self, contact_info):
        """Convert address to FHIR format"""
        address_text = contact_info.get("address", "123 Main St, Anytown, ST 12345")
        
        # Simple parsing of address
        parts = address_text.split(",")
        line = parts[0].strip() if parts else "123 Main St"
        city = parts[1].strip() if len(parts) > 1 else "Anytown"
        
        # Extract state and postal code from last part
        if len(parts) > 2:
            state_zip = parts[2].strip().split()
            state = state_zip[0] if state_zip else "ST"
            postal_code = state_zip[1] if len(state_zip) > 1 else "12345"
        else:
            state = "ST"
            postal_code = "12345"
        
        return [
            {
                "use": "home",
                "type": "both",
                "line": [line],
                "city": city,
                "state": state,
                "postalCode": postal_code,
                "country": "US"
            }
        ]
    
    def _generate_marital_status(self):
        """Generate random marital status"""
        statuses = [
            {"code": "M", "display": "Married"},
            {"code": "S", "display": "Never Married"},
            {"code": "D", "display": "Divorced"},
            {"code": "W", "display": "Widowed"}
        ]
        
        status = random.choice(statuses)
        
        return {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
                    "code": status["code"],
                    "display": status["display"]
                }
            ],
            "text": status["display"]
        }
    
    def _generate_communication(self):
        """Generate communication preferences"""
        return [
            {
                "language": {
                    "coding": [
                        {
                            "system": "urn:ietf:bcp:47",
                            "code": "en-US",
                            "display": "English (United States)"
                        }
                    ],
                    "text": "English"
                },
                "preferred": True
            }
        ]
    
    def _generate_extensions(self, demographics, patient_profile):
        """Generate FHIR extensions for additional data"""
        extensions = []
        
        # Birthsex extension
        birth_sex = demographics.get("gender", "unknown")
        if birth_sex in ["male", "female"]:
            extensions.append({
                "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-birthsex",
                "valueCode": birth_sex[0].upper()  # M or F
            })
        
        return extensions
    
    def _generate_ethnicity_extension(self, ethnicity):
        """Generate ethnicity extension"""
        ethnicity_mapping = {
            "hispanic": {
                "code": "2135-2",
                "display": "Hispanic or Latino"
            },
            "non-hispanic": {
                "code": "2186-5",
                "display": "Not Hispanic or Latino"
            }
        }
        
        eth_data = ethnicity_mapping.get(ethnicity.lower(), ethnicity_mapping["non-hispanic"])
        
        return [
            {
                "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity",
                "extension": [
                    {
                        "url": "ombCategory",
                        "valueCoding": {
                            "system": "urn:oid:2.16.840.1.113883.6.238",
                            "code": eth_data["code"],
                            "display": eth_data["display"]
                        }
                    },
                    {
                        "url": "text",
                        "valueString": eth_data["display"]
                    }
                ]
            }
        ]
    
    def _generate_race_extension(self, race):
        """Generate race extension"""
        race_mapping = {
            "white": {
                "code": "2106-3",
                "display": "White"
            },
            "black": {
                "code": "2054-5",
                "display": "Black or African American"
            },
            "asian": {
                "code": "2028-9",
                "display": "Asian"
            },
            "native": {
                "code": "1002-5",
                "display": "American Indian or Alaska Native"
            },
            "pacific": {
                "code": "2076-8",
                "display": "Native Hawaiian or Other Pacific Islander"
            }
        }
        
        race_data = race_mapping.get(race.lower(), race_mapping["white"])
        
        return [
            {
                "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race",
                "extension": [
                    {
                        "url": "ombCategory",
                        "valueCoding": {
                            "system": "urn:oid:2.16.840.1.113883.6.238",
                            "code": race_data["code"],
                            "display": race_data["display"]
                        }
                    },
                    {
                        "url": "text",
                        "valueString": race_data["display"]
                    }
                ]
            }
        ]
    
    def create_observation_resource(self, patient_id, observation_data):
        """
        Create FHIR Observation resource for lab values or vital signs
        
        Args:
            patient_id (str): Patient identifier
            observation_data (dict): Observation data
            
        Returns:
            dict: FHIR Observation resource
        """
        observation_id = str(uuid.uuid4())
        
        return {
            "resourceType": "Observation",
            "id": observation_id,
            "meta": {
                "versionId": "1",
                "lastUpdated": datetime.now().isoformat() + "Z"
            },
            "status": "final",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "vital-signs",
                            "display": "Vital Signs"
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": observation_data.get("loinc_code", "29463-7"),
                        "display": observation_data.get("display", "Body weight")
                    }
                ]
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "effectiveDateTime": datetime.now().isoformat() + "Z",
            "valueQuantity": {
                "value": observation_data.get("value"),
                "unit": observation_data.get("unit"),
                "system": "http://unitsofmeasure.org",
                "code": observation_data.get("unit_code")
            }
        }
    
    def create_condition_resource(self, patient_id, condition_data):
        """
        Create FHIR Condition resource for medical conditions
        
        Args:
            patient_id (str): Patient identifier
            condition_data (dict): Condition data
            
        Returns:
            dict: FHIR Condition resource
        """
        condition_id = str(uuid.uuid4())
        
        return {
            "resourceType": "Condition",
            "id": condition_id,
            "meta": {
                "versionId": "1",
                "lastUpdated": datetime.now().isoformat() + "Z"
            },
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": "active"
                    }
                ]
            },
            "verificationStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                        "code": "confirmed"
                    }
                ]
            },
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                            "code": "encounter-diagnosis",
                            "display": "Encounter Diagnosis"
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": condition_data.get("snomed_code", "44054006"),
                        "display": condition_data.get("display", "Diabetes mellitus")
                    }
                ],
                "text": condition_data.get("text", condition_data.get("display", "Medical condition"))
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "onsetDateTime": condition_data.get("onset_date", datetime.now().isoformat() + "Z")
        }
    
    def validate_synthea_format(self, patient_resource):
        """
        Validate that patient resource conforms to Synthea format
        
        Args:
            patient_resource (dict): Patient resource to validate
            
        Returns:
            dict: Validation results
        """
        validation = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check required fields
        required_fields = ["resourceType", "id", "name", "gender", "birthDate"]
        for field in required_fields:
            if field not in patient_resource:
                validation["errors"].append(f"Missing required field: {field}")
                validation["is_valid"] = False
        
        # Check resource type
        if patient_resource.get("resourceType") != "Patient":
            validation["errors"].append("Resource type must be 'Patient'")
            validation["is_valid"] = False
        
        # Check name format
        if "name" in patient_resource:
            if not isinstance(patient_resource["name"], list):
                validation["errors"].append("Name must be an array")
                validation["is_valid"] = False
        
        # Check gender values
        valid_genders = ["male", "female", "other", "unknown"]
        if patient_resource.get("gender") not in valid_genders:
            validation["warnings"].append(f"Gender should be one of: {valid_genders}")
        
        return validation
