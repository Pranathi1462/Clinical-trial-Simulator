"""
protocol_parser.py
Lightweight parser: converts a short protocol text into a structured protocol dict.
This parser is intentionally conservative: it extracts title, inclusion/exclusion,
sample size, primary endpoint and a free-text synopsis.
For production, replace with a more robust NLP/GROBID pipeline.
"""

import re
from typing import Dict, List


def _extract_sample_size(text: str):
    m = re.search(r"(?:sample size|n=|n\s*=\s*)(\d{2,6})", text, flags=re.I)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            return None
    # fallback: look for 'N = 200' style
    m2 = re.search(r"\bN\s*=\s*(\d{2,6})\b", text)
    if m2:
        try:
            return int(m2.group(1))
        except Exception:
            return None
    return None


def _extract_age_range(text: str):
    m = re.search(r"age\s*(?:between|from)?\s*(\d{1,3})\s*(?:and|to|-)\s*(\d{1,3})", text, flags=re.I)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None


def _lines_as_list(block: str) -> List[str]:
    if not block:
        return []
    lines = [l.strip("-•* \t\r\n") for l in re.split(r"[\r\n]+", block) if l.strip()]
    return lines


def parse_protocol(text: str) -> Dict:
    """
    Parse a short protocol text blob into a structured dict.
    Returns keys: title, synopsis, inclusion_criteria (list), exclusion_criteria (list),
    sample_size, primary_endpoint, age_min, age_max, raw_text.
    """
    title = ""
    synopsis = ""
    inclusion = []
    exclusion = []
    sample_size = _extract_sample_size(text)
    age_min, age_max = _extract_age_range(text)
    primary_endpoint = None

    # Try to locate title (first short line)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if lines:
        # heuristically treat first line as title if short
        if len(lines[0].split()) <= 10:
            title = lines[0]
            synopsis = "\n".join(lines[1:5])
        else:
            synopsis = "\n".join(lines[:4])

    # find inclusion / exclusion blocks
    inc_match = re.search(r"(Inclusion[s]? Criteria|Inclusion|Inclusion Criteria)[:\s]*(.+?)(?:Exclusion|Exclusion Criteria|Sample size|Primary endpoint|$)", text, flags=re.I | re.S)
    if inc_match:
        inc_block = inc_match.group(2)
        inclusion = _lines_as_list(inc_block)

    exc_match = re.search(r"(Exclusion[s]? Criteria|Exclusion|Exclusion Criteria)[:\s]*(.+?)(?:Inclusion|Sample size|Primary endpoint|$)", text, flags=re.I | re.S)
    if exc_match:
        exc_block = exc_match.group(2)
        exclusion = _lines_as_list(exc_block)

    # primary endpoint
    pe_match = re.search(r"(Primary endpoint[s]?:|Primary Outcome[s]?:)(.+?)(?:Secondary|$)", text, flags=re.I | re.S)
    if pe_match:
        primary_endpoint = pe_match.group(2).strip().splitlines()[0].strip()

    # naive fallback: look for "Primary endpoint: ..." inline
    if not primary_endpoint:
        m = re.search(r"Primary endpoint[:\-]\s*(.+)", text, flags=re.I)
        if m:
            primary_endpoint = m.group(1).splitlines()[0].strip()

    return {
        "title": title or "Protocol (unspecified title)",
        "synopsis": synopsis or text[:400],
        "inclusion_criteria": inclusion,
        "exclusion_criteria": exclusion,
        "sample_size": sample_size,
        "primary_endpoint": primary_endpoint,
        "age_min": age_min,
        "age_max": age_max,
        "raw_text": text
    }

