## Metric set

| Role | Metric | Expected direction (treatment) | Why |
|---|---|---|---|
| Primary | Genuine recovery completion rate | Down (~2–4 pp) | Extra phone step -> more genuine drop-off |
| Guardrail | Takeovers blocked (rate) | Up | Fraud fails the check more often |
| Guardrail | Support contacts / attempt | Up (modest) | Confused users hit support |
| Guardrail | Time to complete | Up, right-skewed | Codes take time; only among who finish |

## Primary vs guardrail

Primary answers: Did we hurt real members getting back in?
Guardrails answer: Did security improve, and did operations blow up?
Do not declare success if a guardrail wins while the primary fails.

## How to measure that opearations are not successful

Measured in [src/effects.py](../src/effects.py). Thresholds locked in [config/settings.py](../config/settings.py).

| Question | Metric in data | Pass / fail rule |
|---|---|---|
| Did security improve? | takeover_blocked rate among is_fraud=1 | lift (treat − ctrl) >= 10 pp |
| Did support time increased dramatically? | treat / ctrl >= 2.0 |
| Is time to complete verification too slow? | median time_to_complete_min among completed=1 | treat / ctrl >= 2.0 or (treat − ctrl) >= +3 min |
