"""Comprehensive visual, accessibility, adversarial, and render QA.

AUDIT_BASE_URL optionally targets a local production preview. No browser downloads.
"""
import json
import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get('AUDIT_BASE_URL', 'http://localhost:5173/')
OUT = Path(os.environ.get('QA_OUTPUT_DIR', 'data/audit'))
OUT.mkdir(parents=True, exist_ok=True)
VIEWPORTS = [(1920, 1080), (1440, 900), (1280, 800), (768, 1024), (390, 844)]
results = {'url': BASE, 'browsers': {}, 'visual': [], 'axe': [], 'consoleErrors': [], 'adversarial': []}

with sync_playwright() as p:
    for name in ['chromium', 'firefox', 'webkit']:
        engine = getattr(p, name)
        if not Path(engine.executable_path).exists():
            results['browsers'][name] = 'SKIPPED: browser binary not installed'
            continue
        browser = engine.launch(headless=True)
        results['browsers'][name] = {'version': browser.version}
        page = browser.new_page()
        page.on('pageerror', lambda error: results['consoleErrors'].append(str(error)))
        for width, height in VIEWPORTS:
            page.set_viewport_size({'width': width, 'height': height})
            page.goto(BASE)
            page.get_by_role('button', name='Explore Giga Corp', exact=True).click()
            explorer = page.get_by_role('region', name='Organization explorer', exact=True)
            expect(explorer.locator('article')).to_have_count(5)

            def capture(state, axe=False):
                page.screenshot(path=str(OUT / f'{name}-{width}x{height}-{state}.png'), full_page=True)
                overflow = page.evaluate('document.documentElement.scrollWidth > innerWidth')
                results['visual'].append({'browser': name, 'viewport': [width, height], 'state': state, 'pageOverflow': overflow})
                assert not overflow, (width, state)
                if axe:
                    page.add_script_tag(path='node_modules/axe-core/axe.min.js')
                    report = page.evaluate('''async()=>{const r=await axe.run();return {violations:r.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>({target:n.target,html:n.html,summary:n.failureSummary}))})),incomplete:r.incomplete.map(v=>({id:v.id,nodes:v.nodes.length})),passes:r.passes.length}}''')
                    results['axe'].append({'browser': name, 'viewport': [width, height], 'state': state, **report})

            capture('initial', True)
            explorer.get_by_role('button', name='Expand reports for GC000002', exact=True).evaluate('(e)=>e.click()')
            capture('expanded')
            # Rapid interaction with a stable root-level manager; final state is collapsed.
            explorer.locator('article[data-card="GC000002"]').evaluate('''async card=>{for(let i=0;i<15;i++){card.querySelector('[aria-expanded]').click();await new Promise(requestAnimationFrame)}}''')
            expect(explorer.locator('article')).to_have_count(5)
            explorer.locator('[data-employee="GC000002"]').evaluate('(e)=>e.click()')
            capture('inspector', True)
            if width < 1280:
                page.keyboard.press('Escape')
                explorer.get_by_role('button', name='Hierarchy', exact=False).first.click()
            capture('navigator', width < 1280)
            # Search nonexistent and duplicate-name records without confusing IDs.
            search = page.get_by_label('Search employees by name or ID')
            search.fill('no-such-person-ever')
            expect(page.get_by_text('No employees found', exact=True)).to_be_visible()
            search.fill('GC040000')
            page.get_by_role('button', name='Find', exact=False).filter(has_text='GC040000').click()
            capture('focus')
            if width < 1280:
                explorer.get_by_role('button', name='Inspector', exact=True).click()
            # Independent reference value for this known leaf: all descendant costs zero.
            inspector = page.get_by_role('complementary', name='Employee details', exact=True)
            expect(inspector).to_contain_text('GC040000')
            for label in ['Management cost', 'IC cost', 'Total descendant cost']:
                expect(inspector.locator('dl > div').filter(has=page.get_by_text(label, exact=True))).to_contain_text('$0')
            if width < 1280:
                inspector.get_by_role('button', name='Close employee inspector').click()
            page.get_by_role('button', name='Workforce Analytics', exact=True).click()
            capture('analytics', True)
            expect(page.get_by_role('region', name='Annual salary cost', exact=True)).to_contain_text('$5,010,042,000')
            expect(page.get_by_role('region', name='Team headcount', exact=True)).to_contain_text('40,000')
            page.get_by_role('button', name='Scenario Planner', exact=True).click()
            capture('planner', True)
            for label, id in [('1. Team or employee to move','GC000002'),('2. New reporting manager','GC000007')]:
                page.get_by_label(label,exact=True).fill(id)
                page.get_by_role('button', name='Select', exact=False).filter(has_text=id).click()
            page.get_by_role('button', name='Preview move', exact=True).click()
            capture('planner-preview', True)
            if width < 1280:
                comparison = page.get_by_role('region', name='Scrollable scenario comparison', exact=True)
                comparison.focus(); comparison.press('ArrowRight')
                page.wait_for_function('(el)=>el.scrollLeft>0', arg=comparison.element_handle())
            # Repeated view changes must not lose the selected employee.
            for _ in range(6):
                page.get_by_role('button', name='Workforce Analytics', exact=True).click()
                page.get_by_role('button', name='Organization Explorer', exact=True).click()
            expect(explorer.locator('[data-employee="GC040000"]')).to_have_count(1)
            # Invalid imports preserve prior valid organization, including selection.
            invalid = [b'', b'employee_id,manager_id,name,salary,currency\na,b,A,1,CAD\nb,a,B,2,CAD',
                       b'employee_id,manager_id,name,salary,currency\na,missing,A,1,CAD',
                       b'employee_id,manager_id,name,salary,currency\na,,A,-1,CAD',
                       b'employee_id,manager_id,name,salary,currency\na,,A,1,CAD\na,,B,2,CAD',
                       b'employee_id,manager_id,name,salary,salary,currency\na,,A,100,200,CAD',
                       b'employee_id,manager_id,name,salary,currency\na,,A,90071992547409.91,CAD\nb,a,B,1,CAD']
            for content in invalid:
                page.locator('input[type=file]').set_input_files({'name':'invalid.csv','mimeType':'text/csv','buffer':content})
                expect(page.locator('input[type=file]')).to_be_enabled()
                expect(page.get_by_role('alert')).to_be_visible()
                expect(explorer.locator('[data-employee="GC040000"]')).to_have_count(1)
            results['adversarial'].append({'browser': name, 'viewport': [width,height], 'rapidToggle': 'PASS', 'nonexistentSearch': 'PASS', 'repeatedViewSwitch': 'PASS', 'invalidImportsRetainData': 'PASS'})
        # Duplicate names and exact decimal UI correctness on a tiny independent fixture.
        page.set_viewport_size({'width':1440,'height':900})
        csv = b'employee_id,manager_id,name,salary,currency\nr,,Same Name,10.10,CAD\na,r,Same Name,20.20,CAD\nb,a,Other,30.30,CAD'
        page.locator('input[type=file]').set_input_files({'name':'decimal.csv','mimeType':'text/csv','buffer':csv})
        expect(page.locator('main > p')).to_contain_text('decimal.csv')
        search = page.get_by_label('Search employees by name or ID'); search.fill('Same Name')
        expect(page.get_by_role('button', name='Find', exact=False)).to_have_count(2)
        page.get_by_role('button', name='Find Same Name (a)', exact=True).click()
        expect(page.get_by_role('complementary', name='Employee details', exact=True).locator('.inspector-profile small')).to_have_text('a')
        expect(page.get_by_role('complementary', name='Employee details', exact=True).locator('dl > div').filter(has=page.get_by_text('IC cost', exact=True))).to_contain_text('$30')
        page.get_by_role('button', name='Workforce Analytics', exact=True).click()
        expect(page.get_by_role('region', name='Annual salary cost', exact=True)).to_contain_text('$61')
        page.emulate_media(reduced_motion='reduce')
        page.get_by_role('button', name='Organization Explorer', exact=True).click()
        assert page.locator('article').first.evaluate('(e)=>getComputedStyle(e).transitionDuration') == '0s'
        # Only / is a product route; view buttons are local state, not URL routes.
        page.reload()
        expect(page.get_by_role('button', name='Explore Giga Corp', exact=True)).to_be_visible()
        results['browsers'][name]['refreshAndReducedMotion'] = 'PASS'
        browser.close()
OUT.joinpath('browser-audit.json').write_text(json.dumps(results, indent=2), encoding='utf8')
print(json.dumps({'screenshots': len(results['visual']), 'axeScans': len(results['axe']), 'axeViolationInstances': sum(len(r['violations']) for r in results['axe']), 'browserErrors': results['consoleErrors'], 'browsers': results['browsers']}))
assert not results['consoleErrors']
assert sum(len(scan['violations']) for scan in results['axe']) == 0, 'Accessibility violations remain; inspect browser-audit.json'
