"""Repeat browser render/interaction measurements; no network beyond localhost."""
import json
import math
import statistics
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

OUT = Path('data/audit')
FRAMES = 'await new Promise(requestAnimationFrame); await new Promise(requestAnimationFrame);'
results = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for n in [1000, 10000, 40000, 100000]:
        runs = []
        for iteration in range(5):
            page = browser.new_page(viewport={'width':1440,'height':900})
            page.goto('http://localhost:5173/')
            csv = Path('data/giga-corp-synthetic-40000.csv' if n == 40000 else f'data/audit/performance-{n}.csv').resolve()
            # The start event is captured before Vue handles file selection. End is
            # captured in-page after the first matching DOM state plus two frames.
            page.evaluate('''n=>{
              window.__longTasks=[];
              window.__observer=new PerformanceObserver(list=>window.__longTasks.push(...list.getEntries().map(e=>e.duration)));
              window.__observer.observe({type:'longtask',buffered:false});
              window.__loaded=new Promise(resolve=>{
                let start;
                document.querySelector('input[type=file]').addEventListener('change',()=>{start=performance.now()},{once:true,capture:true});
                const observer=new MutationObserver(()=>{
                  if(start && document.querySelector('header').textContent.includes(n.toLocaleString('en-CA')+' employees validated') && document.querySelector('article')){
                    observer.disconnect(); requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(performance.now()-start)));
                  }
                }); observer.observe(document.body,{childList:true,subtree:true,characterData:true});
              });
            }''', n)
            page.locator('input[type=file]').set_input_files(str(csv))
            initial = page.evaluate('()=>window.__loaded')
            long_tasks = page.evaluate('()=>window.__longTasks')
            explorer = page.get_by_role('region', name='Organization explorer', exact=True)
            search = explorer.get_by_label('Search employees by name or ID')
            search_ms = search.evaluate('''async input=>{const start=performance.now(); input.value='no-such-employee'; input.dispatchEvent(new Event('input',{bubbles:true}));''' + FRAMES + '''return performance.now()-start;}''')
            search.fill('')
            expand = explorer.get_by_role('button', name='Expand reports for GC000002', exact=True)
            expand_ms = expand.evaluate('async button=>{const start=performance.now();button.click();' + FRAMES + 'return performance.now()-start;}')
            collapse_ms = explorer.get_by_role('button', name='Collapse reports for GC000002', exact=True).evaluate('async button=>{const start=performance.now();button.click();' + FRAMES + 'return performance.now()-start;}')
            focus_ms = explorer.locator('article[data-card="GC000002"] .card-focus').evaluate('async button=>{const start=performance.now();button.click();' + FRAMES + 'return performance.now()-start;}')
            analytics_ms = page.get_by_role('button', name='Workforce Analytics', exact=True).evaluate('async button=>{const start=performance.now();button.click();' + FRAMES + 'return performance.now()-start;}')
            page.get_by_role('button', name='Scenario Planner', exact=True).click()
            for label, id in [('1. Team or employee to move','GC000002'),('2. New reporting manager','GC000003')]:
                page.get_by_label(label,exact=True).fill(id)
                page.get_by_role('button', name='Select', exact=False).filter(has_text=id).click()
            scenario_ms = page.get_by_role('button', name='Preview move', exact=True).evaluate('async button=>{const start=performance.now();button.click();' + FRAMES + 'return performance.now()-start;}')
            session = page.context.new_cdp_session(page)
            session.send('HeapProfiler.collectGarbage')
            memory = session.send('Runtime.getHeapUsage')
            dom = page.evaluate('document.querySelectorAll("*").length')
            runs.append({'initialRenderMs':initial, 'searchToFramesMs':search_ms, 'expandToFramesMs':expand_ms,
                         'collapseToFramesMs':collapse_ms,'focusToFramesMs':focus_ms,'analyticsToFramesMs':analytics_ms,
                         'scenarioToFramesMs':scenario_ms,'jsHeapAfterGCBytes':memory['usedSize'], 'domNodes':dom,
                         'loadLongTasksMs':long_tasks})
            if n == 40000 and iteration == 4:
                before = memory['usedSize']
                for _ in range(20):
                    page.get_by_role('button', name='Workforce Analytics', exact=True).evaluate('(b)=>b.click()')
                    page.get_by_role('button', name='Organization Explorer', exact=True).evaluate('(b)=>b.click()')
                    page.get_by_role('button', name='Scenario Planner', exact=True).evaluate('(b)=>b.click()')
                    page.get_by_role('button', name='Preview move', exact=True).evaluate('(b)=>b.click()')
                session.send('HeapProfiler.collectGarbage')
                after = session.send('Runtime.getHeapUsage')['usedSize']
                OUT.joinpath('memory-cycle.json').write_text(json.dumps({'cycles':20,'beforeBytes':before,'afterBytes':after,'deltaBytes':after-before,
                    'method':'Same 40k page; cycle analytics/explorer/planner and replace scenario, then explicit Chromium GC. Single observation, not proof of no leak.'},indent=2))
            page.close()
        summary = {}
        for key in runs[0]:
            if key == 'loadLongTasksMs': continue
            values = sorted(run[key] for run in runs)
            summary[key] = {'median':statistics.median(values),'p95':values[math.ceil(.95*len(values))-1]}
        results.append({'employees':n,'runs':runs,'summary':summary})
        print(f'Measured browser {n}',flush=True)
    OUT.joinpath('performance-browser.json').write_text(json.dumps({'browser':browser.version,'viewport':[1440,900],
        'method':'5 runs/size. Initial render: file change event to matching DOM + two animation frames, includes file read/parse/build/render. Other timings: in-page click/input to two frames, excluding automation transport. Not guaranteed paint time. p95 is nearest rank and equals maximum at n=5; weak tail estimate. Memory uses explicit Chromium GC; DOM includes hidden mounted views.', 'results':results},indent=2))
    browser.close()
