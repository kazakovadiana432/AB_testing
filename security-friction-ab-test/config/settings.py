"""
All modelling and analysis knobs
"""

# for reproducibility
SEED = 42

# simulation parameters
N_ATTEMPTS = 100_000
P_TREATMENT = 0.50

# experiment design decisions
BASELINE = 0.80
MDE = 0.02
ALPHA = 0.05
POWER = 0.80

# guardrail thresholds for operations veto
SUPPORT_RATE_RATIO_MAX = 2.0  # treatment / control; >= this = support "explodes"
TIME_MEDIAN_RATIO_MAX = 2.0  # treatment / control median minutes among completers
TIME_MEDIAN_LIFT_MAX_MIN = 3.0  # or absolute lift >= this many minutes
TAKEOVER_BLOCK_LIFT_MIN = 0.10  # "little security gain" for operations veto: 
                                #blocked-rate lift among fraud below this => do not ship

# trade-off
COST_LOST_GENUINE = 60  # EUR: missed transactions + support + mild churn
COST_TAKEOVER = 400  # EUR
N_SCALE = 100_000
LOST_COST_GRID = [10, 20, 30, 50, 80]
TAKEOVER_COST_GRID = [100, 250, 400, 750, 1000]

# primary friction hard veto
COMPLETION_DROP_HARD_MAX = 0.05  # >= 5 pp drop => do not ship regardless of net value
