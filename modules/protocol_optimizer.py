# modules/protocol_optimizer.py

import os
import json
import time
import requests
import re
from typing import List, Dict, Optional

# Try to import Groq; fallback if unavailable
try:
    from groq import Groq
    _HAS_GROQ = True
except ImportError:
    _HAS_GROQ = False

# Force-set your Groq API key here (optional, can also set in environment)
# os.environ["GROQ_API_KEY"] = "YOUR_GROQ_API_KEY"

# ------------------------------
# ClinicalTrials.gov helper
# ------------------------------
def fetch_clinicaltrials_examples(condition: str, max_results: int = 3) -> List[Dict]:
    """
    Fetch simplified trial records to guide protocol generation.
    """
    try:
        base = "https://clinicaltrials.gov/api/query/full_studies"
        params = {
            "expr": condition,
            "min_rnk": 1,
            "max_rnk": max_results,
            "fmt": "json"
        }
        r = requests.get(base, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        studies = []
        full_studies = data.get("FullStudiesResponse", {}).get("FullStudies", [])
        for item in full_studies:
            study = item.get("Study", {})
            protocol = {
                "nct_id": study.get("ProtocolSection", {}).get("IdentificationModule", {}).get("NCTId", ""),
                "brief_title": study.get("ProtocolSection", {}).get("IdentificationModule", {}).get("BriefTitle", ""),
                "study_type": study.get("ProtocolSection", {}).get("DesignModule", {}).get("StudyType", ""),
                "phase": study.get("ProtocolSection", {}).get("DesignModule", {}).get("PhaseList", {}).get("Phase", []),
                "enrollment": study.get("ProtocolSection", {}).get("DesignModule", {}).get("EnrollmentInfo", {}).get("EnrollmentCount", ""),
                "primary_outcome": study.get("ProtocolSection", {}).get("OutcomesModule", {}).get("PrimaryOutcomeList", {}).get("PrimaryOutcome", []),
            }
            studies.append(protocol)
        return studies
    except Exception:
        return []

# ------------------------------
# Safe JSON parsing
# ------------------------------
def safe_json_load(text: str):
    """Extract first JSON array and parse."""
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    return json.loads(text)

# ------------------------------
# Mandatory protocol sections
# ------------------------------
MANDATORY_SECTIONS = {
    "SECTION 1": ["protocol_title", "protocol_id", "version", "date", "sponsor", "principal_investigator", "clinicaltrials_gov_id", "ind_ide_number", "protocol_synopsis"],
    "SECTION 2": ["disease_overview", "investigational_product_background", "study_rationale"],
    "SECTION 3": ["primary_objectives", "primary_endpoints", "secondary_objectives", "secondary_endpoints", "safety_objectives", "safety_endpoints"],
    "SECTION 4": ["overall_design", "randomization", "blinding", "control", "treatment_arms"],
    "SECTION 5": ["target_population", "sample_size", "inclusion_criteria", "exclusion_criteria"]
}

# ------------------------------
# Protocol Optimizer
# ------------------------------
class ProtocolOptimizer:
    def __init__(self, api_key: Optional[str] = None):
        self.client = None
        if _HAS_GROQ:
            key = api_key or os.getenv("GROQ_API_KEY")
            if not key:
                raise ValueError("GROQ_API_KEY not set in environment")
            self.client = Groq(api_key=key)

    # --------------------------
    # Call Groq or fallback
    # --------------------------
    def _call_groq(self, prompt: str, model: str = "llama-3.3-70b-versatile", max_tokens: int = 4000) -> str:
        if not self.client:
            # fallback: return blank protocol JSON
            blank_protocols = []
            for _ in range(1):
                proto = {sec: {field: "" if isinstance(field, str) else [] for field in fields} for sec, fields in MANDATORY_SECTIONS.items()}
                proto["schema_version"] = "1.0"
                proto["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                blank_protocols.append(proto)
            return json.dumps(blank_protocols)
        
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert clinical trial designer. Produce only valid JSON. Fill all mandatory sections. Leave empty if unknown."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.3
        )
        return response.choices[0].message.content

    # --------------------------
    # Build prompt
    # --------------------------
    def _make_prompt(self, pi_text: str, examples: Optional[List[Dict]], n_options: int) -> str:
        lines = [
            "You are an expert clinical trial protocol writer.",
            f"PI input: \"\"\"\n{pi_text}\n\"\"\"",
            f"Produce exactly {n_options} fully structured protocols as a JSON array.",
            "Fill all mandatory sections. Leave blank if unknown."
        ]
        for sec, fields in MANDATORY_SECTIONS.items():
            lines.append(f"- {sec}: {fields}")
        if examples:
            lines.append("Example trials from ClinicalTrials.gov (reference only):")
            for ex in examples:
                lines.append(json.dumps(ex))
        return "\n".join(lines)

    # --------------------------
    # Main function
    # --------------------------
    def generate_full_protocol(self, pi_text: str, n_options: int = 1, include_references: bool = True) -> List[Dict]:
        examples = []
        if include_references:
            condition = " ".join(pi_text.split()[:6])
            examples = fetch_clinicaltrials_examples(condition, max_results=2)

        prompt = self._make_prompt(pi_text, examples, n_options)

        last_raw = ""
        for attempt in range(2):
            try:
                last_raw = self._call_groq(prompt)
                protocols = safe_json_load(last_raw)
                # Limit to requested number of drafts
                protocols = protocols[:n_options]
                # Add metadata and ensure all mandatory sections exist
                for p in protocols:
                    p.setdefault("schema_version", "1.0")
                    p.setdefault("generated_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
                    for sec, fields in MANDATORY_SECTIONS.items():
                        if sec not in p:
                            p[sec] = {field: "" if isinstance(field, str) else [] for field in fields}
                return protocols
            except (json.JSONDecodeError, ValueError):
                # Retry once
                prompt2 = "Your previous response was invalid JSON. Return only a JSON array of protocols with all mandatory sections."
                last_raw = self._call_groq(prompt2 + "\nOriginal content:\n" + last_raw)
                try:
                    protocols = safe_json_load(last_raw)
                    protocols = protocols[:n_options]
                    for p in protocols:
                        p.setdefault("schema_version", "1.0")
                        p.setdefault("generated_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
                        for sec, fields in MANDATORY_SECTIONS.items():
                            if sec not in p:
                                p[sec] = {field: "" if isinstance(field, str) else [] for field in fields}
                    return protocols
                except Exception:
                    if attempt == 1:
                        raise RuntimeError(f"Failed to generate protocols. Raw output:\n{last_raw}")

        raise RuntimeError("Unable to generate protocols")