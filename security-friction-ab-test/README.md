# Security vs friction A/B test (simulated)

This is a simulated A/B test for account recovery on a C2C marketplace. 
Treatment adds phone verification. 
The product question is whether that check is worth the friction it introduces. 
Genuine completion is the primary metric. 
Takeover blocking, support contacts, and time-to-complete are guardrails: if one of them fail in our expected behaviour, we do not ship even when completion looks fine. 
Everything is generated from knobs in `config/settings.py`

## Where to start

Docs set the decision frame that the analysis is supposed to answer.

1. `docs/product_question.md` defines the question, the ship / no-ship / iterate rule, and the guardrail thresholds we committed to up front.
2. `docs/metrics.md` explains what counts as primary vs guardrail and how each is defined on the attempt grain.
3. `docs/tracking_plan.md` covers events, assignment, and what we would need in a real instrumentation plan.
4. `docs/experiment_design.md` has the hypothesis, power thinking, and the statistical methods used downstream.
5. `docs/cost_assumptions.md` is why we use €60 per lost genuine recovery and €400 per takeover in the trade-off.
6. `docs/recommendation.md` is the one-page conclusion over the data we saw in the project with recomendations for ship/no-ship decision.
7. `notebooks/findings.ipynb` is the notebook with step-by-step analysis and conclusions drawn from the results.

Assumptions and sample-size knobs live in `config/settings.py`. File locations for the CSV and figures are in `config/paths.py`.

## How to run

From the project root, create a virtual environment, activate it, then install and run:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt

#simulate the data
python src/simulate.py

#run the whole A/B project
python src/main.py
```

`simulate.py` builds `data/recovery_ab.csv`. `main.py` loads that file and walks through quality checks, EDA, SRM, effects, the cost trade-off, and the anomaly RCA, printing the tables you need for the memo.

You can also run modules one at a time while debugging or investigating a specific step:

```bash
python src/design.py      # power / required n
python src/sanity.py      # data quality, EDA, SRM + balance
python src/effects.py     # primary test, guardrails, device slices
python src/tradeoff.py    # net EUR and cost sensitivity grid
python src/anomaly.py     # Android day check + KPI plots
```

## A/B pipeline - `main.py`

First it loads the CSV and runs data quality, then a light EDA, then SRM and covariate balance. If SRM fails we stop: the rest of the analysis is not trustworthy on a broken assignment. If SRM passes we estimate the primary and guardrail effects, feed those rates into the cost trade-off, and finally check whether the planted Android outage day is driving the treatment effect (it hits both arms, so it should not).

## Layout

```
config/     simulation and analysis knobs, file paths
src/        simulate data, power analysis, sanity checks, metrics analysis, trade-off, anomaly RCA; main.py runs modules in order
utils/      shared helpers (load the CSV)
docs/       product and methods documents
data/       generated CSV and plots (gitignored)
```

## Outputs

After a full run you should have:

| File | From |
|---|---|
| `data/recovery_ab.csv` | `simulate.py` |
| `data/eda_*.png` | `sanity.py` |
| `data/kpi_by_variant.png`, `data/kpi_by_device.png` | `anomaly.py` |

The rate tables, tests, and cost grid print to the terminal from `main.py` (or from the individual modules).

## Limits

- Results are based on the assumptions in `settings.py`.
- We do not model fraudsters adapting after the new verification step is implemented.
- The €60 / €400 costs are planning labels from `docs/cost_assumptions.md`.
- The simulation data includes a true `is_fraud` flag. In reality, production data would use a noisy proxy such as `takeover_flagged`.
- The window is about 30 days with one primary metric, and there is no long-run retention story.
- The Android completion drop on 2026-09-12 is planted on purpose, as practice for anomaly RCA.
