"""Execute the existing three Playwright workflow scripts unchanged across engines."""
import json
import os
import subprocess
import sys
from pathlib import Path

out = Path('data/audit/followup')
out.mkdir(exist_ok=True)
results = []
for browser in os.environ.get('QA_BROWSERS', 'chromium,firefox,webkit').split(','):
    directory = out / browser
    directory.mkdir(exist_ok=True)
    for script in ['check_explorer.py', 'check_analytics.py', 'check_scenario.py']:
        env = dict(os.environ, QA_BROWSER=browser, QA_OUTPUT_DIR=str(directory.resolve()),
                   AUDIT_BASE_URL=os.environ.get('AUDIT_BASE_URL', 'http://127.0.0.1:4173/'))
        result = subprocess.run([sys.executable, f'scripts/{script}'], env=env, capture_output=True, text=True, encoding='utf8', errors='replace')
        results.append({'browser':browser, 'script':script, 'exitCode':result.returncode, 'stdout':result.stdout, 'stderr':result.stderr})
        (out / 'cross-browser-suite.json').write_text(json.dumps(results,indent=2),encoding='utf8')
        print(f'{browser} {script}: {result.returncode}',flush=True)
sys.exit(int(any(r['exitCode'] for r in results)))
