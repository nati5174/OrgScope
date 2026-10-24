"""Verify workspace navigation while a real 100k worker import is pending."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

results = []
with sync_playwright() as p:
    for name in ['chromium','firefox','webkit']:
        browser = getattr(p,name).launch(headless=True)
        page = browser.new_page(viewport={'width':1440,'height':900})
        page.goto('http://127.0.0.1:4173/')
        page.get_by_role('button',name='Explore Giga Corp',exact=True).click()
        expect(page.locator('article')).to_have_count(5)
        csv = Path('data/audit/performance-100000.csv').read_text()
        pending = page.evaluate('''csv=>new Promise(resolve=>{
          const input=document.querySelector('input[type=file]'), transfer=new DataTransfer();
          transfer.items.add(new File([csv],'background-100k.csv',{type:'text/csv'}));
          input.files=transfer.files;
          input.dispatchEvent(new Event('change',{bubbles:true}));
          setTimeout(()=>{
            const pending=input.disabled;
            const retained=document.querySelector('header').textContent.includes('40,000 employees validated');
            [...document.querySelectorAll('button')].find(b=>b.textContent==='Workforce Analytics').click();
            requestAnimationFrame(()=>resolve({pending,retained,
              navigated:[...document.querySelectorAll('button')].some(b=>b.textContent==='Workforce Analytics'&&b.getAttribute('aria-current')==='page')}));
          },10);
        })''',csv)
        assert pending == {'pending':True,'retained':True,'navigated':True}, pending
        expect(page.locator('main > p')).to_contain_text('background-100k.csv',timeout=30000)
        expect(page.get_by_role('region',name='Team headcount',exact=True)).to_contain_text('100,000')
        page.locator('input[type=file]').set_input_files({'name':'invalid.csv','mimeType':'text/csv','buffer':b'invalid'})
        expect(page.get_by_role('alert')).to_be_visible()
        expect(page.get_by_role('region',name='Team headcount',exact=True)).to_contain_text('100,000')
        results.append({'browser':name,**pending,'atomicReplaceAndInvalidRetention':'PASS'})
        browser.close()
Path('data/audit/followup/background-import.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results))
