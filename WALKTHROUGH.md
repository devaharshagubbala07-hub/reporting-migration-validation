# Explain the migration audit

This project was built with AI assistance. Run, inspect, and modify it before presenting it as evidence of your own SQL/Python ability. It is separate from the professional migration case note in the portfolio.

## A five-minute walkthrough

1. Open the two CSV snapshots and identify the four-field business key.
2. Explain why `sql/reconcile.sql` begins with duplicate counts and a union of keys.
3. Open a definition mismatch whose values are equal. Explain why numerical agreement alone cannot pass it.
4. Read the policy for PMPM, then demonstrate that a difference of exactly 0.01 passes while 0.0101 does not.
5. Show the filtered review ledger and explain the order in which you would investigate the issues.
6. State the limitation: the checks compare documented snapshots; they cannot inspect unknown formulas or certify a migration.

## Questions to practice

- What would an inner join hide?
- How can duplicate keys multiply amounts in a comparison?
- Why is a percentage-point tolerance different from relative percentage change?
- What do you do when the source value is zero?
- When should you change a tolerance—and who should approve the definition in a real project?
- What additional evidence would you need to close a discrepancy?

## Make one change yourself

Add a new fixture case where the target uses a paid-year basis instead of incurred-year, keeping its value unchanged. Confirm it is flagged, explain why, and update the finding. Do not silently expand tolerances to make a test pass.
