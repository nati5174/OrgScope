"""Browser interaction and layout regressions for the redesigned explorer.

Requires Python Playwright + installed Chromium; run against localhost:5173.
"""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

OUTPUT = Path(os.environ.get('QA_OUTPUT_DIR', str(Path(__file__).resolve().parents[1] / 'data' / 'redesign')))
OUTPUT.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser = getattr(p, os.environ.get('QA_BROWSER', 'chromium')).launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(os.environ.get('AUDIT_BASE_URL', 'http://localhost:5173/'))
    page.get_by_role('button', name='Explore Giga Corp', exact=True).click()
    explorer = page.get_by_role('region', name='Organization explorer', exact=True)
    world = explorer.locator('.chart-world')
    inspector = explorer.get_by_role('complementary', name='Employee details', exact=True)
    expect(explorer.locator('article')).to_have_count(5)
    expect(inspector).to_contain_text('39,999')
    expect(inspector).to_contain_text('$5,009,392,000')
    expect(explorer.locator('[data-nav-row="GC000001"]')).to_have_attribute('aria-selected', 'true')

    def geometry():
        # Layout coordinates are scale independent. Inspect actual rendered boxes.
        return explorer.locator('article').evaluate_all('''cards => {
          const boxes = cards.map(c => c.getBoundingClientRect());
          for (let i=0;i<boxes.length;i++) for(let j=i+1;j<boxes.length;j++) {
            const a=boxes[i], b=boxes[j];
            if(a.left < b.right-.1 && a.right > b.left+.1 && a.top < b.bottom-.1 && a.bottom > b.top+.1) return false;
          }
          return true;
        }''')

    def fit():
        explorer.get_by_role('button', name='Fit to view', exact=True).click()
        # Toolbar takes the bottom 45px; every card should remain inside the canvas.
        assert explorer.locator('.org-canvas').evaluate('''canvas => {
          const v=canvas.getBoundingClientRect();
          return [...canvas.querySelectorAll('article')].every(c=>{const r=c.getBoundingClientRect(); return r.left>=v.left-1 && r.right<=v.right+1 && r.top>=v.top-1 && r.bottom<=v.bottom+1;});
        }''')

    assert geometry()
    fit()
    page.screenshot(path=str(OUTPUT / 'after-desktop.png'), full_page=True)
    initial_height = float(world.get_attribute('data-layout-height'))
    timings = []
    for _ in range(3):
        # In-page click through two animation frames, without Playwright transport time.
        timings.append(explorer.locator('[aria-label="Expand reports for GC000002"]').evaluate('''async button => {
          const start=performance.now(); button.click();
          await new Promise(requestAnimationFrame); await new Promise(requestAnimationFrame);
          return performance.now()-start;
        }'''))
        expect(explorer.locator('article')).to_have_count(9)
        assert float(world.get_attribute('data-layout-height')) > initial_height
        assert geometry()
        explorer.get_by_role('button', name='Collapse reports for GC000002', exact=True).click()
        expect(explorer.locator('article')).to_have_count(5)
        assert float(world.get_attribute('data-layout-height')) == initial_height
    # All 24 direct reports can be shown deliberately, with a bounded chart.
    explorer.get_by_label('Reports per page', exact=True).select_option('24')
    explorer.get_by_role('button', name='Expand reports for GC000002', exact=True).click()
    expect(explorer.locator('article')).to_have_count(33)
    assert geometry()
    explorer.get_by_role('button', name='Collapse reports for GC000002', exact=True).click()
    explorer.get_by_label('Reports per page', exact=True).select_option('4')
    # Selection alone must not recalculate the layout or reset expansion.
    revision = world.get_attribute('data-layout-revision')
    explorer.locator('[data-employee="GC000003"]').click()
    expect(inspector).to_contain_text('GC000003')
    expect(explorer.locator('[data-nav-row="GC000003"]')).to_have_attribute('aria-selected', 'true')
    assert world.get_attribute('data-layout-revision') == revision
    # Keyboard hierarchy navigation and selection.
    row = explorer.locator('[data-nav-row="GC000002"]')
    row.focus(); row.press('ArrowRight')
    expect(row).to_have_attribute('aria-expanded', 'true')
    row.press('ArrowDown')
    assert page.locator(':focus').get_attribute('data-nav-row') != 'GC000002'
    row.focus(); row.press('Enter')
    expect(explorer.get_by_role('navigation', name='Reporting breadcrumbs')).to_contain_text('Riley Davis')
    expect(inspector).to_contain_text('GC000002')
    # Deep search reveals its navigator ancestors and puts the result at chart root.
    explorer.get_by_label('Search employees by name or ID').fill('GC040000')
    explorer.get_by_role('button', name='Find', exact=False).filter(has_text='GC040000').click()
    expect(explorer.locator('[data-employee="GC040000"]')).to_have_count(1)
    expect(explorer.locator('[data-nav-row="GC040000"]')).to_have_attribute('aria-selected', 'true')
    expect(inspector).to_contain_text('GC040000')
    expect(explorer.get_by_role('navigation', name='Reporting breadcrumbs')).to_contain_text('Organization')
    explorer.get_by_role('button', name='Up one level', exact=False).click()
    explorer.get_by_role('button', name='Organization', exact=True).click()
    # Earlier department expansion is preserved when leaving/returning to scope.
    expect(explorer.get_by_role('button', name='Collapse reports for GC000002', exact=True)).to_be_visible()
    explorer.get_by_role('button', name='Collapse all', exact=True).click()
    expect(explorer.locator('article')).to_have_count(1)
    explorer.get_by_role('button', name='Expand reports for GC000001', exact=True).click()
    fit()
    old_scale = float(world.get_attribute('data-scale'))
    explorer.get_by_role('button', name='Zoom in', exact=True).click()
    assert float(world.get_attribute('data-scale')) > old_scale
    explorer.get_by_role('button', name='Zoom out', exact=True).click()
    explorer.get_by_role('button', name='Reset view', exact=True).click()
    assert float(world.get_attribute('data-scale')) == 1
    transform = world.evaluate('(e) => e.style.transform')
    canvas = explorer.locator('.org-canvas'); bounds = canvas.bounding_box()
    page.mouse.move(bounds['x'] + 15, bounds['y'] + 90)
    page.mouse.down(); page.mouse.move(bounds['x'] + 100, bounds['y'] + 140); page.mouse.up()
    assert world.evaluate('(e) => e.style.transform') != transform
    canvas.focus(); transform = world.evaluate('(e) => e.style.transform'); canvas.press('ArrowRight')
    assert world.evaluate('(e) => e.style.transform') != transform
    fit()
    # Expand several branches; chart remains bounded, navigator remains virtualized.
    explorer.get_by_label('Reports per page', exact=True).select_option('24')
    for _ in range(9):
        buttons = explorer.locator('article button[aria-label^="Expand reports"]')
        if not buttons.count(): break
        buttons.first.evaluate('(e) => e.click()')
    assert explorer.locator('article').count() <= 150
    assert explorer.locator('[data-nav-row]').count() < 40
    assert geometry()
    explorer.get_by_role('button', name='Collapse all', exact=True).click()
    explorer.get_by_label('Reports per page', exact=True).select_option('4')
    explorer.get_by_role('button', name='Expand reports for GC000001', exact=True).click()
    fit()
    # Tablet: drawers are modal, close with Escape, and restore accessible controls.
    page.set_viewport_size({"width": 1024, "height": 900})
    explorer.get_by_role('button', name='Hierarchy', exact=False).filter(has_text='Hierarchy').first.click()
    dialog = page.get_by_role('dialog', name='Hierarchy navigator', exact=True)
    expect(dialog).to_be_visible(); page.keyboard.press('Escape'); expect(dialog).not_to_be_visible()
    fit(); page.screenshot(path=str(OUTPUT / 'after-tablet.png'), full_page=True)
    # Mobile: navigator drawer and inspector sheet; no page overflow.
    page.set_viewport_size({"width": 390, "height": 844})
    explorer.get_by_role('button', name='Reset view', exact=True).click()
    page.screenshot(path=str(OUTPUT / 'after-mobile-chart.png'), full_page=True)
    explorer.get_by_role('button', name='Hierarchy', exact=False).filter(has_text='Hierarchy').first.click()
    dialog.get_by_label('Search employees by name or ID').fill('GC040000')
    dialog.get_by_role('button', name='Find', exact=False).filter(has_text='GC040000').click()
    expect(dialog).not_to_be_visible()
    explorer.get_by_role('button', name='Inspector', exact=True).click()
    sheet = page.get_by_role('dialog', name='Employee inspector', exact=True)
    expect(sheet).to_contain_text('GC040000')
    page.screenshot(path=str(OUTPUT / 'after-mobile-inspector.png'), full_page=True)
    page.keyboard.press('Escape'); expect(sheet).not_to_be_visible()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    # Worst-case 40k-deep navigation virtualizes even an entirely revealed path.
    chain = 'employee_id,manager_id,name,salary,currency\n' + '\n'.join(
        f'E{i},{"E" + str(i-1) if i else ""},Person {i},1,CAD' for i in range(40000))
    page.locator('input[type=file]').set_input_files({"name": "deep.csv", "mimeType": "text/csv", "buffer": chain.encode()})
    expect(page.locator('main > p')).to_contain_text('deep.csv')
    explorer.get_by_role('button', name='Hierarchy', exact=False).filter(has_text='Hierarchy').first.click()
    dialog.get_by_label('Search employees by name or ID').fill('E39999')
    dialog.get_by_role('button', name='Find', exact=False).filter(has_text='E39999').click()
    explorer.get_by_role('button', name='Hierarchy', exact=False).filter(has_text='Hierarchy').first.click()
    expect(dialog.locator('[data-nav-row="E39999"]')).to_have_attribute('aria-selected', 'true')
    assert dialog.locator('[data-nav-row]').count() < 40
    page.keyboard.press('Escape')
    assert not errors, errors
    result = {"dataset": "Synthetic Giga Corp, 40000 employees (original assessment dataset unavailable)",
              "browser": browser.version, "viewport": "1440x1000 desktop; 1024x900 tablet; 390x844 mobile",
              "method": "Three expand clicks measured in-page until two requestAnimationFrame callbacks. Includes DOM update and frame scheduling; excludes Playwright transport. Not a paint-time guarantee.",
              "expand_to_two_frames_ms": timings, "maximum_chart_cards": 150, "navigator_dom_rows_limit_observed": "<40",
              "workflows": "geometry, expand/collapse compaction, full 24-report branch, synchronized selection, keyboard tree, deep search/focus, preserved expansion, fit, zoom, pan, drawers, 40k-chain virtualization", "browser_errors": errors}
    (OUTPUT / 'browser-results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(json.dumps(result))
    browser.close()
