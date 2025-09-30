# modules/synthea_schema.py

"""
This module defines the schema (structure) for synthetic patients.
It provides a baseline patient template that can be expanded with
age, gender, conditions, treatments, etc.
"""

# A simple patient schema dictionary
PATIENT_SCHEMA = {
    "id": None,                # unique patient ID
    "age": None,               # integer (years)
    "sex": None,               # "M" or "F"
    "condition": None,         # primary condition (e.g., Multiple Sclerosis)
    "inclusion_criteria": [],  # list of criteria met
    "exclusion_criteria": [],  # list of criteria failed
    "treatment": None,         # assigned treatment arm (if applicable)
    "outcome": None            # placeholder for outcome simulation
}

def create_empty_patient(patient_id: int):
    """
    Create a new patient with default schema.
    """
    schema = PATIENT_SCHEMA.copy()
    schema["id"] = patient_id
    return schema
