# Recommendation: phone verification on account recovery

## Question
Does adding phone verification to account recovery reduce takeovers without losing too many genuine members?

Pre-committed rule: 
- ship if genuine-completion pain is acceptable and estimated net value is positive,
- do not ship if friction dominates or guardrails behaviour fails,
- iterate on mixed / segment-specific pain.

## Result (simulated experiment, n = 100,000 attempts)
| Metric | Finding |
|---|---|
| Primary - genuine completion rate | Control 79.3% -> treatment 76.5% (−2.8 pp, 95% CI −3.3 to −2.3, p < 0.05) |
| Guardrail - takeovers blocked (among fraud) | 45.8% -> 79.5% (+34 pp) |
| Guardrail - support contacts | 4.1% -> 5.6% (+1.6 pp) |
| Guardrail - time to complete (median) | 4.0 -> 6.5 minutes |
| SRM / balance | SRM pass; device/country practically balanced |
| Anomaly | Android 2026-09-12 outage hit both variants. Excluding this anomaly leaves the completion rate drop effect around -3.0 pp |

The data give a strong signal that treatment raises friction and blocks more takeovers.

## Trade-off (per 100,000 attempts)
- approx. 2,797 lost genuine recoveries vs approx. 508 takeovers prevented  
- Assumed costs: €60 per lost genuine recovery; €400 per takeover (see `docs/cost_assumptions.md`)  
- Net ≈ +€35k under those labels  
- Break-even: takeover cost >= 5.5× lost-genuine cost  

## Recommendation
**Ship** under the base-case cost assumptions (€60 / €400), accepting modest support and time increases.

**Do not ship** if finance prices takeovers cheap and lost recoveries expensive (see sensitivity in `src/tradeoff.py`).  

## Risks
- Cost assumptions drive the call more than the p-value.  
- The data are simulated, so this does not show how real fraudsters react once the check is live.
- In production we never know for sure which attempts belong to real members, so the genuine completion rate is an approximation.
- The test covers one short period, we don't know how the drop looks in long-term.