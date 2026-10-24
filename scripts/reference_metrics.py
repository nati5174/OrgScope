"""Independent oracle: walk each raw employee's ancestors; no production imports.

Salary arithmetic uses Decimal, not floating point. Suitable for the balanced
40k input; intentionally not a bottom-up aggregate implementation.
"""
import csv
import json
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

path = Path(sys.argv[1])
with path.open(encoding='utf-8-sig', newline='') as file:
    records = list(csv.DictReader(file))
if len(sys.argv) == 4:
    moving, destination = sys.argv[2:]
    for row in records:
        if row['employee_id'] == moving:
            row['manager_id'] = destination
employees = {row['employee_id']: row for row in records}
assert len(employees) == len(records), 'duplicate IDs'
reports = Counter(row['manager_id'] for row in records if row['manager_id'])
fields = ['descendantCount', 'nonLeafDescendantCount', 'managementCostMinor', 'icCostMinor', 'totalCostMinor']
metrics = {id: dict.fromkeys(fields, 0) for id in employees}
depth = {}
for row in records:
    salary = Decimal(row['salary']) * 100
    assert salary == salary.to_integral_value()
    salary = int(salary)
    manager = row['manager_id']
    seen = {row['employee_id']}
    steps = 0
    while manager:
        assert manager in employees, 'missing manager'
        assert manager not in seen, 'cycle or duplicate in subtree'
        seen.add(manager)
        target = metrics[manager]
        target['descendantCount'] += 1
        target['nonLeafDescendantCount'] += int(reports[row['employee_id']] > 0)
        target['managementCostMinor' if reports[row['employee_id']] else 'icCostMinor'] += salary
        target['totalCostMinor'] += salary
        manager = employees[manager]['manager_id']
        steps += 1
    depth[row['employee_id']] = steps
json.dump({'metrics': metrics, 'directReports': reports, 'depth': depth,
           'parents': {r['employee_id']: r['manager_id'] or None for r in records},
           'roots': [r['employee_id'] for r in records if not r['manager_id']],
           'headcount': len(records), 'totalSalaryMinor': sum(int(Decimal(r['salary']) * 100) for r in records)}, sys.stdout)
