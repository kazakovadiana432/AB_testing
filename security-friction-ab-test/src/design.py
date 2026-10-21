"""Step 5 — pre-registered power / sample size (before reading effects as evidence)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

from config.settings import ALPHA, BASELINE, MDE, POWER
from utils.io import load_recovery_data
from utils.logging_config import get_logger
log = get_logger("design")

def power_analysis(df):
    effect_size = proportion_effectsize(BASELINE, BASELINE - MDE)
    analysis = NormalIndPower()
    sample_size = analysis.solve_power(
                effect_size=effect_size,
                power=POWER,
                alpha=ALPHA,
                ratio=1,
                alternative="two-sided",
            )

    n_per_variant = int(float(sample_size))
    print(f"Required n per variant (genuine): {n_per_variant:,.0f}")

    n_days = df["date"].nunique()
    daily_genuine = (df["is_fraud"] == 0).sum() / n_days
    daily_per_variant = daily_genuine / 2
    days_needed = n_per_variant / daily_per_variant
    current_volume = df[df["is_fraud"] == 0].groupby("variant").size()

    print()
    log.info("\n\nRunning power analysis")
    print(f"Cohen's h: {effect_size:.4f}")
    print(f"Daily genuine {daily_genuine:,.0f}  ->  {daily_per_variant:,.0f}/variant")
    print(f"Required days: {days_needed:.1f} days | available days: {n_days} days")
    current_n = int(current_volume.min())
    print(f"Required n per variant (genuine): {n_per_variant:,.0f} | current volume: {current_n:,.0f}")
    if current_n >= n_per_variant:
        print(f"Status for {MDE:.0%} MDE: over-powered (have {current_n:,.0f} / need {n_per_variant:,.0f})")
    else:
        print(f"Status for {MDE:.0%} MDE: under-powered (have {current_n:,.0f} / need {n_per_variant:,.0f})")

if __name__ == "__main__":
    df = load_recovery_data()
    power_analysis(df)
    print()