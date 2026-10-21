"""Data quality, EDA plots, SRM, covariate balance."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.io import load_recovery_data
from utils.logging_config import get_logger

import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import chi2_contingency, chisquare

from config.paths import DATA_DIR
from config.settings import (
    BALANCE_P_THRESHOLD,
    COUNTRY_SHARES,
    DEVICE_SHARES,
    SRM_P_THRESHOLD,
)

log = get_logger("sanity")


def data_quality_checks(df):
    log.info("\n\nRunning data quality checks")
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


def eda_checks(df):
    log.info("\n\nRunning EDA checks")
    print(df.shape)
    print(df.head())
    print()
    print("fraud rate:", round(df["is_fraud"].mean(), 4))
    g = df[df["is_fraud"] == 0]
    print("\nGenuine completion:")
    print(g.groupby("variant")["completed"].mean().round(3))
    print()
    print("Support contact rate:")
    print(df.groupby("variant")["support_contact"].mean().round(3))
    print()
    print("Time to complete (median minutes):")
    print(
        df[df["completed"] == 1]
        .groupby("variant")["time_to_complete_min"]
        .median()
        .round(2)
    )

    # weekday volume
    weekday = df["date"].dt.day_name()
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    print("\nVolume by weekday:")
    print(weekday.value_counts().reindex(order))
    print("\nCompleted attempts by weekday:")
    print(weekday[df["completed"] == 1].value_counts().reindex(order))
    print("\nFraud attempts by weekday:")
    print(weekday[df["is_fraud"] == 1].value_counts().reindex(order))

    print("\nFraud rate by device:")
    print(df.groupby("device")["is_fraud"].mean().round(4))
    print("\nFraud rate by country:")
    print(df.groupby("country")["is_fraud"].mean().round(4))

    # plots
    g.groupby("date").size().plot(title="Daily volume (genuine)")
    plt.ylabel("attempts")
    plt.tight_layout()
    plt.savefig(DATA_DIR / "eda_volume.png", dpi=100)
    plt.close()

    g.groupby(["date", "variant"])["completed"].mean().unstack().plot(
        title="Daily genuine completion by variant"
    )
    plt.ylabel("rate")
    plt.tight_layout()
    plt.savefig(DATA_DIR / "eda_completion.png", dpi=100)
    plt.close()

    weekday.value_counts().reindex(order).plot(kind="bar", title="Volume by weekday")
    plt.ylabel("attempts")
    plt.tight_layout()
    plt.savefig(DATA_DIR / "eda_weekday.png", dpi=100)
    plt.close()

    # duration for completed attempts
    df.loc[df["completed"] == 1, "time_to_complete_min"].plot(
        kind="hist", bins=40, title="Time to complete (minutes, completers)"
    )
    plt.xlabel("minutes")
    plt.tight_layout()
    plt.savefig(DATA_DIR / "eda_time.png", dpi=100)
    plt.close()

    df.groupby("device")["is_fraud"].mean().plot(kind="bar", title="Fraud rate by device")
    plt.ylabel("fraud rate")
    plt.tight_layout()
    plt.savefig(DATA_DIR / "eda_fraud_device.png", dpi=100)
    plt.close()

    df.groupby("country")["is_fraud"].mean().plot(kind="bar", title="Fraud rate by country")
    plt.ylabel("fraud rate")
    plt.tight_layout()
    plt.savefig(DATA_DIR / "eda_fraud_country.png", dpi=100)
    plt.close()


def sanity_checks(df):
    log.info("\n\nRunning sanity checks")
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
    eda_checks(df)
    sanity_checks(df)
