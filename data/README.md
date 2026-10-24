# Giga Corp — synthetic development dataset

This is fictional test data generated for OrgScope. It is **not** the original
Dayforce/Agentnoon Giga Corp dataset, and its schema has not been verified against
that dataset. Names are randomly combined; any resemblance to people is incidental.

Regenerate from the `dayforce_OA` directory with Python 3 (no dependencies):

```sh
python scripts/generate_dataset.py
```

The CSV contains exactly 40,000 employees with one CEO, eight organizational
branches, uneven team sizes, and up to eight reporting edges below the CEO.
It is deliberately valid: unique IDs, existing managers, no cycles, and
nonnegative salaries. Invalid-input cases should use separate test fixtures.

| Column | Convention |
| --- | --- |
| employee_id | Unique string ID, e.g. GC000001 |
| manager_id | Manager's employee_id; blank for the CEO |
| name | Fictional display name; duplicates are intentional |
| salary | Annual base salary, decimal with two places; excludes benefits/bonus |
| currency | CAD throughout, allowing comparable salary sums |
| department | Synthetic organizational branch; Executive for the CEO |
| title | Fictional role label; determine managers from reports, not titles |
| location | Fictional office assignment or Remote |

The fixed seed makes regeneration reproducible. Rows put managers before reports,
but the application's importer must also support shuffled input. Salary and team
distributions are development assumptions, not claims about real companies.

`synthetic-summary.json` records generated counts and expected CEO descendant-only
metrics for reconciliation. Whole-company salary totals include the CEO; CEO
descendant metrics exclude the CEO. No performance benchmarks are claimed here.

This dataset supports initial development and 40k-row profiling. It does not
replace later verification against the assessment's actual data or tests for
extreme depth, unusually wide teams, CSV quoting, and invalid relationships.
