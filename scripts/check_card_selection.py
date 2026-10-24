"""Real pointer hit-testing, selection traces and control isolation regressions.

QA_STAGE=before records failures without stopping at the first mismatch.
No component calls, DOM click dispatch, click retries or arbitrary sleeps.
"""
import csv
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

stage = os.environ.get('QA_STAGE', 'after')
out = Path('data/audit/card-selection')
out.mkdir(parents=True, exist_ok=True)
names = {r['employee_id']:r['name'] for r in csv.DictReader(Path('data/giga-corp-synthetic-40000.csv').open(encoding='utf-8-sig'))}
results = []
failures = []
if os.environ.get('QA_BROWSERS') and (out/f'{stage}-results.json').exists():
    previous=json.loads((out/f'{stage}-results.json').read_text())
    results=previous['results'];failures=previous['failures']
with sync_playwright() as p:
    for engine in os.environ.get('QA_BROWSERS','chromium,firefox,webkit').split(','):
        browser = getattr(p, engine).launch()
        page = browser.new_page(viewport={'width':1920,'height':1200})
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(os.environ.get('AUDIT_BASE_URL','http://127.0.0.1:4173/'))
        page.get_by_role('button',name='Explore Giga Corp',exact=True).click()
        expect(page.locator('article')).to_have_count(5)
        page.evaluate('''()=>{
          window.selectionTrace=[];
          const snapshot=()=>({selected:[...document.querySelectorAll('article.is-selected')].map(e=>e.dataset.card),
            inspector:document.querySelector('.inspector-profile small')?.textContent,
            heading:document.querySelector('.inspector-profile h2')?.textContent,
            navigator:[...document.querySelectorAll('[data-nav-row][aria-selected="true"]')].map(e=>e.dataset.navRow)});
          for(const type of ['pointerdown','pointermove','pointerup','click','gotpointercapture','lostpointercapture'])
            document.addEventListener(type,e=>window.selectionTrace.push({type,time:performance.now(),
              target:e.target.tagName,classes:e.target.getAttribute('class'),
              card:e.target.closest('[data-card]')?.dataset.card,button:e.target.closest('button')?.getAttribute('aria-label'),
              x:e.clientX,y:e.clientY,dragging:document.querySelector('.org-canvas').classList.contains('dragging'),...snapshot()}),true);
          new MutationObserver(()=>window.selectionTrace.push({type:'selection/inspector mutation',time:performance.now(),...snapshot()}))
            .observe(document.querySelector('[aria-label="Organization explorer"]'),{subtree:true,attributes:true,childList:true,characterData:true});
        }''')
        world = page.locator('.chart-world')
        canvas = page.locator('.org-canvas')
        checks = []
        ids = ['GC000004','GC000002','GC000001','GC000003','GC000005']

        def state():
            return page.evaluate('''()=>({ids:[...document.querySelectorAll('article.is-selected')].map(e=>e.dataset.card),
              pressed:[...document.querySelectorAll('[data-employee][aria-pressed="true"]')].map(e=>e.dataset.employee),
              heading:document.querySelector('.inspector-profile h2').textContent,
              inspector:document.querySelector('.inspector-profile small').textContent.split(' ')[0],
              navigator:[...document.querySelectorAll('[data-nav-row][aria-selected="true"]')].map(e=>e.dataset.navRow)})''')

        def verify(id, label):
            # Observe Vue's normal update and two frames, never repeat the input.
            page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
            actual = state()
            ok = actual == {'ids':[id],'pressed':[id],'heading':names[id],'inspector':id,'navigator':[id]}
            checks.append({'label':label,'expected':id,'actual':actual,'passed':ok})
            if not ok: failures.append({'browser':engine,**checks[-1]})

        def click_card(id, area, label):
            card = page.locator(f'article[data-card="{id}"]')
            box = card.bounding_box()
            x,y = {'header':(.50,.25),'center':(.50,.50),'stats':(.50,.60),'padding':(.97,.62),'footer-space':(.50,.88)}[area]
            px,py = round(box['x']+box['width']*x),round(box['y']+box['height']*y)
            target = page.evaluate('''([x,y])=>{const e=document.elementFromPoint(x,y);return {card:e?.closest('[data-card]')?.dataset.card,button:!!e?.closest('button'),tag:e?.tagName}}''',[px,py])
            assert target['card']==id, (label,id,target,box)
            if area not in ['header','center']: assert not target['button'], (area,target)
            transform,revision = world.get_attribute('style'),world.get_attribute('data-layout-revision')
            page.mouse.click(px,py)
            verify(id,label+'/'+area)
            assert world.get_attribute('style')==transform, 'Card click panned or zoomed the canvas'
            if world.get_attribute('data-layout-revision')!=revision:
                (out/f'{stage}-{engine}-layout-diagnostic.json').write_text(json.dumps({'label':label,'area':area,'id':id,'target':target,'beforeRevision':revision,'afterRevision':world.get_attribute('data-layout-revision'),'checks':checks,'trace':page.evaluate('window.selectionTrace')},indent=2))
                raise AssertionError('Selection recomputed layout; see layout-diagnostic.json')
            assert 'dragging' not in canvas.get_attribute('class')

        def series(label):
            page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
            # Every initial card, every selectable surface; always start elsewhere.
            for area in ['header','center','stats','padding','footer-space']:
                for id in ids: click_card(id,area,label)
            # Alternating genuine pointers, no wait between clicks beyond assertions.
            for i in range(32): click_card(ids[i%4],['header','center','stats','padding'][i%4],label+'/alternate')

        series('default-native-scale')
        for _ in range(5): page.get_by_role('button',name='Zoom out',exact=True).click()
        # Five steps are ~50%; control-wheel reaches approximately 47% from native.
        page.get_by_role('button',name='Reset view',exact=True).click()
        cb = canvas.bounding_box()
        page.mouse.move(cb['x']+15,cb['y']+80)
        page.keyboard.down('Control')
        for _ in range(8): page.mouse.wheel(0,1)
        page.keyboard.up('Control')
        page.wait_for_function('Math.abs(+document.querySelector(".chart-world").dataset.scale - Math.pow(1/1.1,8))<.0001')
        series('47-percent')
        # Empty-canvas click retains selection; small and intentional drags still pan.
        for dx,dy in [(1,1),(45,25)]:
            cb=canvas.bounding_box(); x,y=cb['x']+12,cb['y']+95
            assert page.evaluate('([x,y])=>!document.elementFromPoint(x,y).closest("article,button")',[x,y])
            previous=state(); transform=world.get_attribute('style')
            page.mouse.click(x,y)
            assert state()==previous
            page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+dx,y+dy,steps=4);page.mouse.up()
            assert world.get_attribute('style')!=transform
            assert state()==previous
        series('after-pan-and-empty-click')
        # Expand/collapse controls act independently of selection.
        click_card('GC000003','header','control-setup')
        page.get_by_role('button',name='Expand reports for GC000002',exact=True).click()
        expect(page.locator('article')).to_have_count(9)
        verify('GC000003','expand-does-not-select-manager')
        page.get_by_role('button',name='Collapse reports for GC000002',exact=True).click()
        expect(page.locator('article')).to_have_count(5)
        verify('GC000003','collapse-does-not-select-manager')
        series('after-expand-collapse')
        page.get_by_role('button',name='Next reports for GC000001',exact=True).click()
        expect(page.locator('article[data-card="GC000002"]')).to_have_count(0)
        verify('GC000001','pagination-selection')
        new_ids=page.locator('article').evaluate_all('(cards)=>cards.map(c=>c.dataset.card)')
        for id in new_ids: click_card(id,'center','second-page')
        page.get_by_role('button',name='Previous reports for GC000001',exact=True).click()
        page.get_by_role('button',name='Focus on Riley Davis',exact=True).click()
        verify('GC000002','focus-control')
        expect(page.get_by_role('navigation',name='Reporting breadcrumbs')).to_contain_text('Riley Davis')
        page.get_by_role('button',name='Fit to view',exact=True).click()
        focused_ids=page.locator('article').evaluate_all('(cards)=>cards.map(c=>c.dataset.card)')
        for id in focused_ids: click_card(id,'stats','focused-team')
        page.get_by_role('button',name='Organization',exact=True).click()
        page.get_by_role('button',name='Fit to view',exact=True).click()
        series('explicit-fit')
        # Main selection button remains a native keyboard target, not a nested button.
        main = page.locator('[data-employee="GC000002"]')
        main.focus();main.press('Enter');verify('GC000002','native-button-enter')
        page.locator('[data-employee="GC000003"]').focus();page.keyboard.press('Space');verify('GC000003','native-button-space')
        row=page.locator('[data-nav-row="GC000004"]');row.focus();row.press('Enter');verify('GC000004','navigator-enter')
        # Repeat on the shorter desktop viewport from manual reproduction.
        page.get_by_role('button',name='Organization',exact=True).click()
        page.set_viewport_size({'width':1440,'height':900})
        page.get_by_role('button',name='Fit to view',exact=True).click()
        series('short-desktop-fit')
        if stage == 'after':
            page.get_by_role('button',name='Collapse all',exact=True).click()
            page.get_by_role('button',name='Expand reports for GC000001',exact=True).click()
            page.get_by_role('button',name='Reset view',exact=True).click()
            # Partially clipped cards in the actual 1440x900 default camera.
            for id in ids:
                point = page.locator(f'article[data-card="{id}"]').evaluate('''card=>{
                  const r=card.getBoundingClientRect(),v=document.querySelector('.org-canvas').getBoundingClientRect();
                  for(const f of [.25,.5,.6,.88]){
                    const x=Math.round(r.x+r.width*.5),y=Math.round(r.y+r.height*f);
                    const e=document.elementFromPoint(x,y);
                    if(x>v.x&&x<v.right&&y>v.y&&y<v.bottom&&e?.closest('article')===card)
                      return {x,y};
                  }
                  return null;
                }''')
                assert point, f'No visible card surface for {id}'
                transform=world.get_attribute('style')
                page.mouse.click(point['x'],point['y']);verify(id,'short-desktop-native-visible-surface')
                assert world.get_attribute('style')==transform
            page.get_by_role('button',name='Fit to view',exact=True).click()
            box=page.locator('article[data-card="GC000002"]').bounding_box()
            x,y=round(box['x']+box['width']*.5),round(box['y']+box['height']*.6)
            transform=world.get_attribute('style')
            page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+2,y+1);page.mouse.up()
            verify('GC000002','ordinary-pointer-jitter')
            assert world.get_attribute('style')==transform
            # Duplicate display names must still resolve to distinct IDs.
            fixture=b'employee_id,manager_id,name,salary,currency\nr,,Root,10,CAD\na,r,Same Name,20,CAD\nb,r,Same Name,30,CAD'
            page.locator('input[type=file]').set_input_files({'name':'duplicate-names.csv','mimeType':'text/csv','buffer':fixture})
            expect(page.locator('main > p')).to_contain_text('duplicate-names.csv')
            names.update({'r':'Root','a':'Same Name','b':'Same Name'})
            page.get_by_role('button',name='Fit to view',exact=True).click()
            for i in range(32): click_card(['a','b'][i%2],['header','stats','padding','footer-space'][i%4],'duplicate-name-alternation')
        assert not errors,errors
        trace=page.evaluate('window.selectionTrace')
        (out/f'{stage}-{engine}-trace.json').write_text(json.dumps(trace,indent=2))
        result={'browser':engine,'version':browser.version,'checks':checks,'pageErrors':errors}
        results.append(result)
        (out/f'{stage}-results.json').write_text(json.dumps({'results':results,'failures':failures},indent=2))
        print(f'{stage} {engine}: {len(checks)} selection assertions; {sum(not c["passed"] for c in checks)} failures',flush=True)
        browser.close()
assert not failures, f'{len(failures)} one-click selection failures; see {out}/{stage}-results.json'
