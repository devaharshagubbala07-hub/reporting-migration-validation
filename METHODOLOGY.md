# Audit rules and limits

## Comparison grain

The business key is `(metric, period, plan, cohort)`. The baseline contains six metrics, two incurred calendar years, two plans, and two enrollment cohorts: 48 rows. The cohorts are nested in the generator: the continuously enrolled cohort is a subset of all enrolled members. The seed is `20260921`.

The target introduces eight review cases and four rounding differences. One row is missing, one is duplicated, one extra period is present, three keys have changed definitions, one value is nonnumeric, and one value exceeds tolerance. Duplicates are counted as source/target rows but yield one audit result per business key.

## Comparison sequence

1. Verify nonempty key fields, then use the union of source and target keys. Missing and unexpected keys cannot vanish in an inner join.
2. Count duplicates before joining values. A non-unique key has no comparable single value; all duplicate values are withheld and the key needs review. There is no arbitrary “keep first” rule.
3. Require a metric policy and complete definition fields: unit, time basis, denominator, and filters. Compare these exact documented values and check units against the policy.
4. Require finite, nonnegative numeric values. Member-month values must be integers. These are domain rules for the six selected metrics, not general rules for every financial dataset.
5. Use exact decimal subtraction. Pass if `abs(target − source) <= absolute_tolerance`; equality at the threshold passes.

If any definition gate fails, the numerical delta is withheld because the values are not established as comparable. Every reason found at the applicable gate is retained; the first reason supplies the display status.

## Tolerances

| Metric | Unit | Absolute tolerance |
|---|---|---:|
| Allowed cost | USD | 0.01 |
| Member-months | member-months | 0 |
| PMPM | USD/member/month | 0.01 |
| Members with an episode | percent | 0.01 percentage points |
| Admissions rate | admissions/1,000 members | 0.1 |
| Risk score | score | 0.001 |

These are illustrative project policies, not vendor or industry standards. In real work, agree them with report owners before running the comparison. The optional relative change is descriptive; it does not control pass/fail. A zero source value has no relative percentage but still receives the absolute comparison.

## Reconciliation

Four checks confirm one result per union key, source row counts, target row counts, and the partition into passed/review keys. Eight unit tests cover inclusive decimal boundaries, definition changes despite equal numbers, duplicates on both sides, missing/unexpected keys, zero baselines, invalid numbers, unit/policy requirements, and the composite key.

## Limits

Exact metadata matching can flag differently worded but equivalent definitions; it cannot discover undisclosed calculation changes or errors shared by both systems. The fixture does not model benchmark availability, late claims, risk adjustment, privacy restrictions, or clinical validity. The generated population and values are fictional. This is a reproducible review workflow, not proof of production accuracy.
