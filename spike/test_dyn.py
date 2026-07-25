"""Fair dynamic test: ship the page's OWN initial family set, then add components at runtime."""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright
from split import normalize
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
                page = browser.new_page(viewport={'width': 1100, 'height': 900})
                for n in SHEETS:
                    body = filter_sheet(n, used)

                    def handler(route, _request=None, b=body):
                        route.fulfill(status=200, content_type='text/css', body=b)
                    page.route(f'**/{n}', handler)
                return page

            # reference: full CSS, /dyn before + after
            page = make_page(None)
            page.goto(f'{base}/dyn')
            page.wait_for_timeout(2500)
            own = {normalize(c) for c in page.evaluate(CLASSES_JS)}
            full_before = page.evaluate(DUMP_JS)
            page.get_by_role('button', name='add').click()
            page.wait_for_timeout(3000)
            full_after = page.evaluate(DUMP_JS)
            page.close()
            print(f'/dyn own initial families ({len(own)}): {sorted(own)}')

            # split shipping exactly /dyn's own initial families
            page = make_page(own)
            page.goto(f'{base}/dyn')
            page.wait_for_timeout(2500)
            split_before = page.evaluate(DUMP_JS)
            page.screenshot(path=str(HERE / 'own_before.png'), full_page=True)
            d0 = diff_styles(full_before, split_before)
            print(f'BEFORE click: {len(d0)} computed-style differences (expect 0)')
            for x in d0[:10]:
                print('   ', x)
            page.get_by_role('button', name='add').click()
            page.wait_for_timeout(3000)
            split_after = page.evaluate(DUMP_JS)
            page.screenshot(path=str(HERE / 'own_after.png'), full_page=True)
            d1 = diff_styles(full_after, split_after)
            print(f'AFTER click: {len(d1)} computed-style differences')
            affected = sorted({x[0] for x in d1})
            print(f'affected elements: {len(affected)} / {len(full_after)}')
            for a in affected[:20]:
                print('   ', a)
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
