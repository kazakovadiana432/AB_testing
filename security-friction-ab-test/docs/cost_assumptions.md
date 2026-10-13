# Cost assumptions

Planning labels for the ship rule. Not measured from the simulation.

---

## Takeover cost — €400 per successful takeover prevented

Decision: lock €400

Statistics used
$15.6B total ATO losses in 2024 ([AARP/Javelin via Cybercheck](https://www.cyberchecksecurity.com/en/insights/account_takeover_numbers))

24% of consumers reported ATO victimisation in 2024 (same source / Sift)

ATO volume still rising (~24–37% YoY in industry summaries: [Cybercheck](https://www.cyberchecksecurity.com/en/insights/account_takeover_numbers), [WiserNotify](https://wisernotify.com/blog/ecommerce-fraud-stats/))

~4 in 5 consumers would stop buying from a site after an ATO ([Sift via Cybercheck](https://www.cyberchecksecurity.com/en/insights/account_takeover_numbers))

How that leads to €400
Macro floor: $15.6B ÷ (0.24 × ~230M online consumers ≈ 55M) ≈ $280 / victim (mixes banks, email, retail — not C2C-only)

Marketplace build-up on top of that scale

| Component | EUR | Why |
|---|---:|---|
| Refunds / stolen goods / account abuse | 120 | Typical small/mid order damage on a C2C marketplace |
| Support and remediation | 40 | Tickets, investigation, password reset help |
| Trust / churn | 240 | ~80% leave × ~€300 annual contribution |
| Total | 400 | Above the ~€260 floor |

Also true
Sensitivity grid still tests €100–€1000 ([src/tradeoff.py](../src/tradeoff.py))
Not every fraud row in the sim is worth exactly €400; real ATOs vary

---

## Lost genuine recovery — €60 per failed recovery

Decision: lock €60

Statistics used
None from the ATO articles for “failed password reset” itself
Churn rate after ATO (~80%) is not copied here — failed recovery is milder; we use a lower leave probability (product judgment)

How that leads to €60 (product judgment)

| Component | EUR | Why |
|---|---:|---|
| Missed transactions while locked out | 20 | Roughly one small marketplace order |
| Extra support / reactivation friction | 10 | Ticket or delayed return |
| Churn risk | 30 | ~10% leave × ~€300 annual contribution (lower than ~80% after a full ATO) |
| Total | 60 | |

---

## Net value (ship math)

Per 100,000 attempts

(takeovers prevented × €400) − (lost genuine recoveries × €60)

Ship if net > 0
Do not ship on friction alone if completion drop is >= 5 pp (hard veto), even if net looks positive
