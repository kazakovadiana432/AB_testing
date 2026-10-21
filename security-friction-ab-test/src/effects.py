"""Primary metrics, bootstrap check, guardrails, device segments + BH"""


import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import confint_proportions_2indep, proportions_ztest

from utils.io import load_recovery_data

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
    ctrl_completion_rate = ctrl.mean()
    treat_completion_rate = treat.mean()

    # hypothesis testing with z-test for completion rate difference
    success_counts = [treat.sum(), ctrl.sum()]
    sample_sizes = [len(treat), len(ctrl)]

    z_stat, p_val = proportions_ztest(success_counts, sample_sizes)
    ci_low, ci_high = confint_proportions_2indep(
        success_counts[0], sample_sizes[0], success_counts[1], sample_sizes[1], compare="diff", method="wald", alpha=ALPHA
    )
    print(f"control completion rate: {ctrl_completion_rate:.4f} (n={len(ctrl):,})  treatment completion rate: {treat_completion_rate:.4f} (n={len(treat):,})")
    print(f"completion rate difference: {treat_completion_rate - ctrl_completion_rate:.4f}  95% CI [{ci_low:.4f}, {ci_high:.4f}]")
    print(f"z={z_stat:.3f}, p={p_val:.2e}")
    print(f"significant at alpha={ALPHA:.2f}:", p_val < ALPHA)

    # bootstrap check for completion rate difference
    print("\n--- Bootstrap check for completion rate difference ---")
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

    print(f"Takeover blocked (among fraud) \n\tcontrol takeover blocked rate: {fc.mean():.4f}  \n\ttreatment takeover blocked rate: {ft.mean():.4f}  "
        f"\n\tdiff={ft.mean() - fc.mean():.4f} z={z_tb:.3f}, p={p_tb:.2e}")

    # guardrail metric with z-test for support contact rate difference
    sc = df.loc[df["variant"] == "control", "support_contact"]
    st = df.loc[df["variant"] == "treatment", "support_contact"]

    success_contact_counts = [st.sum(), sc.sum()]
    sample_contact_sizes = [len(st), len(sc)]

    z_s, p_s = proportions_ztest(success_contact_counts, sample_contact_sizes)

    print(f"Support contact (among genuine) \n\tcontrol support contact rate: {sc.mean():.4f}  \n\ttreatment support contact rate: {st.mean():.4f}  "
        f"\n\tdiff={st.mean() - sc.mean():.4f} z={z_s:.3f}, p={p_s:.2e}")

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

    results = []
    for device in g["device"].unique():
        sub = g[g["device"] == device]

        c = sub.loc[sub["variant"] == "control", "completed"]
        t = sub.loc[sub["variant"] == "treatment", "completed"]

        p_val = proportions_ztest([t.sum(), c.sum()], [len(t), len(c)])[1]

        results.append(
            {
                "device": device,
                "completion_rate_ctrl": c.mean(),
                "completion_rate_treat": t.mean(),
                "completion_rate_diff": t.mean() - c.mean(),
                "p_value": p_val,
            }
        )

    device_results = pd.DataFrame(results)

    reject, pvals_corr, _, _ = multipletests(device_results["p_value"], method="fdr_bh")
    device_results["p_value_fdr"] = pvals_corr
    device_results["significant"] = reject
    device_results = device_results[
        ['device', 'completion_rate_ctrl', 'completion_rate_treat', 'completion_rate_diff', 'p_value', 'p_value_fdr', 'significant']]
    print("\nDevice segments analysis + BH")
    print(device_results.round(4).to_string(index=False))
    
    # Guardrail thresholds from docs/product_question.md (any fail => do not ship)
    support_ratio = st.mean() / sc.mean() if sc.mean() > 0 else float("inf")
    time_ratio = tt.median() / tc.median() if tc.median() > 0 else float("inf")
    time_lift = tt.median() - tc.median()
    block_lift = ft.mean() - fc.mean()

    support_too_high = support_ratio >= SUPPORT_RATE_RATIO_MAX
    time_too_slow = (
        time_ratio >= TIME_MEDIAN_RATIO_MAX or time_lift >= TIME_MEDIAN_LIFT_MAX_MIN
    )
    little_security = block_lift < TAKEOVER_BLOCK_LIFT_MIN
    guardrails_failed = support_too_high or time_too_slow or little_security

    print("\nOperations guardrail check")
    print(
        f"support ratio treat/ctrl={support_ratio:.2f}  "
        f"(fail if >={SUPPORT_RATE_RATIO_MAX:.1f})  -> "
        f"{'fail' if support_too_high else 'ok'}"
    )
    print(
        f"time median ratio={time_ratio:.2f}  lift={time_lift:.2f} min  "
        f"(fail if ratio>={TIME_MEDIAN_RATIO_MAX:.1f} or lift>={TIME_MEDIAN_LIFT_MAX_MIN:.1f})  -> "
        f"{'fail' if time_too_slow else 'ok'}"
    )
    print(
        f"takeover block lift={block_lift:.4f}  "
        f"(fail if <{TAKEOVER_BLOCK_LIFT_MIN:.2f})  -> "
        f"{'fail' if little_security else 'ok'}"
    )
    print(f"guardrails failed: {guardrails_failed}")

    return {
        "ctrl_completion_rate": ctrl_completion_rate,
        "treat_completion_rate": treat_completion_rate,
        "completion_rate_difference": treat_completion_rate - ctrl_completion_rate,
        "z_stat_completion_rate": z_stat,
        "p_val_completion_rate": p_val,
        "ci_low_completion_rate": ci_low,
        "ci_high_completion_rate": ci_high,
        "bootstrap_mean_diff_completion_rate": np.mean(boot_diffs),
        "bootstrap_ci_low_completion_rate": ci_b_low,
        "bootstrap_ci_high_completion_rate": ci_b_high,
        "ctrl_takeover_blocked_rate": fc.mean(),
        "treat_takeover_blocked_rate": ft.mean(),
        "z_stat_takeover_blocked": z_tb,
        "p_val_takeover_blocked": p_tb,
        "ctrl_support_contact_rate": sc.mean(),
        "treat_support_contact_rate": st.mean(),
        "z_stat_support_contact": z_s,
        "p_val_support_contact": p_s,
        "time_median_ctrl": tc.median(),
        "time_median_treat": tt.median(),
        "time_median_difference": tt.median() - tc.median(),
        "p_val_time_median": p_time,
        "device_results": device_results,
        "guardrails_failed": guardrails_failed,
    }

if __name__ == "__main__":
    df = load_recovery_data()
    metrics_analysis(df)