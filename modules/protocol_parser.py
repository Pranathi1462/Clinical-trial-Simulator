# modules/protocol_parser.py
import re

def parse_protocol(text):
    """
    Very lightweight parser that extracts:
    - indication (first line or title)
    - age_min, age_max
    - sample_size (n=)
    - mentions of EBV or other biomarkers (simple keyword search)
    - list of exclusion mentions
    Returns a dict.
    """
    if not text:
        return {}

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    indication = lines[0] if lines else "Unknown indication"

    # Age extraction
    age_min, age_max = None, None
    age_match = re.search(r'age\s*(?:between|:)?\s*(\d{1,3})\s*(?:and|-|to)\s*(\d{1,3})', text, re.IGNORECASE)
    if age_match:
        age_min = int(age_match.group(1))
        age_max = int(age_match.group(2))
    else:
        # look for simple "18+" patterns
        m = re.search(r'(\d{1,3})\s*\+', text)
        if m:
            age_min = int(m.group(1))
            age_max = 99

    # sample size
    sample_size = None
    m = re.search(r'\b[nN]\s*=\s*(\d{2,6})', text)
    if m:
        sample_size = int(m.group(1))
    else:
        m2 = re.search(r'sample size[:\s]+(\d{2,6})', text, re.IGNORECASE)
        if m2:
            sample_size = int(m2.group(1))

    # biomarkers / keywords
    biomarkers = []
    if re.search(r'\bEBV\b', text, re.IGNORECASE):
        biomarkers.append('EBV')
    if re.search(r'\bJC virus\b', text, re.IGNORECASE) or re.search(r'JCV\b', text, re.IGNORECASE):
        biomarkers.append('JCV')
    # add more as needed

    # Extract lines that look like exclusions (very naive)
    exclusions = []
    for ln in lines:
        if ln.lower().startswith('exclusion') or ln.lower().startswith('exclusion criteria') or 'exclude' in ln.lower():
            exclusions.append(ln)

    # If none found, look for sentences with 'no prior' or 'without'
    for sent in re.split(r'[.;]\s*', text):
        if 'no prior' in sent.lower() or 'without' in sent.lower() or 'exclude' in sent.lower():
            exclusions.append(sent.strip())

    return {
        "indication": indication,
        "age_min": age_min,
        "age_max": age_max,
        "sample_size": sample_size,
        "biomarkers": biomarkers,
        "exclusions": exclusions
    }
