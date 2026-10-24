"""Optional Playwright browser smoke check for hypothetical planning."""
import json
import os
import re
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

with sync_playwright() as p:
    browser = getattr(p, os.environ.get('QA_BROWSER', 'chromium')).launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(os.environ.get('AUDIT_BASE_URL', 'http://localhost:5173/'))
    page.get_by_role('button', name='Explore Giga Corp', exact=True).click()
    page.get_by_role('button', name='Scenario Planner', exact=True).click()
    planner = page.get_by_role('region', name='Scenario planner', exact=True)

    def choose(label, employee_id):
        planner.get_by_label(label, exact=True).fill(employee_id)
        planner.get_by_role('button', name=re.compile(r'\(' + re.escape(employee_id) + r'\)$')).click()

    expect(planner.get_by_role('button', name='Preview move', exact=True)).to_be_disabled()
    choose('1. Team or employee to move', 'GC000002')
    choose('2. New reporting manager', 'GC000002')
    expect(planner.get_by_role('alert')).to_contain_text('themselves')
    choose('2. New reporting manager', 'GC000001')
    expect(planner.get_by_role('alert')).to_contain_text('already')
    choose('2. New reporting manager', 'GC000007')
    planner.get_by_role('button', name='Preview move', exact=True).click()
    expect(planner.get_by_role('region', name='Scenario metric comparison')).to_be_visible()
    expect(planner.get_by_role('region', name='proposed reporting structure')).to_contain_text('GC000007')
    with page.expect_download() as download_info:
        planner.get_by_role('button', name='Export preview JSON', exact=True).click()
    data = json.loads(Path(download_info.value.path()).read_text(encoding='utf8'))
    assert data['hypothetical'] is True and data['destinationId'] == 'GC000007'
    output = Path(os.environ.get('QA_OUTPUT_DIR', str(Path(__file__).resolve().parents[1] / 'data')))
    page.screenshot(path=str(output / 'scenario-desktop.png'), full_page=True)
    planner.get_by_role('button', name='Open interactive structure preview', exact=True).click()
    expect(planner.get_by_role('complementary', name='Employee details')).to_contain_text('GC000002')
    expect(planner.get_by_role('complementary', name='Employee details')).to_contain_text('Quinn Patel')
    planner.get_by_label('View', exact=True).select_option('original')
    expect(planner.get_by_role('complementary', name='Employee details')).to_contain_text('Jamie Martin')
    # Baseline explorer is not altered by the simulated move.
    page.get_by_role('button', name='Organization Explorer', exact=True).click()
    expect(page.get_by_role('complementary', name='Employee details')).to_contain_text('GC000001')
    page.get_by_role('button', name='Scenario Planner', exact=True).click()
    expect(planner.get_by_role('region', name='proposed reporting structure')).to_contain_text('GC000007')
    planner.get_by_role('button', name='Hide interactive preview', exact=True).click()
    choose('2. New reporting manager', 'GC000009')
    expect(planner.get_by_role('status').filter(has_text='Selections changed')).to_be_visible()
    page.set_viewport_size({"width": 390, "height": 844})
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    page.screenshot(path=str(output / 'scenario-mobile.png'), full_page=True)
    planner.get_by_role('button', name='Reset scenario', exact=True).click()
    expect(planner.get_by_role('region', name='Scenario metric comparison')).to_have_count(0)
    expect(planner.get_by_role('button', name='Preview move', exact=True)).to_be_disabled()
    # Small hierarchy to exercise source demotion, destination promotion, and cycle prevention.
    csv = 'employee_id,manager_id,name,salary,currency\nroot,,Root,900,CAD\na,root,A,200,CAD\nb,root,B,300,CAD\nc,a,C,400,CAD\nd,c,D,500,CAD'
    page.locator('input[type=file]').set_input_files({"name": "scenario.csv", "mimeType": "text/csv", "buffer": csv.encode()})
    expect(page.locator('main > p')).to_contain_text('scenario.csv')
    choose('1. Team or employee to move', 'c')
    # Search names are single letters in this fixture, so choose explicit IDs below.
    choose('2. New reporting manager', 'd')
    expect(planner.get_by_role('alert')).to_contain_text('descendants')
    choose('2. New reporting manager', 'b')
    planner.get_by_role('button', name='Preview move', exact=True).click()
    expect(planner.get_by_role('region', name='Scenario metric comparison')).to_contain_text('0 → 1 reports')
    expect(planner.get_by_role('region', name='Scenario metric comparison')).to_contain_text('1 → 0 reports')
    assert not errors, errors
    print(json.dumps({"valid_invalid_moves": "passed", "preview_and_export": "passed", "baseline_unchanged": "passed", "reset_and_mobile": "passed", "browser_errors": errors}))
    browser.close()
