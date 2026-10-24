"""Short desktop inspection and real keyboard-event checks in all three engines."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

out = Path('data/audit/followup')
stage = os.environ.get('QA_STAGE', 'before')
results = []
with sync_playwright() as p:
    for name in ['chromium', 'firefox', 'webkit']:
        browser = getattr(p, name).launch(headless=True)
        page = browser.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        for width, height in [(1280,720),(1280,800),(1440,768),(1440,900)]:
            page.set_viewport_size({'width':width,'height':height})
            page.goto('http://127.0.0.1:4173/')
            page.get_by_role('button', name='Explore Giga Corp', exact=True).click()
            expect(page.locator('article')).to_have_count(5)
            page.screenshot(path=str(out/f'{stage}-{name}-{width}x{height}.png'),full_page=True)
            metrics = page.locator('.employee-card-name').first.evaluate('''el=>{
              const scale=+document.querySelector('.chart-world').dataset.scale;
              return {scale,namePixels:parseFloat(getComputedStyle(el).fontSize)*scale,
                cardWidth:el.closest('article').getBoundingClientRect().width,
                pageOverflow:document.documentElement.scrollWidth>innerWidth};
            }''')
            assert not metrics['pageOverflow']
            if stage == 'after':
                assert metrics['namePixels'] >= 10.2
            results.append({'browser':name,'viewport':[width,height],**metrics})
        # Search-result Enter must leave a useful focus target after results unmount.
        search = page.get_by_label('Search employees by name or ID')
        search.fill('GC040000')
        result = page.get_by_role('button',name='Find',exact=False).filter(has_text='GC040000')
        result.focus(); page.keyboard.press('Enter')
        expect(page.locator('[data-nav-row="GC040000"]')).to_have_attribute('aria-selected','true')
        page.wait_for_timeout(100)
        focus = page.evaluate('({tag:document.activeElement.tagName,key:document.activeElement.dataset.navRow})')
        results.append({'browser':name,'searchEnterFocus':focus})
        if stage == 'after':
            assert focus['key'] == 'GC040000', focus
        (out/f'keyboard-readability-{stage}.json').write_text(json.dumps(results,indent=2))
        # Roving tree controls, including Space selection and boundary navigation.
        row = page.locator('[data-nav-row="GC000001"]')
        page.locator('[data-nav-row="GC040000"]').focus(); page.keyboard.press('Home')
        expect(row).to_be_focused()
        page.keyboard.press('ArrowRight'); page.keyboard.press('ArrowDown')
        page.keyboard.press('ArrowLeft'); page.keyboard.press('Home')
        expect(row).to_be_focused()
        page.keyboard.press('End')
        assert page.evaluate('document.activeElement.getAttribute("role")') == 'treeitem'
        page.keyboard.press('Home'); page.keyboard.press('Space')
        expect(row).to_have_attribute('aria-selected','true')
        # Canvas controls from keyboard.
        canvas = page.locator('.org-canvas'); canvas.focus()
        before = page.locator('.chart-world').get_attribute('style')
        page.keyboard.press('ArrowRight')
        assert page.locator('.chart-world').get_attribute('style') != before
        page.keyboard.press('Home')
        page.get_by_role('button',name='Zoom in',exact=True).focus(); page.keyboard.press('Enter')
        # Narrow native-dialog focus trapping and Escape restoration.
        page.set_viewport_size({'width':768,'height':1024})
        hierarchy = page.get_by_role('button',name='Hierarchy',exact=False).first
        expect(hierarchy).to_have_attribute('aria-expanded','false')
        hierarchy.focus(); page.keyboard.press('Enter')
        dialog = page.get_by_role('dialog',name='Hierarchy navigator',exact=True)
        expect(dialog).to_be_visible()
        for key in ['Tab']*12+['Shift+Tab']*12:
            page.keyboard.press(key)
            assert dialog.evaluate('(d)=>document.activeElement===document.body || d.contains(document.activeElement)')
        page.keyboard.press('Escape'); expect(dialog).not_to_be_visible(); expect(hierarchy).to_be_focused()
        inspector = page.get_by_role('button',name='Inspector',exact=True)
        inspector.focus(); page.keyboard.press('Enter')
        dialog = page.get_by_role('dialog',name='Employee inspector',exact=True)
        expect(dialog).to_be_visible()
        for _ in range(15):
            page.keyboard.press('Tab')
            assert dialog.evaluate('(d)=>document.activeElement===document.body || d.contains(document.activeElement)')
        page.keyboard.press('Escape'); expect(inspector).to_be_focused()
        assert not errors, errors
        results.append({'browser':name,'keyboardTreeCanvasDialogs':'PASS','pageErrors':errors})
        (out/f'keyboard-readability-{stage}.json').write_text(json.dumps(results,indent=2))
        browser.close()
print(json.dumps(results))
