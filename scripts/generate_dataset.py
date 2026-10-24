"""Generate a deterministic fictional organization; no external data required."""

import csv
import json
import random
from collections import Counter
from pathlib import Path


SEED = 20261023
COUNT = 40_000
ROOT = Path(__file__).resolve().parents[1]
DEPARTMENTS = [
    "Engineering", "Product", "Sales", "Customer Success", "Operations",
    "Finance", "People", "Marketing",
]
FIRST = ["Alex", "Jordan", "Sam", "Taylor", "Morgan", "Casey", "Riley", "Avery",
         "Jamie", "Cameron", "Robin", "Drew", "Quinn", "Reese", "Skyler", "Emery"]
LAST = ["Patel", "Chen", "Smith", "Garcia", "Kim", "Brown", "Wilson", "Singh",
        "Martin", "Lee", "Nguyen", "Davis", "Lopez", "Clark", "Ahmed", "Roy"]


def generate():
    rng = random.Random(SEED)
    rows = []
    depths = []
    children = []
    # A weighted pool produces uneven reporting spans while keeping depth bounded.
    manager_pool = []

    def add(manager, department, title, salary, location):
        index = len(rows)
        rows.append({
            "employee_id": f"GC{index + 1:06d}",
            "manager_id": "" if manager is None else rows[manager]["employee_id"],
            "name": f"{rng.choice(FIRST)} {rng.choice(LAST)}",
            "salary": f"{salary:.2f}",
            "currency": "CAD",
            "department": department,
            "title": title,
            "location": location,
        })
        depths.append(0 if manager is None else depths[manager] + 1)
        children.append([])
        if manager is not None:
            children[manager].append(index)
        return index

    add(None, "Executive", "Chief Executive Officer", 650000, "Toronto")
    for department in DEPARTMENTS:
        i = add(0, department, f"VP, {department}", rng.randrange(240000, 340001, 1000), "Toronto")
        manager_pool.extend([i] * 5)

    locations = ["Toronto", "Vancouver", "Montreal", "Ottawa", "Remote"]
    for index in range(len(rows), COUNT):
        manager = rng.choice(manager_pool)
        department = rows[manager]["department"]
        depth = depths[manager] + 1
        # Reserve management roles early enough that they can receive later reports.
        potential_manager = depth < 8 and index < COUNT * 0.8 and rng.random() < 0.23
        salary = rng.randrange(65000, 165001, 500)
        if potential_manager:
            title = f"{'Director' if depth <= 2 else 'Manager'}, {department}"
            salary = rng.randrange(145000, 235001, 1000)
        else:
            title = f"{rng.choice(['Associate', 'Specialist', 'Senior Specialist', 'Lead'])}, {department}"
        i = add(manager, department, title, salary, rng.choice(locations))
        if potential_manager:
            manager_pool.extend([i] * rng.randint(1, 4))
        # Bound large teams without assuming every manager has the same span.
        if len(children[manager]) >= 24:
            manager_pool[:] = [m for m in manager_pool if m != manager]

    # A role selected as a potential manager may never receive reports.
    for i, reports in enumerate(children):
        if not reports and rows[i]["title"].startswith(("Manager,", "Director,")):
            rows[i]["title"] = f"Principal Specialist, {rows[i]['department']}"

    ids = {row["employee_id"] for row in rows}
    assert len(ids) == COUNT
    assert sum(not row["manager_id"] for row in rows) == 1
    assert all(not r["manager_id"] or r["manager_id"] in ids for r in rows)
    # Every edge points to an earlier row, proving the generated graph is acyclic.
    assert all(int(r["manager_id"][2:]) < int(r["employee_id"][2:]) for r in rows[1:])
    assert sum(map(len, children)) == COUNT - 1

    output = ROOT / "data"
    output.mkdir(exist_ok=True)
    target = output / "giga-corp-synthetic-40000.csv"
    with target.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    salaries = [int(float(row["salary"])) for row in rows]
    management_salary = sum(s for s, reports in zip(salaries, children) if reports)
    total_salary = sum(salaries)
    summary = {
        "synthetic": True, "seed": SEED, "employees": COUNT,
        "roots": 1, "managers": sum(bool(c) for c in children),
        "individual_contributors": sum(not c for c in children),
        "max_depth_edges": max(depths), "max_direct_reports": max(map(len, children)),
        "currency": "CAD", "annual_salary_total_including_ceo": total_salary,
        "annual_management_salary_including_ceo": management_salary,
        "annual_ic_salary": total_salary - management_salary,
        "ceo_descendant_count": COUNT - 1,
        "ceo_non_leaf_descendant_count": sum(bool(c) for c in children) - 1,
        "ceo_descendant_management_cost": management_salary - salaries[0],
        "ceo_descendant_ic_cost": total_salary - management_salary,
        "ceo_descendant_total_cost": total_salary - salaries[0],
        "department_headcounts": dict(Counter(r["department"] for r in rows)),
    }
    (output / "synthetic-summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    generate()
