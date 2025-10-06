import random
import pandas as pd

def generate_patients(criteria: dict, n: int = 100, seed: int = 42):
    """
    Simple synthetic patient generator.
    Uses eligibility criteria to create a basic dataset without faker.
    """

    random.seed(seed)

    # Basic attributes
    ages = [random.randint(criteria.get("age_min", 18), criteria.get("age_max", 65)) for _ in range(n)]
    genders = [random.choice(["Male", "Female"]) for _ in range(n)]
    biomarkers = criteria.get("biomarkers", [])
    exclusions = criteria.get("exclusions", [])

    # Generate simple synthetic data
    data = []
    for i in range(n):
        patient = {
            "Patient_ID": f"PAT-{i+1:04d}",
            "Age": ages[i],
            "Gender": genders[i],
            "Eligible": True,
        }

        # Add biomarkers
        for b in biomarkers:
            patient[b] = random.choice(["Positive", "Negative"])

        # Randomly exclude a few patients
        if random.random() < 0.1:
            patient["Eligible"] = False
            patient["ExclusionReason"] = random.choice(exclusions) if exclusions else "Random exclusion"
        else:
            patient["ExclusionReason"] = ""

        data.append(patient)

    return pd.DataFrame(data)