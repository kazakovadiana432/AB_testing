Metrics in [metrics.md](metrics.md) only work if events and assignment are logged the same way for control and treatment.

## Unit of analysis

| Decision | Choice | Reason |
|---|---|---|
| Analysis unit | `attempt_id` | Same user can start recovery more than once; rates are per attempt |
| Not only `user_id` | Rejected as sole key | Double-counts multi-attempt users and breaks completion |

## Assignment

| Decision | Choice | Reason |
|---|---|---|
| When to assign | At `recovery_started` | Everyone who enters recovery (clicked forgot password) is in the test, including early drop-offs |
| What to store | `variant` (`control` / `treatment`) on `attempt_id` | Source of truth for the whole funnel |
| Later events | Copy stored variant (or join on `attempt_id`) | Keeps sample ratio mismatch and effects valid |
| Not at `step_shown` | Rejected | `step_shown` is when the phone verification page appears (ask for number / SMS code). If we only put people in the test at that moment, anyone who started recovery and quit before that page never gets a variant and never enters the data. We do want those people in: they started recovery and did not finish |

## Events

| Event | When it starts | Required fields | Why |
|---|---|---|---|
| `recovery_started` | User clicks `forgot password`; once per attempt | `attempt_id`, `user_id`, `timestamp`, `variant`, `device`, `country`, `app_version` | Denominator of completion rate (finished / recovery_started); used for assignment; possible to use for slices in root cause analysis |
| `step_shown` | Phone verification page appeared (ask for number / SMS code). Control: same event with `step_name=none` (or skip marker) | Fields from `recovery_started` + `step_name` | Analyse at what step people leave the recovery process |
| `step_completed` | treatment: Phone code accepted, control:`step_name=none` since thre is no phone verification | Fields from `recovery_started` + `step_name` | Tracking users'behaviour and analysing on which step they leave, also small building block for completion rate (final is `recovery_completed`) |
| `step_abandoned` | User leaves without completing phone verification step, once per abandon (even if return to the screeen and left again) | Fields from `recovery_started`  + `step_name` | Separates users who never saw a step from users who saw and quit |
| `recovery_completed` | Password reset confirmed | Fields above | Numerator of completion rate (finished / recovery_started) |
| `takeover_flagged` | Fraud/security marks attempt or session (can be after recovery) | `attempt_id`, `user_id`, `timestamp`, `variant`, `flag_source` | Used for guardrail|

Support contacts come from helpdesk, joined on `user_id` (and preferably `attempt_id`) in a window after `recovery_started`.

## Metric and how it is calculated

| Metric ([metrics.md](metrics.md)) | Definition from events |
|---|---|
| Genuine completion rate | Take genuine attempts only (production: no `takeover_flagged`; simulation: `is_fraud=0`). Rate = `recovery_completed` /`recovery_started` |
| Takeovers blocked | Check only among `is_fraud=1` in simulation or `takeover_flagged` in production: share of attempts that have `recovery_completed`=0 |
| Support contacts / attempt | Helpdesk tickets linked to `user_id` / `attempt_id` after `recovery_started` |
| Time to complete | `timestamp(recovery_completed) − timestamp(recovery_started)` among completers |

## Must not break

| Mistake | Why it breaks the test |
|---|---|
| `variant` missing on later events (such as `recovery_completed` or `takeover_flagged`) | if one variant loses more rows in the join -> biased rate, we cannot trust the comparison |
| `step_shown` starts several times (re-render / back) | Flow looks worse than reality, might be worse in treatment because of the new feature |
| Assign at `step_shown` | People who quit before the phone verification page never enter the test, in this case we would measure only those people who stayed long enough to reach the phone page. |
| Re-assign or hash differently by platform | Same attempt has different variants, SRM and effects are not trustworthy |