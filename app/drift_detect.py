from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp


def detect_drift(reference_file: str, production_file: str, threshold: float = 0.05) -> dict:
    reference_path = Path(reference_file)
    production_path = Path(production_file)

    if not reference_path.exists():
        raise FileNotFoundError(f"Missing reference file: {reference_path}")
    if not production_path.exists():
        raise FileNotFoundError(f"Missing production file: {production_path}")

    ref_df = pd.read_csv(reference_path)
    prod_df = pd.read_csv(production_path)

    if "Exited" in ref_df.columns:
        ref_df = ref_df.drop(columns=["Exited"])
    if "Exited" in prod_df.columns:
        prod_df = prod_df.drop(columns=["Exited"])

    common_cols = [col for col in ref_df.columns if col in prod_df.columns]
    if not common_cols:
        raise ValueError("No common columns to compare")

    results = {}
    for col in common_cols:
        if not np.issubdtype(ref_df[col].dtype, np.number):
            continue

        ref_values = ref_df[col].dropna().values
        prod_values = prod_df[col].dropna().values

        if len(ref_values) == 0 or len(prod_values) == 0:
            continue

        statistic, p_value = ks_2samp(ref_values, prod_values)
        drift_detected = p_value < threshold

        results[col] = {
            "p_value": float(p_value),
            "statistic": float(statistic),
            "drift_detected": drift_detected,
            "type": "ks",
        }

    return results
