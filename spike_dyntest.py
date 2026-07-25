"""Drive the /dynamic page: click the button that adds an ESM-backed element AFTER load."""
import sys

from playwright.sync_api import sync_playwright

PORT = sys.argv[1]
errors = []

with sync_playwright() as p:
    browser = p.chromium.launch()
    try:
        page = browser.new_page()
        page.on('console', lambda m: errors.append(f'{m.type}: {m.text}') if m.type == 'error' else None)
        page.on('pageerror', lambda e: errors.append(f'pageerror: {e}'))
        page.goto(f'http://127.0.0.1:{PORT}/dynamic')
        page.wait_for_selector('[class~="addbtn"]', timeout=10000)
        page.wait_for_timeout(1000)
        print('--- errors before click:', errors)
        errors.clear()
        page.click('[class~="addbtn"]')
        page.wait_for_timeout(3000)
        print('--- errors after click:', errors)
        chart = page.query_selector('[class~="mychart"]')
        print('--- chart element present:', chart is not None)
        if chart:
            print('--- chart innerHTML length:', len(chart.inner_html()))
            print('--- has canvas:', page.query_selector('[class~="mychart"] canvas') is not None)
    finally:
        browser.close()
