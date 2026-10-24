"""Browser smoke check against the running local Vite server."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

with sync_playwright() as p:
    browser = getattr(p, os.environ.get('QA_BROWSER', 'chromium')).launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(os.environ.get('AUDIT_BASE_URL', 'http://localhost:5173/'))
    page.get_by_role('button', name='Explore Giga Corp', exact=True).click()
    page.get_by_role('button', name='Workforce Analytics', exact=True).click()
    expect(page.get_by_role('heading', name='See where your organization invests.')).to_be_visible()
    expect(page.get_by_role('region', name='Team headcount', exact=True)).to_contain_text('40,000')
    expect(page.get_by_role('region', name='Annual salary cost', exact=True)).to_contain_text('$5,010,042,000')
    page.get_by_role('region', name='Branch cost concentration').get_by_role('button').filter(has_text='GC000007').click()
    expect(page.get_by_role('region', name='Team headcount', exact=True)).to_contain_text('16,325')
    expect(page.get_by_role('navigation', name='Analytics scope breadcrumbs')).to_contain_text('GC000007')
    page.get_by_role('button', name='Explore this team').click()
    expect(page.get_by_role('complementary', name='Employee details')).to_contain_text('GC000007')
    page.get_by_role('button', name='Analyze this team', exact=True).click()
    expect(page.get_by_role('region', name='Team headcount', exact=True)).to_contain_text('16,325')
    page.get_by_role('button', name='Entire organization', exact=True).click()
    output = Path(os.environ.get('QA_OUTPUT_DIR', str(Path(__file__).resolve().parents[1] / 'data')))
    page.screenshot(path=str(output / 'analytics-desktop.png'), full_page=True)
    page.set_viewport_size({"width": 390, "height": 844})
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    page.screenshot(path=str(output / 'analytics-mobile.png'), full_page=True)
    page.get_by_label('Choose analytics team by name or ID').fill('GC040000')
    page.get_by_role('button').filter(has_text='GC040000').click()
    expect(page.get_by_role('region', name='Team headcount', exact=True)).to_contain_text('1')
    expect(page.get_by_role('region', name='Branch cost concentration')).to_contain_text('no direct reports')
    expect(page.get_by_role('region', name='Span of control', exact=True)).to_contain_text('No managers')
    # Empty costs, multiple roots, and a >10-branch page using tiny imported files.
    csv = 'employee_id,manager_id,name,salary,currency\n'
    page.locator('input[type=file]').set_input_files({"name": "zero.csv", "mimeType": "text/csv", "buffer": (csv + 'zero,,Zero,0,CAD').encode()})
    expect(page.get_by_role('region', name='Annual salary cost', exact=True)).to_contain_text('$0')
    expect(page.get_by_role('region', name='Average span of control', exact=True)).to_contain_text('N/A')
    forest = csv + '\n'.join(f'{i},,Root {i},{i},CAD' for i in range(12))
    page.locator('input[type=file]').set_input_files({"name": "forest.csv", "mimeType": "text/csv", "buffer": forest.encode()})
    expect(page.get_by_role('region', name='Team headcount', exact=True)).to_contain_text('12')
    expect(page.get_by_role('button', name='Next branches', exact=True)).to_be_enabled()
    page.get_by_role('button', name='Next branches', exact=True).click()
    expect(page.get_by_role('region', name='Branch cost concentration')).to_contain_text('Page 2 / 2')
    assert not errors, errors
    print(json.dumps({"desktop": "passed", "scope_and_navigation": "passed", "leaf_zero_salary_and_forest": "passed", "mobile_no_page_overflow": True, "browser_errors": errors}))
    browser.close()
