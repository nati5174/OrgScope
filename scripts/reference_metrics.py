"""Independent oracle: walk each raw employee's ancestors; no production imports.

Salary arithmetic uses Decimal, not floating point. Suitable for the balanced
40k input; intentionally not a bottom-up aggregate implementation.
"""
import csv
import json
import sys
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

path = Path(sys.argv[1])
with path.open(encoding='utf-8-sig', newline='') as file:
    records = list(csv.DictReader(file))
if len(sys.argv) == 4:
    moving, destination = sys.argv[2:]
    for row in records:
        if row['Employee Id'] == moving:
            row['Manager'] = destination
employees = {row['Employee Id']: row for row in records}
assert len(employees) == len(records), 'duplicate IDs'
reports = Counter(row['Manager'] for row in records if row['Manager'])
fields = ['descendantCount', 'nonLeafDescendantCount', 'managementCostMinor', 'icCostMinor', 'totalCostMinor']
metrics = {id: dict.fromkeys(fields, 0) for id in employees}
depth = {}
for row in records:
    salary = int((Decimal(row['Salary']) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    manager = row['Manager']
    seen = {row['Employee Id']}
    steps = 0
    while manager:
        assert manager in employees, 'missing manager'
        assert manager not in seen, 'cycle or duplicate in subtree'
        seen.add(manager)
        target = metrics[manager]
        target['descendantCount'] += 1
        target['nonLeafDescendantCount'] += int(reports[row['Employee Id']] > 0)
        target['managementCostMinor' if reports[row['Employee Id']] else 'icCostMinor'] += salary
        target['totalCostMinor'] += salary
        manager = employees[manager]['Manager']
        steps += 1
    depth[row['Employee Id']] = steps
json.dump({'metrics': metrics, 'directReports': reports, 'depth': depth,
           'parents': {r['Employee Id']: r['Manager'] or None for r in records},
           'roots': [r['Employee Id'] for r in records if not r['Manager']],
           'headcount': len(records), 'totalSalaryMinor': sum(int((Decimal(r['Salary']) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP)) for r in records)}, sys.stdout)
