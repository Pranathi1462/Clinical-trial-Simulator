"""
eligibility_extractor.py
Turn a parsed protocol dict into an editable form structure for the UI.
"""

from typing import Dict, List


def struct_to_form(parsed_protocol: Dict) -> Dict:
    """
    Convert parsed protocol dict -> simple form dict expected by Streamlit UI.
    Returns keys:
      - age_min, age_max, biomarkers (list), exclusions (list)
    """
    # default values
    age_min = parsed_protocol.get("age_min") or 18
    age_max = parsed_protocol.get("age_max") or 65
    exclusions = parsed_protocol.get("exclusion_criteria", []) or []
    inclusions = parsed_protocol.get("inclusion_criteria", []) or []

    # heuristically extract biomarkers by looking for keywords (very naive)
    biomarkers = []
    biomarker_keywords = ["EBV", "HIV", "HBV", "HCV", "PCR", "CD4", "anti-", "IgG", "IgM"]
    for inc in inclusions:
        for k in biomarker_keywords:
            if k.lower() in inc.lower() and k not in biomarkers:
                biomarkers.append(k)

    return {
        "age_min": int(age_min),
        "age_max": int(age_max),
        "biomarkers": biomarkers,
        "exclusions": exclusions
    }