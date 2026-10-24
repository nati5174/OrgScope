"""Exercise overlapping App imports with real workers and no injected delays."""
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
        page.add_init_script('''{
          const NativeWorker=window.Worker;
          window.importWorkers=[];
          window.Worker=class extends NativeWorker {
            constructor(url, options) {
              super(url, options);
              this.record={terminated:0};window.importWorkers.push(this.record);
            }
            terminate() { this.record.terminated++;super.terminate(); }
          };
        }''')
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(os.environ.get('AUDIT_BASE_URL', 'http://127.0.0.1:4173/'))
        page.get_by_role('button', name='Explore Giga Corp', exact=True).click()
        expect(page.locator('article')).to_have_count(5)
        csv = Path('data/audit/performance-100000.csv').read_text()

        def overlap(second, filename):
            page.evaluate('''({first,second,filename})=>{
              const input=document.querySelector('input[type=file]');
              for(const [csv,name] of [[first,'superseded.csv'],[second,filename]]){
                const transfer=new DataTransfer();
                transfer.items.add(new File([csv],name,{type:'text/csv'}));
                input.files=transfer.files;
                input.dispatchEvent(new Event('change',{bubbles:true}));
              }
            }''', {'first': csv, 'second': second, 'filename': filename})

        overlap('employee_id,manager_id,name,salary,currency\nnew,,Replacement,2,CAD', 'latest.csv')
        expect(page.locator('main > p')).to_contain_text('latest.csv')
        expect(page.locator('.inspector-profile small')).to_have_text('new')
        expect(page.locator('.inspector-profile h2')).to_have_text('Replacement')
        # The newest invalid import must retain the last good dataset, not the
        # superseded 100k organization. Superseded workers are really terminated.
        overlap('invalid', 'latest-invalid.csv')
        expect(page.get_by_role('alert')).to_be_visible()
        expect(page.locator('input[type=file]')).to_be_enabled()
        expect(page.locator('main > p')).to_contain_text('latest.csv')
        expect(page.locator('.inspector-profile small')).to_have_text('new')
        workers = page.evaluate('window.importWorkers')
        assert len(workers) == 5 and all(worker['terminated'] == 1 for worker in workers), workers
        assert not errors, errors
        results.append({'browser': engine, 'latestValidWins': 'PASS', 'latestInvalidRetainsPrior': 'PASS', 'workerTerminations': workers, 'pageErrors': errors})
        browser.close()
(out / 'import-races.json').write_text(json.dumps(results, indent=2))
print(json.dumps(results))
