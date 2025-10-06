"""
clinicaltrials_api.py
Simple wrapper for ClinicalTrials.gov API to fetch trial metadata (FullStudies).
"""

import requests
from typing import List, Dict, Optional


CTG_BASE = "https://clinicaltrials.gov/api/query/full_studies"


def fetch_trials_by_condition(condition: str, max_results: int = 10) -> List[Dict]:
    """
    Query ClinicalTrials.gov FullStudies API for a condition (free text).
    Returns a list of simplified trial dicts (nct_id, title, phase, enrollment, brief_summary).
    """
    params = {"expr": condition, "min_rnk": 1, "max_rnk": max_results, "fmt": "json"}
    try:
        r = requests.get(CTG_BASE, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        studies = data.get("FullStudiesResponse", {}).get("FullStudies", [])
        out = []
        for item in studies:
            study = item.get("Study", {})
            proto = study.get("ProtocolSection", {})
            ident = proto.get("IdentificationModule", {})
            design = proto.get("DesignModule", {})
            desc = proto.get("DescriptionModule", {})
            outcomes = proto.get("OutcomesModule", {})
            out.append({
                "nct_id": ident.get("NCTId"),
                "brief_title": ident.get("BriefTitle"),
                "official_title": ident.get("OfficialTitle"),
                "study_type": design.get("StudyType"),
                "phase": design.get("PhaseList", {}).get("Phase"),
                "enrollment": design.get("EnrollmentInfo", {}).get("EnrollmentCount"),
                "primary_outcomes": outcomes.get("PrimaryOutcomeList", {}).get("PrimaryOutcome"),
                "brief_summary": desc.get("BriefSummary", {}).get("BriefSummary"),
            })
        return out
    except Exception:
        return []


def fetch_trial_by_nct(nct_id: str) -> Optional[Dict]:
    """Fetch single trial full study by NCT ID (or return None)."""
    try:
        params = {"expr": nct_id, "min_rnk": 1, "max_rnk": 1, "fmt": "json"}
        r = requests.get(CTG_BASE, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        studies = data.get("FullStudiesResponse", {}).get("FullStudies", [])
        if not studies:
            return None
        study = studies[0].get("Study", {})
        # return the raw ProtocolSection for maximal flexibility
        return study.get("ProtocolSection", {})
    except Exception:
        return None