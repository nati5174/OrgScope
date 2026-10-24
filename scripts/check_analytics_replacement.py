"""Regression: organization replacement resets analytics page and search state."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

out = Path(os.environ.get('QA_OUTPUT_DIR', 'data/code-quality/final'))
out.mkdir(parents=True, exist_ok=True)
results = []
with sync_playwright() as p:
    for engine in ['chromium', 'firefox', 'webkit']:
        browser = getattr(p, engine).launch()
        page = browser.new_page(viewport={'width': 1440, 'height': 900})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(os.environ.get('AUDIT_BASE_URL', 'http://127.0.0.1:4173/'))
        page.get_by_role('button', name='Explore Giga Corp', exact=True).click()
        expect(page.locator('article')).to_have_count(5)
        page.get_by_role('button', name='Workforce Analytics', exact=True).click()
        header = 'employee_id,manager_id,name,salary,currency\n'
        forest = header + '\n'.join(f'r{i},,Root {i},{i+1},CAD' for i in range(12))
        page.locator('input[type=file]').set_input_files({'name': 'forest.csv', 'mimeType': 'text/csv', 'buffer': forest.encode()})
        expect(page.locator('main > p')).to_contain_text('forest.csv')
        page.get_by_role('button', name='Next branches', exact=True).click()
        branches = page.get_by_role('region', name='Branch cost concentration')
        expect(branches).to_contain_text('Page 2 / 2')
        search = page.get_by_label('Choose analytics team by name or ID')
        search.fill('Root')
        # A rejected replacement must preserve both valid data and local state.
        page.locator('input[type=file]').set_input_files({'name': 'invalid.csv', 'mimeType': 'text/csv', 'buffer': b'invalid'})
        expect(page.get_by_role('alert')).to_be_visible()
        expect(branches).to_contain_text('Page 2 / 2')
        expect(search).to_have_value('Root')
        replacement = header + 'new,,New Root,10,CAD\na,new,A,20,CAD\nb,new,B,30,CAD'
        page.locator('input[type=file]').set_input_files({'name': 'replacement.csv', 'mimeType': 'text/csv', 'buffer': replacement.encode()})
        expect(page.locator('main > p')).to_contain_text('replacement.csv')
        expect(page.get_by_role('region', name='Team headcount', exact=True)).to_contain_text('3')
        rows = branches.locator('tbody tr')
        actual = {'rows': rows.count(), 'query': search.input_value()}
        passed = actual == {'rows': 2, 'query': ''}
        results.append({'browser': engine, 'expected': {'rows': 2, 'query': ''}, 'actual': actual, 'passed': passed, 'pageErrors': errors})
        if passed:
            expect(rows).to_contain_text(['b', 'a'])
            expect(page.get_by_role('region', name='Annual salary cost', exact=True)).to_contain_text('$60')
        browser.close()
        (out / 'analytics-replacement.json').write_text(json.dumps(results, indent=2))
print(json.dumps(results))
assert all(result['passed'] and not result['pageErrors'] for result in results)
