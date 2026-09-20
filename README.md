# Reporting migration validation

**[Explore the audit](https://devaharshagubbala07-hub.github.io/projects/migration/)** · [Findings](outputs/findings.md) · [Methodology](METHODOLOGY.md) · [Walkthrough](WALKTHROUGH.md)

An analyst portfolio project that compares two report snapshots before and after a simulated platform change. Built with AI assistance using generated snapshots and deliberately injected discrepancies. It contains no employer data, internal report definitions, or client deliverables.

## The question

Did the report preserve its population, definitions, and values—and which differences need human review?

The audit uses SQL to reconcile the union of business keys, then Python `Decimal` to compare valid, definition-aligned values against explicit metric tolerances. Missing and duplicate records remain visible. Matching numbers do not override changed units, denominators, time basis, or filters.

## Run locally

Python 3.11 or newer. No third-party dependencies.

```bash
python audit.py
python -m unittest discover -s tests -v
```

The generator recreates both snapshots in `data/` and the audit ledger in `outputs/`. The fixture contains **49 distinct keys: 8 need review, 41 pass**, including four nonzero differences within tolerance. These issue counts were constructed for the example; they are not a measured real-world detection rate.

To compare your own non-sensitive snapshots, keep the documented columns and call `reconcile(source_rows, target_rows, policy)` from `audit.py`. The command-line entry point always regenerates the demonstration, so do not overwrite its fixture expecting it to analyze that file automatically.

## Repository guide

| File | Purpose |
|---|---|
| `data/source_snapshot.csv` | Generated baseline report |
| `data/target_snapshot.csv` | Generated target with known discrepancies |
| `policies.json` | Units and absolute tolerances, declared before comparison |
| `sql/reconcile.sql` | Union of keys and duplicate-safe snapshot join |
| `audit.py` | Definition gates, numerical comparison, and export |
| `tests/test_audit.py` | Eight tests of analytical failure cases and boundaries |
| `outputs/audit.csv` | Complete review ledger |
| `outputs/findings.md` | Findings and suggested review order |

The website source is in `dashboard/`. It reads `dashboard/data.json`, which is refreshed automatically when the audit runs. Serve the repository with `python -m http.server 8000` and visit `http://localhost:8000/dashboard/`.

## Intended use

Demonstrate how an analyst structures a migration review: establish comparable definitions, reconcile populations, distinguish harmless rounding from discrepancies, and document unresolved issues. This tool supports review; it does not certify a migration or infer undocumented calculation logic.
