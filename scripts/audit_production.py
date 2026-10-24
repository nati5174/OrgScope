"""Verify the built local production preview, not an external deployment."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width':1440,'height':900})
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    response = page.goto('http://127.0.0.1:4173/')
    assert response.status == 200
    page.get_by_role('button', name='Explore Giga Corp', exact=True).click()
    expect(page.locator('article')).to_have_count(5)
    page.get_by_role('button', name='Expand reports for GC000002', exact=True).click()
    expect(page.locator('article')).to_have_count(9)
    page.get_by_role('button', name='Workforce Analytics', exact=True).click()
    expect(page.get_by_role('region', name='Team headcount', exact=True)).to_contain_text('40,000')
    expect(page.get_by_role('region', name='Annual salary cost', exact=True)).to_contain_text('$5,010,042,000')
    page.get_by_role('button', name='Scenario Planner', exact=True).click()
    for label, id in [('1. Team or employee to move','GC000002'),('2. New reporting manager','GC000007')]:
        page.get_by_label(label, exact=True).fill(id)
        page.get_by_role('button', name='Select', exact=False).filter(has_text=id).click()
    page.get_by_role('button', name='Preview move', exact=True).click()
    expect(page.get_by_role('region', name='Scenario metric comparison')).to_be_visible()
    page.add_script_tag(path='node_modules/axe-core/axe.min.js')
    axe = page.evaluate('async()=>{const r=await axe.run();return {violations:r.violations.map(v=>v.id),passes:r.passes.length,incomplete:r.incomplete.map(v=>v.id)}}')
    result = {'url':'http://127.0.0.1:4173/', 'kind':'Local Vite production preview, NOT an external deployment',
              'httpStatus':response.status, 'sampleAssetAndExplorer':'PASS', 'analyticsIndependentGlobalTotal':'PASS',
              'scenarioPreview':'PASS', 'axe':axe, 'browserErrors':errors, 'publicDeploymentTested':False}
    Path('data/audit/production-preview.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result))
    assert not errors
    assert not axe['violations']
    browser.close()
