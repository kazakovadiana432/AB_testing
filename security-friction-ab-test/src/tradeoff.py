"""Analysing cost sensitivity."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from config.settings import (
    COST_LOST_GENUINE,
    COST_TAKEOVER,
    LOST_COST_GRID,
    N_SCALE,
    TAKEOVER_COST_GRID,
)

from utils.io import load_recovery_data
from src.effects import metrics_analysis


def run_tradeoff(
    df,
    ctrl_completion_rate,
    treat_completion_rate,
    ctrl_takeover_blocked_rate,
    treat_takeover_blocked_rate,
):
    print("--- Cost sensitivity analysis ---")
    fraud_rate = df["is_fraud"].mean()
    drop = ctrl_completion_rate - treat_completion_rate
    lift_block = treat_takeover_blocked_rate - ctrl_takeover_blocked_rate

    lost_genuine = N_SCALE * (1 - fraud_rate) * drop
    takeovers_prevented = N_SCALE * fraud_rate * lift_block

    benefit = takeovers_prevented * COST_TAKEOVER
    cost = lost_genuine * COST_LOST_GENUINE
    net = benefit - cost
    breakeven_ratio = lost_genuine / takeovers_prevented

    print(f"Lost genuine / 100k: {lost_genuine:.0f}")
    print(f"Takeovers prevented / 100k: {takeovers_prevented:.0f}")
    print(f"Cost lost genuine (assumption): {COST_LOST_GENUINE} EUR")
    print(f"Cost takeover (assumption): {COST_TAKEOVER} EUR")
    print(f"Benefit: {benefit:,.0f} EUR | Cost: {cost:,.0f} EUR | Net: {net:,.0f} EUR")
    print(f"Break-even ratio cost_takeover/cost_lost = {breakeven_ratio:.2f}")

    grid = pd.DataFrame(
        index=[f"lost={c}" for c in LOST_COST_GRID],
        columns=[f"takeover={c}" for c in TAKEOVER_COST_GRID],
        dtype=float,
    )
    for lc in LOST_COST_GRID:
        for tc in TAKEOVER_COST_GRID:
            grid.loc[f"lost={lc}", f"takeover={tc}"] = (
                takeovers_prevented * tc - lost_genuine * lc
            )

    print("\nNet EUR / 100k (positive => value supports ship)")
    print(grid.round(0).astype(int).to_string())

    return {"net": net, "breakeven_ratio": breakeven_ratio}

if __name__ == "__main__":
    df = load_recovery_data()
    m = metrics_analysis(df)
    run_tradeoff(
        df,
        m["ctrl_completion_rate"],
        m["treat_completion_rate"],
        m["ctrl_takeover_blocked_rate"],
        m["treat_takeover_blocked_rate"],
    )