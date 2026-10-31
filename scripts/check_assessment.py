"""Browser regressions against the supplied dataset; run production preview first."""
import csv
import io
import json
import os
import subprocess
import sys
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

workspace = Path(__file__).resolve().parent.parent
dataset = workspace / 'data data.csv'
with dataset.open(encoding='utf-8-sig', newline='') as source:
    rows = list(csv.DictReader(source))
reference = json.loads(subprocess.check_output([sys.executable, str(workspace / 'scripts/reference_metrics.py'), str(dataset)], text=True))
people = {row['Employee Id']: row for row in rows}
children = defaultdict(list)
for row in rows:
    children[row['Manager']].append(row['Employee Id'])
root, target = reference['roots'][0], rows[-1]['Employee Id']
manager = next(id for id in children[root] if len(children[id]) > 2)
base = os.environ.get('AUDIT_BASE_URL', 'http://127.0.0.1:4173')
def exact(minor):
    return f'{Decimal(minor) / 100:,.2f}'
def metric(inspector, label):
    return inspector.locator('dl > div').filter(has=inspector.page.get_by_text(label, exact=True)).locator('dd')
def select(page, id):
    page.get_by_label('Search employees by name or ID').fill(id)
    page.get_by_role('button', name=f'Find {people[id]["Name"]} ({id})', exact=True).click()

with sync_playwright() as playwright:
    browser = getattr(playwright, os.environ.get('QA_BROWSER', 'chromium')).launch()
    page = browser.new_page(viewport={'width': 1600, 'height': 1000})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(base)
    page.get_by_role('button', name='Explore Giga Corp', exact=True).click()
    expect(page.get_by_text('40,000 employees validated')).to_be_visible(timeout=60000)
    inspector = page.get_by_role('complementary', name='Employee details')
    expect(inspector).to_contain_text(people[root]['Name'])
    expect(inspector.locator('.inspector-profile')).not_to_contain_text(root)
    expect(inspector.locator('.inspector-profile')).to_contain_text(people[root]['Department'])
    expect(inspector.locator('[data-employee-id]')).to_have_text(root)
    page.evaluate("window.__copiedId = null; Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText: async text => { window.__copiedId = text } } })")
    inspector.get_by_role('button', name='Copy employee ID', exact=True).click()
    expect(inspector.get_by_role('status')).to_have_text('Employee ID copied')
    assert page.evaluate('window.__copiedId') == root
    inspector.get_by_label('Show exact salary amounts').check()
    expected = reference['metrics'][root]
    for label, field in [('Total descendants', 'descendantCount'), ('Non-leaf descendants', 'nonLeafDescendantCount')]:
        expect(metric(inspector, label)).to_have_text(f'{expected[field]:,}')
    for label, field in [('Management cost', 'managementCostMinor'), ('IC cost', 'icCostMinor'), ('Total descendant cost', 'totalCostMinor')]:
        expect(metric(inspector, label)).to_have_text(exact(expected[field]))
    expect(page.locator(f'article[data-card="{root}"]')).to_contain_text(f"{expected['nonLeafDescendantCount']:,} non-leaf")
    for id in [root, *children[root]]:
        card_counts = page.locator(f'article[data-card="{id}"]')
        expect(card_counts).to_contain_text(f"{reference['metrics'][id]['descendantCount']:,} descendants")
        expect(card_counts).to_contain_text(f"{reference['metrics'][id]['nonLeafDescendantCount']:,} non-leaf")
    expect(metric(inspector, 'Management cost ratio')).to_have_text(f"{expected['icCostMinor'] / expected['managementCostMinor']:.2f}")
    card = page.locator(f'article[data-card="{manager}"]')
    before = card.bounding_box()
    page.get_by_role('button', name=f'Expand reports for {manager}', exact=True).evaluate('(button) => button.click()')
    expect(page.locator(f'article[data-card="{children[manager][0]}"]')).to_be_attached()
    after = card.bounding_box()
    assert abs(before['x'] - after['x']) < 2 and abs(before['y'] - after['y']) < 2
    page.get_by_role('button', name=f'Collapse reports for {manager}', exact=True).evaluate('(button) => button.click()')
    after = card.bounding_box()
    assert abs(before['x'] - after['x']) < 2 and abs(before['y'] - after['y']) < 2
    select(page, manager)
    page.get_by_label('Reports per page').select_option('2')
    page.locator(f'article[data-card="{manager}"]').get_by_role('button', name=f'Next reports for {manager}', exact=True).click()
    expect(page.locator(f'article[data-card="{children[manager][2]}"]')).to_be_attached()
    expect(page.locator(f'article[data-card="{children[manager][0]}"]')).to_have_count(0)
    select(page, target)
    expect(inspector).to_contain_text(people[target]['Name'])
    expect(metric(inspector, 'Total descendants')).to_have_text('0')
    expect(metric(inspector, 'Management cost ratio')).to_have_text('N/A')
    page.get_by_role('button', name='Show full path', exact=True).click()
    expect(page.get_by_role('navigation', name='Reporting breadcrumbs').get_by_role('button', name=people[root]['Name'], exact=True)).to_be_visible()
    page.get_by_role('button', name='Organization', exact=True).click()
    expect(inspector).to_contain_text(people[root]['Name'])
    page.get_by_role('button', name='Workforce Analytics', exact=True).click()
    analytics = page.get_by_role('region', name='Workforce analytics')
    analytics.get_by_label('Show exact salary amounts').check()
    expect(analytics.get_by_role('region', name='Annual salary cost')).to_contain_text(exact(reference['totalSalaryMinor']))
    table = analytics.get_by_role('table')
    for sort in ['cost', 'headcount', 'management']:
        analytics.get_by_label('Order branches by').select_option(sort)
        def sort_value(id):
            metrics = reference['metrics'][id]
            salary = int((Decimal(people[id]['Salary']) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
            total = metrics['totalCostMinor'] + salary
            management = metrics['managementCostMinor'] + (salary if children[id] else 0)
            return {'cost': total, 'headcount': metrics['descendantCount'] + 1, 'management': management / total if total else 0}[sort]
        expected_branch = sorted(children[root], key=lambda id: (-sort_value(id), id))[0]
        expect(table.locator('tbody tr').first).to_have_attribute('data-branch', expected_branch)
    table.locator('tbody tr').first.get_by_role('button', name=f'Explore {people[expected_branch]["Name"]} in chart', exact=True).click()
    expect(inspector).to_contain_text(people[expected_branch]['Name'])
    page.get_by_role('button', name='Organization', exact=True).click()
    # Exercise planner validations and reconcile exported metrics independently.
    page.get_by_role('button', name='Scenario Planner', exact=True).click()
    planner = page.get_by_role('region', name='Scenario planner')
    def choose(label, id):
        planner.get_by_label(label, exact=True).fill(id)
        planner.get_by_role('button', name=f'Select {people[id]["Name"]} ({id})', exact=True).click()
    moving_label, destination_label = '1. Team or employee to move', '2. New reporting manager'
    choose(moving_label, root)
    choose(destination_label, target)
    expect(planner.get_by_role('alert')).to_contain_text('descendants')
    expect(planner.get_by_role('button', name='Preview move', exact=True)).to_be_disabled()
    choose(moving_label, children[root][0])
    choose(destination_label, children[root][0])
    expect(planner.get_by_role('alert')).to_be_visible()
    expect(planner.get_by_role('button', name='Preview move', exact=True)).to_be_disabled()
    choose(destination_label, root)
    expect(planner.get_by_role('alert')).to_be_visible()
    expect(planner.get_by_role('button', name='Preview move', exact=True)).to_be_disabled()
    moving, destination = children[root][:2]
    choose(destination_label, destination)
    expect(planner.get_by_role('button', name='Preview move', exact=True)).to_be_enabled()
    planner.get_by_role('button', name='Preview move', exact=True).click()
    expect(planner.get_by_role('region', name='proposed reporting structure')).to_contain_text(people[destination]['Name'])
    with page.expect_download() as download_event:
        planner.get_by_role('button', name='Export preview JSON', exact=True).click()
    exported = json.loads(Path(download_event.value.path()).read_text(encoding='utf-8'))
    assert exported['hypothetical'] is True and exported['destinationId'] == destination
    assert exported['movedEmployee']['id'] == moving
    proposed = json.loads(subprocess.check_output([sys.executable, str(workspace / 'scripts/reference_metrics.py'), str(dataset), moving, destination], text=True))
    assert proposed['headcount'] == reference['headcount']
    assert proposed['totalSalaryMinor'] == reference['totalSalaryMinor']
    for affected in exported['affectedEmployees']:
        assert affected['original'] == reference['metrics'][affected['id']]
        assert affected['proposed'] == proposed['metrics'][affected['id']]
    planner.get_by_role('button', name='Open interactive structure preview', exact=True).click()
    expect(planner.get_by_role('complementary', name='Employee details')).to_contain_text(people[moving]['Name'])
    planner.get_by_label('View', exact=True).select_option('original')
    expect(planner.get_by_role('complementary', name='Employee details')).to_contain_text(people[moving]['Name'])
    choose(destination_label, children[root][2])
    expect(planner.get_by_role('status').filter(has_text='Selections changed')).to_be_visible()
    planner.get_by_role('button', name='Reset scenario', exact=True).click()
    expect(planner.get_by_role('button', name='Export preview JSON', exact=True)).to_have_count(0)
    page.get_by_role('button', name='Organization Explorer', exact=True).click()
    expect(metric(inspector, 'Total descendant cost')).to_have_text(exact(reference['metrics'][root]['totalCostMinor']))
    invalid = dict(rows[0], Manager='missing-assessment-manager')
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(invalid))
    writer.writeheader()
    writer.writerow(invalid)
    page.locator('input[type=file]').set_input_files({'name': 'invalid.csv', 'mimeType': 'text/csv', 'buffer': buffer.getvalue().encode()})
    expect(page.get_by_role('alert')).to_contain_text('Missing manager')
    page.get_by_role('button', name='Retry import', exact=True).click()
    expect(page.get_by_role('alert')).to_contain_text('Missing manager')
    expect(page.get_by_text('40,000 employees validated')).to_be_visible()
    expect(inspector).to_contain_text(people[root]['Name'])
    retry = browser.new_page(viewport={'width': 1600, 'height': 1000})
    retry.on('pageerror', lambda error: errors.append(str(error)))
    retry.route('**/*.csv', lambda route: route.abort(), times=1)
    retry.goto(base)
    retry.get_by_role('button', name='Explore Giga Corp', exact=True).click()
    expect(retry.get_by_role('alert')).to_be_visible()
    retry.get_by_role('button', name='Retry import', exact=True).click()
    expect(retry.get_by_text('40,000 employees validated')).to_be_visible(timeout=60000)
    expect(retry.get_by_role('alert')).to_have_count(0)
    retry.close()
    mobile = browser.new_page(viewport={'width': 390, 'height': 844}, has_touch=True)
    mobile.on('pageerror', lambda error: errors.append(str(error)))
    mobile.goto(base)
    mobile.get_by_role('button', name='Explore Giga Corp', exact=True).click()
    expect(mobile.get_by_text('40,000 employees validated')).to_be_visible(timeout=60000)
    mobile.get_by_role('button', name='Hierarchy', exact=False).click()
    expect(mobile.get_by_role('dialog', name='Hierarchy navigator')).to_be_visible()
    select(mobile, target)
    expect(mobile.get_by_role('dialog', name='Hierarchy navigator')).not_to_be_visible()
    mobile.get_by_role('button', name='Inspector', exact=True).click()
    dialog = mobile.get_by_role('dialog', name='Employee inspector')
    expect(dialog).to_contain_text(people[target]['Name'])
    dialog.get_by_role('button', name='Close employee inspector', exact=True).click()
    mobile.get_by_role('button', name='Organization', exact=True).click()
    mobile.get_by_role('button', name='Zoom in', exact=True).click()
    assert mobile.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    assert not errors, errors
    page.get_by_role('button', name='Workforce Analytics', exact=True).click()
    page.get_by_role('region', name='Workforce analytics').get_by_label('Show exact salary amounts').check()
    page.screenshot(path=str(workspace / 'data/audit/analytics-priorities.png'), full_page=True)
    browser.close()
print('Passed: scenario validation, exported-metric reconciliation, preview/reset and baseline preservation; supplied-data metrics, card counts, camera anchoring, pagination, search, breadcrumbs, analytics sorting/drill-through, import recovery, mobile navigation; no browser errors')
