"""Sanity checks: data quality, SRM, covariate balance."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.io import load_recovery_data

import pandas as pd
from scipy.stats import chi2_contingency, chisquare

from config.settings import (
    BALANCE_P_THRESHOLD,
    COUNTRY_SHARES,
    DEVICE_SHARES,
    SRM_P_THRESHOLD,
)

def data_quality_checks(df):
    print("--- Data quality ---")
    issues = []
    key_cols = [c for c in df.columns if c != "time_to_complete_min"]
    if df[key_cols].isna().any().any():
        issues.append("unexpected nulls")
    if ((df["completed"] == 1) & df["time_to_complete_min"].isna()).any():
        issues.append("completers missing time")
    if not df["attempt_id"].is_unique:
        issues.append("duplicate attempt_id")
    if not df["variant"].isin(["control", "treatment"]).all():
        issues.append("bad variant")
    if not df["device"].isin(DEVICE_SHARES).all():
        issues.append("bad device")
    if not df["country"].isin(COUNTRY_SHARES).all():
        issues.append("bad country")
    flags = ["is_fraud", "completed", "support_contact", "takeover_blocked", "anomaly_day"]
    if not df[flags].isin([0, 1]).all().all():
        issues.append("flags not 0/1")
    if (df["time_to_complete_min"] < 0).any():
        issues.append("negative time")

    print("Data quality:", "FAIL - " + "; ".join(issues) if issues else "PASS")
    return len(issues) == 0

def sanity_checks(df):
    print("--- Sanity checks ---")
    counts = df["variant"].value_counts()
    print(counts)
    n = counts.sum()
    chi2_srm, p_srm = chisquare(f_obs=counts.values, f_exp=[n / 2, n / 2])
    passed = p_srm >= SRM_P_THRESHOLD

    print(f"treatment share: {counts['treatment'] / n:.4f}")
    print(f"SRM test results: chi2={chi2_srm:.3f}, p={p_srm:.4f}")

    chi2_device, p_device, _, _ = chi2_contingency(pd.crosstab(df["variant"], df["device"]))
    print("\nDevice shares")
    print(pd.crosstab(df["variant"], df["device"], normalize="index").round(3))
    print(f"Device balance test results: chi2={chi2_device:.3f}, p={p_device:.4f}")
    passed_device = p_device >= BALANCE_P_THRESHOLD

    chi2_country, p_country, _, _ = chi2_contingency(pd.crosstab(df["variant"], df["country"]))
    print("\nCountry shares")
    print(pd.crosstab(df["variant"], df["country"], normalize="index").round(3))
    print(f"Country balance test results: chi2={chi2_country:.3f}, p={p_country:.4f}")
    passed_country = p_country >= BALANCE_P_THRESHOLD

    print(f"SRM test passed: {'PASS' if passed else 'FAIL'}")
    print(f"Device balance test passed: {'PASS' if passed_device else 'FAIL'}")
    print(f"Country balance test passed: {'PASS' if passed_country else 'FAIL'}")

    return {
        "srm_passed": passed,
        "p_srm": p_srm,
        "device_passed": passed_device,
        "p_device": p_device,
        "country_passed": passed_country,
        "p_country": p_country,
    }


if __name__ == "__main__":
    df = load_recovery_data()
    data_quality_checks(df)
    print()
    sanity_checks(df)