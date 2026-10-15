## Hypothesis and design (primary metric)

Primary: genuine recovery completion rate
p_t = treatment
p_c = control

| | |
|---|---|
| H0 | p_t = p_c — phone verification does not change genuine completion |
| H1 | p_t ≠ p_c — two-sided; rates differ (we expect p_t < p_c, but we test both ways) |
| alpha | 0.05 |
| Power | 0.80 |
| Baseline | 0.80 (assumed control completion) |
| MDE | 0.02 (2 pp) — smallest drop we care to detect (80% → 78%) |

Numbers are locked in [config/settings.py](../config/settings.py) and used by [src/design.py](../src/design.py) for sample size.

## Statistical methods (pre-committed)

Chosen before reading results. Implemented in [src/design.py](../src/design.py), [src/sanity.py](../src/sanity.py), [src/effects.py](../src/effects.py).

Before trusting results, check that the data roughly meet the assumptions. If they do not, fix tracking / rethink the method before shipping on p-values.

Shared for this experiment: independent attempts (`attempt_id`); random assignment at `recovery_started` (~50/50, not re-randomised); stable logging (no uneven missing `variant` / `attempt_id`).

| Check | Method | Assumptions | Why this method |
|---|---|---|---|
| Sample and effect size | Cohen's h for effect size; `solve_power` (NormalIndPower) for n per variant | Independence of samples. Binary data type. Sufficient amount of data for normal approximation. | Primary metric is a rate; this sizes n to detect the smallest drop we care about (MDE), with power already set to 0.80 |
| SRM | Chi-square goodness of fit vs 50/50 | Independence of observations. Categorical variables. Sufficient expected cell counts. | Check that control/treatment counts match the planned split |
| Covariate balance (device, country) | Chi-square test of independence (variant x slice) | Independence of observations. Categorical variables. Sufficient expected cell counts. | Soft check that randomisation did not skew device or country shares by variant |
| Genuine completion rate (primary) | Two-proportion z-test + 95% Wald CI on difference | Independence of samples. Binary data type. Sufficient amount of data for normal approximation. | Standard test for two rates at large n; CI determines uncertainty, because we care how much the completion rate will drop  |
| Primary robustness | Bootstrap 95% CI on mean difference | Attempts treated as similar draws within variant | Second look at the same lift without relying only on the Wald CI |
| Takeovers blocked | Two-proportion z-test | Independence of samples. Binary data type. Sufficient amount of data for normal approximation. | Rates are analysed with two proportion z test, this metric is used for guardrails, not as the only ship rule |
| Support contacts / attempt | Two-proportion z-test | Independence of samples. Binary data type. Sufficient amount of data for normal approximation. | Rates are analysed with two proportion z test, this metric is used for guardrails, not as the only ship rule |
| Time to complete | Mann-Whitney U among completers; ship rule uses median ratio / lift | Independence of samples (control vs treatment completers). Comparable ranks (minutes). No need for normality. | Time is skewed; rank test fits better than a t-test; thresholds still use medians |
| Device segments | Two-proportion z-test per device, then Benjamini-Hochberg (FDR) | Per device: independence of samples, binary completion, sufficient data for normal approximation. BH only adjusts those p-values — each device test must already be trustworthy on its own. | In testing several slices BH limits false discoveries by adjusting alpha; This measure for exploration only, not a second primary metric |

Ship or no-ship decision follows the rules in [product_question.md](product_question.md) (net value, 5 pp hard stop, operations thresholds), not p-value alone.
