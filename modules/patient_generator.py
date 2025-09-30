# modules/patient_generator.py
import numpy as np
import pandas as pd

def generate_patients(criteria, n=50, seed=None):
    """
    Generate n synthetic patients that satisfy 'criteria'.
    criteria dict may contain age_min, age_max, biomarkers (list), exclusions list.
    This function produces diverse patients by varying demographics and labs.
    """
    rng = np.random.RandomState(seed or 0)

    age_min = criteria.get("age_min", 18)
    age_max = criteria.get("age_max", 65)
    biomarkers = criteria.get("biomarkers", [])

    rows = []
    for i in range(n):
        # age: sample uniformly but with some normal jitter
        age = int(rng.choice(range(age_min, age_max+1)))
        sex = rng.choice(['Male','Female'], p=[0.48, 0.52])
        # EBV handling: if criteria requires EBV negative, force it; else sample with typical adult prevalence
        if 'EBV' in biomarkers:
            # if biomarker listed, assume they want negative (we let PI decide)
            EBV_status = rng.choice(['negative','positive'], p=[0.8,0.2])
        else:
            EBV_status = rng.choice(['negative','positive'], p=[0.05,0.95])

        # comorbidity count increases with age
        comorbidity_prob = min(0.6, (age - 20) / 100.0)
        comorbidity_count = rng.binomial(3, comorbidity_prob)

        # generate two lab values correlated with age
        lab1 = round(rng.normal(loc=100 + (age-50)*0.5, scale=10), 1)
        lab2 = round(rng.normal(loc=7 + (comorbidity_count*0.5), scale=1.0), 2)

        rows.append({
            "patient_id": f"P{i+1:04d}",
            "age": age,
            "sex": sex,
            "EBV_status": EBV_status,
            "comorbidity_count": int(comorbidity_count),
            "lab1": lab1,
            "lab2": lab2
        })

    df = pd.DataFrame(rows)

    # If biomarker required to be negative, filter and if insufficient, oversample / replace
    if 'EBV' in biomarkers:
        # here we interpret as requiring EBV negative patients; keep only negative
        df = df[df['EBV_status']=='negative']
        if len(df) < n:
            # generate additional samples forcefully
            needed = n - len(df)
            extra = []
            for j in range(needed):
                age = int(rng.choice(range(age_min, age_max+1)))
                sex = rng.choice(['Male','Female'], p=[0.48,0.52])
                comorbidity_prob = min(0.6, (age - 20) / 100.0)
                comorbidity_count = rng.binomial(3, comorbidity_prob)
                lab1 = round(rng.normal(loc=100 + (age-50)*0.5, scale=10), 1)
                lab2 = round(rng.normal(loc=7 + (comorbidity_count*0.5), scale=1.0), 2)
                extra.append({
                    "patient_id": f"P_extra{j+1:03d}",
                    "age": age,
                    "sex": sex,
                    "EBV_status": 'negative',
                    "comorbidity_count": int(comorbidity_count),
                    "lab1": lab1,
                    "lab2": lab2
                })
            df = pd.concat([df, pd.DataFrame(extra)], ignore_index=True)

    # Ensure exactly n rows
    if len(df) > n:
        df = df.sample(n=n, random_state=rng)
    df = df.reset_index(drop=True)
    return df
