"""Detecting / segmenting / isolating / confirming a planted one-day device drop."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt
import pandas as pd
from statsmodels.stats.proportion import confint_proportions_2indep

from config.paths import FIG_PATH
from config.settings import ALPHA, ANOMALY_DATE, ANOMALY_DEVICE
from utils.io import load_recovery_data
from utils.logging_config import get_logger
log = get_logger("anomaly")

def run_anomaly(df, fig_path=FIG_PATH):
    log.info("Running anomaly detection")
    g = df[df["is_fraud"] == 0]
    n_anom = g["anomaly_day"].sum()
    print(f"Investigating planted anomaly {ANOMALY_DEVICE}/{ANOMALY_DATE} ({n_anom} genuine rows flagged)")

    for label, sub in [
        ("WITH anomaly rows", g),
        ("WITHOUT anomaly rows", g[g["anomaly_day"] == 0]),
    ]:
        ctrl = sub.loc[sub["variant"] == "control", "completed"]
        treat = sub.loc[sub["variant"] == "treatment", "completed"]
        diff = treat.mean() - ctrl.mean()
        ci_low, ci_high = confint_proportions_2indep(treat.sum(), len(treat), ctrl.sum(), len(ctrl), compare="diff", method="wald", alpha=ALPHA)
        print(f"\n{label}: diff={diff:.4f} 95% CI [{ci_low:.4f}, {ci_high:.4f}] ctrl={ctrl.mean():.4f} treat={treat.mean():.4f}")

    daily_var = g.groupby(["date", "variant"])["completed"].mean().unstack("variant")
    daily_dev = g.groupby(["date", "device"])["completed"].mean().unstack("device")

    daily_var.plot(title="Daily genuine completion by variant", marker="o", markersize=3)
    plt.axvline(pd.Timestamp(ANOMALY_DATE), color="gray", ls="--")
    plt.ylabel("completion rate")
    plt.tight_layout()
    plt.savefig(Path(fig_path).with_name("kpi_by_variant.png"), dpi=100)
    plt.close()

    daily_dev.plot(title="Daily genuine completion by device", marker="o", markersize=3)
    plt.axvline(pd.Timestamp(ANOMALY_DATE), color="gray", ls="--")
    plt.ylabel("completion rate")
    plt.tight_layout()
    plt.savefig(Path(fig_path).with_name("kpi_by_device.png"), dpi=100)
    plt.close()

    day = g[g["date"] == ANOMALY_DATE]
    print(f"\n{ANOMALY_DATE} by device x variant:")
    print(day.groupby(["device", "variant"])["completed"].mean().round(3))

    # android anomaly day and other days completion by variant
    android = g[g["device"] == ANOMALY_DEVICE]
    android_day = android[android["date"] == ANOMALY_DATE]
    android_other = android[android["date"] != ANOMALY_DATE]
    print(f"\n{ANOMALY_DEVICE} completion by variant (anomaly day vs other days):")
    print(f"anomaly day: {android_day.groupby('variant')['completed'].agg(['mean', 'count']).round(3)}")
    print(f"other days: {android_other.groupby('variant')['completed'].agg(['mean', 'count']).round(3)}")


if __name__ == "__main__":
    df = load_recovery_data()
    run_anomaly(df)
