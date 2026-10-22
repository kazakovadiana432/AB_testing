"""
Run the full A/B analysis pipeline.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.io import load_recovery_data
from utils.logging_config import get_logger


import numpy as np

from anomaly import run_anomaly
from config.paths import FIG_PATH
from config.settings import SEED
from design import power_analysis
from effects import metrics_analysis
from sanity import eda_checks, sanity_checks, data_quality_checks
from tradeoff import run_tradeoff

log = get_logger("analysis")
rng = np.random.default_rng(SEED)

log.info("Starting analysis pipeline")
df = load_recovery_data()

# data quality checks
data_quality_checks(df)

# EDA checks
eda_checks(df)

# sanity checks
sanity = sanity_checks(df)
if not sanity["srm_passed"]:
    log.error("SRM failed (p=%.4f) - stopping analysis", sanity["p_srm"])
    sys.exit(1)
log.info(
    "SRM passed (p=%.4f); device balance p=%.4f; country balance p=%.4f",
    sanity["p_srm"],
    sanity["p_device"],
    sanity["p_country"],
)
# statistical analysis
eff = metrics_analysis(df, verbose=True)

# cost sensitivity analysis
trade = run_tradeoff(df, eff["ctrl_completion_rate"], eff["treat_completion_rate"], eff["ctrl_takeover_blocked_rate"], eff["treat_takeover_blocked_rate"])

# anomaly RCA
anom = run_anomaly(df, FIG_PATH)

# pipeline complete
log.info("Pipeline completed")
print("Done")
