"""
Simulate recovery A/B test data: phone verification (treatment) vs current flow (control).
Assumptions live in config/settings.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.io import ensure_project_on_path

ensure_project_on_path()

import numpy as np
import pandas as pd

from config.paths import DATA_PATH
from utils.logging_config import get_logger
from config.settings import (
    ANOMALY_COMPLETE_MULT,
    ANOMALY_DATE,
    ANOMALY_DEVICE,
    BASE_COMPLETE_GENUINE,
    BASE_TAKEOVER_SUCCESS,
    COUNTRY_SHARES,
    DEVICE_SHARES,
    N_ATTEMPTS,
    N_DAYS,
    P_FRAUD,
    P_TREATMENT,
    SEED,
    START_DATE,
    TREAT_COMPLETE_DROP,
    TREAT_TAKEOVER_SUCCESS,
 )
import warnings
#ignore future warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

log = get_logger("simulate")
log.info("Starting simulation n=%s seed=%s", f"{N_ATTEMPTS:,}", SEED)

#set random seed
rng = np.random.default_rng(SEED)

#list of devices
devices = list(DEVICE_SHARES.keys())
device_probs = list(DEVICE_SHARES.values())
countries = list(COUNTRY_SHARES.keys())
country_probs = list(COUNTRY_SHARES.values())

# Slightly uneven daily volume (weekends a bit lower) due to people using the app more on weekdays
day_weights = np.ones(N_DAYS)
#calendar Sat/Sun from START_DATE
calendar_days = pd.to_datetime(START_DATE) + pd.to_timedelta(np.arange(N_DAYS), unit="D")
day_weights[calendar_days.dayofweek == 5] = 0.75  # Saturday
day_weights[calendar_days.dayofweek == 6] = 0.70  # Sunday
#turn into probabilities
day_weights = day_weights / day_weights.sum()
#randomly choose a day for each attempt
day_ix = rng.choice(N_DAYS, size=N_ATTEMPTS, p=day_weights)
dates = calendar_days[day_ix]

#randomly choose a variant for each attempt
variant = np.where(rng.random(N_ATTEMPTS) < P_TREATMENT, "treatment", "control")
#randomly choose a device for each attempt
device = rng.choice(devices, size=N_ATTEMPTS, p=device_probs)
#randomly choose a country for each attempt
country = rng.choice(countries, size=N_ATTEMPTS, p=country_probs)

is_fraud = rng.random(N_ATTEMPTS) < P_FRAUD
is_treat = variant == "treatment"

#completion probabilities for fraud and real users
completion_probs = np.where(
    is_fraud,
    np.where(is_treat, TREAT_TAKEOVER_SUCCESS, BASE_TAKEOVER_SUCCESS),
    np.where(is_treat, BASE_COMPLETE_GENUINE - TREAT_COMPLETE_DROP, BASE_COMPLETE_GENUINE),
)


#create anomaly information
anomaly = (device == ANOMALY_DEVICE) & (dates == pd.Timestamp(ANOMALY_DATE))

#apply anomaly multiplier to completion probabilities
completion_probs = np.where(anomaly, completion_probs * ANOMALY_COMPLETE_MULT, completion_probs)

#define who completed recovery
completed = rng.random(N_ATTEMPTS) < completion_probs