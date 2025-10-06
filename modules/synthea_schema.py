"""
synthea_schema.py
Simple helper mapping to Synthea-like patient fields for later export.
This is a placeholder mapping — extend to match your Synthea templates.
"""

def map_patient_to_synthea(patient_row: dict) -> dict:
    """
    Convert a synthetic patient dict -> a minimal Synthea-like dict.
    """
    return {
        "id": patient_row.get("patient_id"),
        "name": {
            "first": patient_row.get("first_name"),
            "last": patient_row.get("last_name"),
        },
        "demographics": {
            "age": patient_row.get("age"),
            "sex": patient_row.get("sex"),
            "bmi": patient_row.get("bmi"),
        },
        "labs": {
            "ANC": patient_row.get("ANC"),
            "Platelets": patient_row.get("Platelets"),
            "Hemoglobin": patient_row.get("Hemoglobin"),
        },
        "biomarkers": {k: v for k, v in patient_row.items() if k.upper().endswith("_status") or k in ["EBV_status"]},
    }