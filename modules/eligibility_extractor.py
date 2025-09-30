# modules/eligibility_extractor.py

def struct_to_form(parsed):
    """
    Convert parsed dict to a simple editable form structure
    """
    form = {
        "age_min": parsed.get("age_min") or 18,
        "age_max": parsed.get("age_max") or 65,
        "biomarkers": parsed.get("biomarkers") or [],
        "exclusions": parsed.get("exclusions") or []
    }
    return form
