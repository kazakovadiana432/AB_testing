## Product question

Does adding a phone-verification step to account recovery reduce successful account takeovers without losing too many genuine members who need to get back in?

## Decision this changes

Whether to roll phone verification out to 100% of recovery attempts, keep the current flow, or redesign the step (e.g. skip for trusted devices).

## Ship rule (pre-committed)

Cost labels (assumptions)
€60 per lost genuine recovery
€400 per takeover prevented
How these were estimated: [cost_assumptions.md](cost_assumptions.md)

Net value per 100,000 attempts
(takeovers prevented × €400) − (lost genuine recoveries × €60)
Break-even roughly when takeover cost >= 5.5× lost-genuine cost
(€60 lost → takeover worth >= €330)

2 pp is the MDE (smallest drop we power the test to detect: 80% → 78%)
It is not an automatic kill switch: a drop a bit above 2 pp can still ship if net value is clearly positive
A >= 5 pp completion drop is treated as too much friction regardless of the euro math

Operations guardrail reach thresholds (locked in [config/settings.py](../config/settings.py); see [metrics.md](metrics.md))

| Guardrail | Measure | Kill if |
|---|---|---|
| Support time | support_contact rate, treatment / control | ratio >= 2.0 |
| Time to complete verification | median time_to_complete_min among completers | ratio >= 2.0 or lift >= +3 minutes |
| Security gain | takeover_blocked rate lift among fraud (treat − ctrl) | lift < 10 pp |

| Outcome | Rule |
|---|---|
| Ship (X) | Takeovers blocked rise, completion drop is under 5 pp, and net value at €60 / €400 is > 0 and guardrails do not hit the threshold. |
| Do not ship (Y) | Net value at €60 / €400 is <= 0, or completion drop is >= 5 pp, or guardrails hit the threshold. |
| Iterate (Z) | Net near zero / finance disputes the €60 or €400 labels, or the completion hit is concentrated on one device (e.g. web much worse) — redesign that slice, no full rollout. |

