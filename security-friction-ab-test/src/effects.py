"""Metrics analysis, bootstrap check, guardrails"""


import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import confint_proportions_2indep, proportions_ztest

from config.settings import (
    ALPHA,
    BOOTSTRAP_B,
    SEED,
    SUPPORT_RATE_RATIO_MAX,
    TAKEOVER_BLOCK_LIFT_MIN,
    TIME_MEDIAN_LIFT_MAX_MIN,
    TIME_MEDIAN_RATIO_MAX,
)


def metrics_analysis(df):
    rng = np.random.default_rng(SEED)
    g = df[df["is_fraud"] == 0]
    f = df[df["is_fraud"] == 1]

    print("--- Primary metrics ---")
    # completion rates
    ctrl = g.loc[g["variant"] == "control", "completed"]
    treat = g.loc[g["variant"] == "treatment", "completed"]
    p_c = ctrl.mean()
    p_t = treat.mean()

    # hypothesis testing with z-test for completion rate difference
    success_counts = [treat.sum(), ctrl.sum()]
    sample_sizes = [len(treat), len(ctrl)]

    z_stat, p_val = proportions_ztest(success_counts, sample_sizes)
    ci_low, ci_high = confint_proportions_2indep(
        success_counts[0], sample_sizes[0], success_counts[1], sample_sizes[1], compare="diff", method="wald", alpha=ALPHA
    )
    print(f"control completion rate: {p_c:.4f} (n={len(ctrl):,})  treatment completion rate: {p_t:.4f} (n={len(treat):,})")
    print(f"completion rate difference: {p_t - p_c:.4f}  95% CI [{ci_low:.4f}, {ci_high:.4f}]")
    print(f"z={z_stat:.3f}, p={p_val:.2e}")
    print("significant at alpha={ALPHA:.0%}:", p_val < ALPHA)

    # bootstrap check for completion rate difference
    c_vals = ctrl.values
    t_vals = treat.values
    n_bootstraps = BOOTSTRAP_B
    boot_diffs = []
    for i in range(n_bootstraps):
        treat_sample = rng.choice(t_vals, size=len(t_vals), replace=True)
        ctrl_sample = rng.choice(c_vals, size=len(c_vals), replace=True)

        boot_diffs.append(treat_sample.mean() - ctrl_sample.mean())

    ci_b_low, ci_b_high = np.percentile(boot_diffs, [2.5, 97.5])
    print(f"bootstrap mean diff={np.mean(boot_diffs):.4f}  95% CI [{ci_b_low:.4f}, {ci_b_high:.4f}]")

    print("\n--- Guardrails metrics---")
    fc = f.loc[f["variant"] == "control", "takeover_blocked"]
    ft = f.loc[f["variant"] == "treatment", "takeover_blocked"]

    # guardrail metric with z-test for takeover blocked rate difference
    success_blocked_counts = [ft.sum(), fc.sum()]
    sample_blocked_sizes = [len(ft), len(fc)]

    z_tb, p_tb = proportions_ztest(success_blocked_counts, sample_blocked_sizes)

    print(f"Takeover blocked (among fraud) control takeover blocked rate: {fc.mean():.4f}  treatment takeover blocked rate: {ft.mean():.4f}  "
        f"diff={ft.mean() - fc.mean():.4f} z={z_tb:.3f}, p={p_tb:.2e}")

    # guardrail metric with z-test for support contact rate difference
    sc = df.loc[df["variant"] == "control", "support_contact"]
    st = df.loc[df["variant"] == "treatment", "support_contact"]

    success_contact_counts = [st.sum(), sc.sum()]
    sample_contact_sizes = [len(st), len(sc)]

    z_s, p_s = proportions_ztest(success_contact_counts, sample_contact_sizes)

    print(f"Support contact (among genuine) control support contact rate: {sc.mean():.4f}  treatment support contact rate: {st.mean():.4f}  "
        f"diff={st.mean() - sc.mean():.4f} z={z_s:.3f}, p={p_s:.2e}")

    # guardrail metric with Mann-Whitney test for time to complete difference
    tc = df.loc[
        (df["variant"] == "control") & (df["completed"] == 1), "time_to_complete_min"
    ]
    tt = df.loc[
        (df["variant"] == "treatment") & (df["completed"] == 1), "time_to_complete_min"
    ]
    _, p_time = stats.mannwhitneyu(tt, tc, alternative="two-sided")
    print("\nTime to complete (Mann-Whitney)")
    print(f"median ctrl={tc.median():.2f}  treat={tt.median():.2f}  p={p_time:.2e}")