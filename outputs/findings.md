# Findings: fictional reporting migration

An AI-assisted portfolio example. Both snapshots are generated; no employer report definitions or client results are included.

## Audit summary

- 48 source rows and 49 target rows.
- **49 distinct business keys** across the union of snapshots.
- **8 keys need review**; **41 pass** the declared comparisons.
- Passing keys include 4 nonzero differences inside the explicit tolerance.

## Review ledger

| Metric | Period | Plan | Cohort | Issue |
|---|---|---|---|---|
| admissions_per_1000 | 2025 | PPO | All enrolled | definition_mismatch |
| allowed_cost | 2025 | PPO | All enrolled | invalid_value |
| member_months | 2025 | PPO | All enrolled | missing_target |
| member_months | 2026 | PPO | All enrolled | unexpected_target |
| members_with_episode_pct | 2025 | HDHP | All enrolled | definition_mismatch, unit_policy_mismatch |
| members_with_episode_pct | 2025 | PPO | All enrolled | definition_mismatch |
| pmpm | 2025 | PPO | All enrolled | value_mismatch |
| risk_score | 2025 | PPO | All enrolled | duplicate_target |

## Suggested review order

1. Resolve missing and duplicate keys before interpreting totals. Duplicate values are withheld from comparison to avoid an arbitrary row choice or join fan-out.
2. Align units, denominator definitions, time basis, and filter metadata before comparing numbers. Equal values do not prove that definitions agree.
3. Investigate values outside the declared absolute tolerance; never expand the tolerance just to make a discrepancy pass.
4. Re-run the audit and retain the issue ledger for review.

## Interpretation limit

These issues were deliberately injected. Finding them demonstrates the checks on this fixture, not a measured detection rate on real migrations. Definition comparison uses exact documented strings; it cannot inspect an undocumented calculation, validate clinical logic, or detect shared errors in both snapshots. This audit supports review and does not certify a migration.
