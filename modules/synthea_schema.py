# modules/optimizer.py
import random
import math
from statsmodels.stats.power import TTestIndPower
from sklearn.cluster import KMeans
import numpy as np

power_calc = TTestIndPower()

def compute_power(effect_size, n_per_group, alpha=0.05):
    try:
        power = power_calc.power(effect_size=effect_size, nobs1=n_per_group, alpha=alpha, ratio=1.0)
    except Exception:
        power = 0.0
    return power

def score_design(sample_size, looseness_score, est_effect=0.4):
    # sample_size: total
    n_per_group = max(2, int(sample_size / 2))
    pow_score = compute_power(est_effect, n_per_group)
    # feasibility: smaller sample and looser criteria -> higher feasibility
    feasibility = 1.0 - (sample_size / 2000.0) - (looseness_score * 0.1)
    feasibility = max(0.0, min(1.0, feasibility))
    # final score combine power and feasibility
    return 0.6 * pow_score + 0.4 * feasibility

def generate_candidate(parsed, variation_frac=0.2):
    base_n = parsed.get("sample_size") or 200
    # randomize sample size around base
    delta = int(base_n * variation_frac)
    new_n = max(20, base_n + random.randint(-delta, delta))
    # looseness score = number of exclusions removed/relaxed (0..3)
    looseness = random.choice([0,1,2])
    # randomize randomization ratio
    rand_ratio = random.choice([1.0, 1.5, 2.0])
    score = score_design(new_n, looseness)
    return {
        "sample_size": new_n,
        "looseness": looseness,
        "rand_ratio": rand_ratio,
        "score": score
    }

def optimize_protocol(parsed, pool_size=12, pick_k=3):
    # generate pool_size candidates, score them, then pick 3 diverse ones
    pool = []
    for _ in range(pool_size):
        c = generate_candidate(parsed)
        pool.append(c)

    # vectorize for clustering: sample_size, looseness, rand_ratio
    X = np.array([[c['sample_size'], c['looseness'], c['rand_ratio']] for c in pool])
    k = min(pick_k, len(pool))
    # cluster into k groups to get diversity
    try:
        km = KMeans(n_clusters=k, random_state=0).fit(X)
        labels = km.labels_
    except Exception:
        # fallback: sort by score
        pool_sorted = sorted(pool, key=lambda x: -x['score'])
        return pool_sorted[:k]

    selected = []
    for lab in range(k):
        # take best in each cluster by score
        members = [pool[i] for i in range(len(pool)) if labels[i]==lab]
        members_sorted = sorted(members, key=lambda x: -x['score'])
        selected.append(members_sorted[0])
    # sort selected by score descending
    selected.sort(key=lambda x: -x['score'])
    return selected
