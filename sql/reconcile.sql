-- Reconcile the union of business keys. Never join duplicate rows into a fan-out.
WITH source_counts AS (
    SELECT metric, period, plan, cohort, COUNT(*) AS source_count
    FROM source_snapshot GROUP BY metric, period, plan, cohort
), target_counts AS (
    SELECT metric, period, plan, cohort, COUNT(*) AS target_count
    FROM target_snapshot GROUP BY metric, period, plan, cohort
), keys AS (
    SELECT metric, period, plan, cohort FROM source_counts
    UNION
    SELECT metric, period, plan, cohort FROM target_counts
), source_unique AS (
    SELECT s.* FROM source_snapshot s
    JOIN source_counts c USING (metric, period, plan, cohort)
    WHERE c.source_count = 1
), target_unique AS (
    SELECT t.* FROM target_snapshot t
    JOIN target_counts c USING (metric, period, plan, cohort)
    WHERE c.target_count = 1
)
SELECT k.*, COALESCE(sc.source_count, 0) AS source_count,
       COALESCE(tc.target_count, 0) AS target_count,
       s.value AS source_value, t.value AS target_value,
       s.unit AS source_unit, t.unit AS target_unit,
       s.time_basis AS source_time_basis, t.time_basis AS target_time_basis,
       s.denominator AS source_denominator, t.denominator AS target_denominator,
       s.filters AS source_filters, t.filters AS target_filters
FROM keys k
LEFT JOIN source_counts sc USING (metric, period, plan, cohort)
LEFT JOIN target_counts tc USING (metric, period, plan, cohort)
LEFT JOIN source_unique s USING (metric, period, plan, cohort)
LEFT JOIN target_unique t USING (metric, period, plan, cohort)
ORDER BY k.metric, k.period, k.plan, k.cohort;
