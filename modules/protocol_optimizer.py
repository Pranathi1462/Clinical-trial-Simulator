# modules/protocol_designer.py
"""
Protocol Designer / Optimizer module
- generate_full_protocol(pi_text, n_options=1, include_references=True)
  returns: list of structured protocol dicts (length = n_options)

Requirements:
  - Set environment variable OPENAI_API_KEY or assign openai.api_key before calling
  - Optionally uses ClinicalTrials.gov public API to sample similar trial records to ground the model
"""

import os
import json
import time
import requests
from typing import List, Dict, Optional

# pip install openai
import openai

# Configure your OpenAI key in environment or set below
# openai.api_key = os.getenv("OPENAI_API_KEY")  # preferred

# ClinicalTrials.gov API helper (public)
def fetch_clinicaltrials_examples(condition: str, max_results: int = 3) -> List[Dict]:
    """
    Query ClinicalTrials.gov API for trials matching `condition`.
    Returns a small list of simplified trial records to include as examples for the LLM.
    If the API fails or is blocked, returns [] and we proceed without examples.
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
                "nct_id": study.get("ProtocolSection", {}).get("IdentificationModule", {}).get("NCTId"),
                "brief_title": study.get("ProtocolSection", {}).get("IdentificationModule", {}).get("BriefTitle"),
                "study_type": study.get("ProtocolSection", {}).get("DesignModule", {}).get("StudyType"),
                "phase": study.get("ProtocolSection", {}).get("DesignModule", {}).get("PhaseList", {}).get("Phase", []),
                "enrollment": study.get("ProtocolSection", {}).get("DesignModule", {}).get("EnrollmentInfo", {}).get("EnrollmentCount"),
                "primary_outcome": study.get("ProtocolSection", {}).get("OutcomesModule", {}).get("PrimaryOutcomeList", {}).get("PrimaryOutcome", []),
            }
            studies.append(protocol)
        return studies
    except Exception:
        return []


# Utility: ask the LLM and request strict JSON output
def _call_llm_for_protocol(prompt: str, model: str = "gpt-4", temperature: float = 0.3, max_tokens: int = 2500):
    """
    Calls OpenAI ChatCompletion API and returns the assistant content.
    Keeps a light temperature for reproducible / cautious output.
    """
    if not openai.api_key:
        raise ValueError("OpenAI API key is not set. Set openai.api_key or environment variable OPENAI_API_KEY.")

    # system instruction to ensure JSON-only output
    system_msg = {
        "role": "system",
        "content": (
            "You are an expert clinical trial designer and regulatory-aware medical writer. "
            "Produce ONLY valid JSON that conforms to the requested schema. Do not include any surrounding commentary. "
            "If you must include notes, place them in the JSON field 'notes'."
        )
    }
    user_msg = {"role": "user", "content": prompt}

    # attempt chat completions (use ChatCompletion for compatibility)
    resp = openai.ChatCompletion.create(
        model=model,
        messages=[system_msg, user_msg],
        temperature=temperature,
        max_tokens=max_tokens,
        n=1
    )
    content = resp["choices"][0]["message"]["content"]
    return content


def _make_prompt(pi_text: str, examples: Optional[List[Dict]], n_options: int):
    """
    Build a long prompt instructing the LLM to return a JSON array of `n_options` protocols.
    The schema requested corresponds to the sections you gave.
    """
    schema = {
        "SECTION 1": ["protocol_title", "protocol_id", "version", "date", "sponsor", "principal_investigator", "clinicaltrials_gov_id", "ind_ide_number", "protocol_synopsis"],
        "SECTION 2": ["disease_overview", "investigational_product_background", "study_rationale"],
        "SECTION 3": ["primary_objectives", "primary_endpoints", "secondary_objectives", "secondary_endpoints", "exploratory_objectives", "exploratory_endpoints", "safety_objectives", "safety_endpoints"],
        "SECTION 4": ["overall_design", "randomization", "blinding", "control", "treatment_arms"],
        "SECTION 5": ["target_population", "sample_size", "inclusion_criteria", "exclusion_criteria"],
        "SECTION 6": ["investigational_product", "dose_modifications", "control_comparator", "concomitant_medications", "treatment_duration"],
        "SECTION 7": ["study_procedures", "visit_schedule", "assessments_by_visit"],
        "SECTION 8": ["schedule_of_activities_table_note"],
        "SECTION 9": ["safety_monitoring", "ae_definitions", "reporting_requirements", "dsmb_plan"],
        "SECTION 10": ["statistical_analysis_plan"],
        "SECTION 11": ["timeline_milestones"],
        "SECTION 12": ["study_operations_quality"],
        "SECTION 13": ["subject_management"],
        "SECTION 14": ["pharmacokinetics_section_if_applicable"],
        "SECTION 15": ["biomarkers_translational"],
        "SECTION 16": ["quality_of_life_pro"],
        "SECTION 17": ["data_handling_ethics"],
        "SECTION 18": ["references"],
        "SECTION 19": ["appendices"]
    }

    prompt_lines = []
    prompt_lines.append("You are an expert clinical trial protocol writer and regulatory/operations advisor.")
    prompt_lines.append("A principal investigator has given the following short instruction (PI input):")
    prompt_lines.append(f'"""\n{pi_text}\n"""')
    prompt_lines.append("")
    prompt_lines.append(
        f"Produce EXACTLY {n_options} alternative, fully-structured clinical trial protocol drafts as a JSON array. "
        "Each element in the array must be a JSON object containing the following top-level keys (use these section headings):"
    )
    # Provide the required sections and required fields
    for sec, fields in schema.items():
        prompt_lines.append(f"- {sec}: {fields}")

    prompt_lines.append("")
    prompt_lines.append(
        "Each field should be filled with specific, realistic values. Use best practice regulatory conventions (ICH-GCP, FDA/EMA guidance) "
        "for required items like primary endpoint definition, safety reporting timelines, DSMB rules, and statistical thresholds. "
        "If exact numbers (e.g., prevalence, effect size) are not known, provide reasonable assumptions and state them under the key 'assumptions' "
        "inside the protocol object. Provide 'feasibility_notes' describing why this design is feasible (recruitment estimate, site count assumptions)."
    )

    if examples:
        prompt_lines.append("")
        prompt_lines.append("Use the following example trial summaries from ClinicalTrials.gov to help choose plausible designs and language (these are examples only):")
        for ex in examples:
            prompt_lines.append(json.dumps(ex))
        prompt_lines.append("")

    prompt_lines.append("")
    prompt_lines.append(
        "OUTPUT FORMAT: Return ONLY valid JSON: a top-level array of protocol objects. "
        "Do not include any extra text before/after the JSON. Each protocol object must include a field called 'schema_version' (string) and 'generated_at' (ISO 8601 timestamp)."
    )

    prompt = "\n".join(prompt_lines)
    return prompt


def generate_full_protocol(pi_text: str, n_options: int = 1, include_references: bool = True) -> List[Dict]:
    """
    Main function to call from your app.
    - pi_text: short instruction from the PI (free text)
    - n_options: how many alternative protocols to return
    - include_references: whether to fetch small ClinicalTrials.gov examples to include in the prompt
    Returns: list of protocol dictionaries
    """

    # prepare examples (try clinicaltrials.gov)
    examples = []
    if include_references:
        # extract short topic/condition from the pi_text heuristically
        # naive: pick first noun phrase after 'for' or last phrase. Better to use more robust extraction later.
        condition = " ".join(pi_text.split()[:6])
        examples = fetch_clinicaltrials_examples(condition, max_results=2)

    prompt = _make_prompt(pi_text, examples, n_options)

    # Attempt multiple tries, and try to recover if JSON parse fails
    max_attempts = 2
    last_raw = None
    for attempt in range(max_attempts):
        try:
            raw = _call_llm_for_protocol(prompt, model="gpt-4", temperature=0.25, max_tokens=3500)
            last_raw = raw.strip()

            # some models may include markdown or code fences — try to extract JSON substring
            # Find first '[' and last ']' and parse substring
            first_idx = last_raw.find('[')
            last_idx = last_raw.rfind(']')
            if first_idx != -1 and last_idx != -1:
                json_text = last_raw[first_idx:last_idx+1]
            else:
                json_text = last_raw

            protocols = json.loads(json_text)
            # Add generated metadata if missing
            for p in protocols:
                if "schema_version" not in p:
                    p["schema_version"] = "1.0"
                if "generated_at" not in p:
                    p["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            return protocols
        except json.JSONDecodeError as e:
            # try a second pass: ask the LLM to ONLY return JSON
            try:
                followup_prompt = (
                    "Your previous response could not be parsed as JSON. "
                    "Please return ONLY the JSON array of protocol objects with no surrounding text. The schema required was provided earlier."
                )
                raw2 = _call_llm_for_protocol(followup_prompt + "\n\nOriginal content:\n" + (last_raw or ""), model="gpt-4", temperature=0.0)
                # try parse again
                first_idx = raw2.find('[')
                last_idx = raw2.rfind(']')
                if first_idx != -1 and last_idx != -1:
                    json_text = raw2[first_idx:last_idx+1]
                else:
                    json_text = raw2
                protocols = json.loads(json_text)
                for p in protocols:
                    if "schema_version" not in p:
                        p["schema_version"] = "1.0"
                    if "generated_at" not in p:
                        p["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                return protocols
            except Exception:
                # on failure, raise with trace
                raise RuntimeError("Failed to parse LLM output as JSON. Raw output:\n\n" + (last_raw or ""))
        except Exception as e:
            # other exceptions (e.g., rate limit), try again or raise
            if attempt + 1 >= max_attempts:
                raise
            time.sleep(1.5)

    # if we reach here, raise
    raise RuntimeError("Unable to generate protocol; LLM did not return valid JSON.")


# Example quick CLI usage for testing (not used in web UI)
if __name__ == "__main__":
    # Example: short PI text
    pi_text = "Design a randomized Phase II study to test Vaccine X for prevention of Disease Y, 200 patients."
    # Make sure to set your OpenAI API key before running:
    # export OPENAI_API_KEY="sk-..."
    openai.api_key = os.getenv("OPENAI_API_KEY")
    protos = generate_full_protocol(pi_text, n_options=2, include_references=True)
    print(json.dumps(protos, indent=2))
