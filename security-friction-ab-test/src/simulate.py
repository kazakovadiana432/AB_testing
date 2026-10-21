"""
Simulate recovery A/B test data: phone verification (treatment) vs current flow (control).
Assumptions live in config/settings.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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
    TIME_CTRL_MEDIAN,
    TIME_TREAT_MEDIAN,
    TIME_SIGMA,
    P_SUPPORT_CTRL,
    P_SUPPORT_TREAT
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

#set median time for completing verification for treatment and control
log_m = np.where(is_treat, np.log(TIME_TREAT_MEDIAN), np.log(TIME_CTRL_MEDIAN))

time_min = rng.lognormal(mean=log_m, sigma=TIME_SIGMA)
time_min = np.where(completed, time_min, np.nan)

support_probs = np.where(is_treat, P_SUPPORT_TREAT, P_SUPPORT_CTRL)
support_contact = rng.random(N_ATTEMPTS) < support_probs

#define who was blocked from takeover
takeover_blocked = is_fraud & (completed == False)

df = pd.DataFrame(
    {
        "attempt_id": np.arange(1, N_ATTEMPTS + 1),
        "user_id": rng.integers(1_000_000, 9_999_999, size=N_ATTEMPTS),
        "date": dates,
        "variant": variant,
        "device": device,
        "country": country,
        "is_fraud": is_fraud.astype(int),
        "completed": completed.astype(int),
        "time_to_complete_min": np.round(time_min, 2),
        "support_contact": support_contact.astype(int),
        "takeover_blocked": takeover_blocked.astype(int),
        "anomaly_day": anomaly.astype(int),
    }
)

#write to csv
DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

df.to_csv(DATA_PATH, index=False)
log.info(
    "Wrote %s rows -> %s (anomaly rows=%s)",
    f"{len(df):,}",
    DATA_PATH,
    f"{df['anomaly_day'].sum():,}",
)


if __name__ == "__main__":
    n = len(df)
    print(f"Wrote {n:,} rows -> {DATA_PATH}")
    print(df["variant"].value_counts(normalize=True).round(3))
    print()
    g = df[df["is_fraud"] == 0]
    print("Genuine completion by variant:")
    print(g.groupby("variant")["completed"].mean())
    print()
    f = df[df["is_fraud"] == 1]
    print(f"Fraud attempts: {len(f):,} ({len(f) / n:.2%})")
    print("Fraud takeover success (completed) by variant:")
    print(f.groupby("variant")["completed"].mean())
    print()
    print("Support rate by variant:")
    print(df.groupby("variant")["support_contact"].mean())
    print()
    print("Median time (completers) by variant:")
    print(
        df[df["completed"] == 1]
        .groupby("variant")["time_to_complete_min"]
        .median()
        .round(2)
    )
    print()
    print(f"Anomaly rows ({ANOMALY_DEVICE} {ANOMALY_DATE}): {df['anomaly_day'].sum():,}")
