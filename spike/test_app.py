"""Measure the split on a realistic multi-component page (and check its cascade equivalence)."""
from __future__ import annotations

import gzip
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright
from split import STATIC, normalize
from test_split import CLASSES_JS, DUMP_JS, PY, SHEETS, diff_styles, filter_sheet, free_port

sys.path.insert(0, str(Path(__file__).parent))

HERE = Path(__file__).parent


def main() -> None:
    port = free_port()
    proc = subprocess.Popen([PY, str(HERE / 'app_hello.py'), str(port)],
                            cwd=HERE.parent, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        base = f'http://127.0.0.1:{port}'
        time.sleep(4)
        with sync_playwright() as pw:
            browser = pw.chromium.launch()

            def make_page(used):
                page = browser.new_page(viewport={'width': 1300, 'height': 1000})
                for n in SHEETS:
                    body = filter_sheet(n, used)

                    def handler(route, _request=None, b=body):
                        route.fulfill(status=200, content_type='text/css', body=b)
                    page.route(f'**/{n}', handler)
                return page

            page = make_page(None)
            page.goto(f'{base}/app')
            page.wait_for_timeout(4000)
            used = {normalize(c) for c in page.evaluate(CLASSES_JS)}
            full = page.evaluate(DUMP_JS)
            page.screenshot(path=str(HERE / 'app_full.png'), full_page=True)
            page.close()

            raw_f = gz_f = raw_c = gz_c = 0
            for n in SHEETS:
                o = (STATIC / n).read_text().encode()
                c = filter_sheet(n, used).encode()
                raw_f += len(o)
                gz_f += len(gzip.compress(o, 9))
                raw_c += len(c)
                gz_c += len(gzip.compress(c, 9))
            print(f'/app: {len(used)} families, {len(full)} DOM elements')
            print(f'  full  = {raw_f} B raw / {gz_f} B gz')
            print(f'  split = {raw_c} B raw / {gz_c} B gz')
            print(f'  SAVED = {raw_f-raw_c} B raw ({(raw_f-raw_c)/raw_f:.1%}) / {gz_f-gz_c} B gz ({(gz_f-gz_c)/gz_f:.1%})')

            page = make_page(used)
            page.goto(f'{base}/app')
            page.wait_for_timeout(4000)
            split = page.evaluate(DUMP_JS)
            page.screenshot(path=str(HERE / 'app_split.png'), full_page=True)
            d = diff_styles(full, split)
            print(f'  cascade diff: {len(d)} computed-style differences')
            for x in d[:10]:
                print('   ', x)
            browser.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        print('server exit code', proc.poll())


if __name__ == '__main__':
    main()
