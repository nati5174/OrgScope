"""Before/after import measurements using identical production-preview fixtures."""
import hashlib
import json
import os
import statistics
from pathlib import Path
from playwright.sync_api import sync_playwright

stage = os.environ.get('QA_STAGE', 'after')
base = os.environ.get('AUDIT_BASE_URL', 'http://127.0.0.1:4173/')
out = Path('data/audit/followup')
out.mkdir(exist_ok=True)
results = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for count in [1000, 10000, 40000, 100000]:
        csv = Path('data/giga-corp-synthetic-40000.csv' if count == 40000 else f'data/audit/performance-{count}.csv').resolve()
        runs = []
        for iteration in range(6):
            page = browser.new_page(viewport={'width':1440,'height':900})
            page.goto(base)
            page.evaluate('''n=>{
              window.__probe=new Promise(resolve=>{
                let started=0,lastTick=0,lastFrame=0,timer,raf;
                const gaps=[],frames=[],longTasks=[];
                const supportsLongTasks=PerformanceObserver.supportedEntryTypes.includes('longtask');
                const observer=supportsLongTasks?new PerformanceObserver(list=>longTasks.push(...list.getEntries().map(e=>e.duration))):null;
                observer?.observe({type:'longtask',buffered:false});
                document.querySelector('input[type=file]').addEventListener('change',()=>{
                  started=lastTick=performance.now();
                  timer=setInterval(()=>{const now=performance.now();gaps.push(now-lastTick);lastTick=now},10);
                  const frame=t=>{if(lastFrame)frames.push(t-lastFrame);lastFrame=t;raf=requestAnimationFrame(frame)};
                  raf=requestAnimationFrame(frame);
                },{once:true,capture:true});
                const changes=new MutationObserver(()=>{
                  if(started && document.querySelector('header').textContent.includes(n.toLocaleString('en-CA')+' employees validated') && document.querySelector('article')){
                    changes.disconnect();requestAnimationFrame(()=>requestAnimationFrame(()=>{
                      const now=performance.now();gaps.push(now-lastTick);clearInterval(timer);cancelAnimationFrame(raf);observer?.disconnect();
                      resolve({totalMs:now-started,maxTimerGapMs:Math.max(0,...gaps),maxFrameGapMs:Math.max(0,...frames),timerTicks:gaps.length-1,longTasksMs:supportsLongTasks?longTasks:null});
                    }));
                  }
                });changes.observe(document.body,{subtree:true,childList:true,characterData:true});
              });
            }''', count)
            page.locator('input[type=file]').set_input_files(str(csv))
            measurement = page.evaluate('()=>window.__probe')
            if iteration:
                runs.append(measurement)
            page.close()
        def stats(key):
            values = sorted(r[key] for r in runs)
            return {'median':statistics.median(values),'p95_nearest_rank':values[-1]}
        results.append({'employees':count,'sha256':hashlib.sha256(csv.read_bytes()).hexdigest(),
                        'summary':{key:stats(key) for key in ['totalMs','maxTimerGapMs','maxFrameGapMs','timerTicks']},'runs':runs})
        print(f'{stage}: measured {count}',flush=True)
    result = {'stage':stage,'url':base,'browser':browser.version,'samples':5,'warmups':1,
              'method':'Fresh pages; same local production preview and fixture hashes; file-change to ready DOM + two frames. A 10ms heartbeat and rAF track main-thread scheduling gaps. Long Tasks API where supported. Five-sample p95 is maximum, not a robust tail estimate. No CPU throttling.', 'results':results}
    (out / f'import-{stage}.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    browser.close()
