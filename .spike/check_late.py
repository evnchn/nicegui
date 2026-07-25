#!/usr/bin/env python3
"""The crux test: page renders runtime-only, then a template slot is added AFTER load."""
from playwright.sync_api import sync_playwright

URL = 'http://127.0.0.1:48731/late'

with sync_playwright() as p:
    browser = p.chromium.launch()
    try:
        page = browser.new_page()
        msgs = []
        page.on('console', lambda m: msgs.append((m.type, m.text)))
        page.on('pageerror', lambda e: msgs.append(('pageerror', str(e))))
        page.goto(URL, wait_until='networkidle')
        page.wait_for_timeout(1500)
        vue = page.evaluate('() => document.querySelector("script[type=importmap]").textContent')
        print('vue build:', 'runtime-only' if 'vue.runtime' in vue else 'FULL')
        page.click('text=add late template')
        page.wait_for_timeout(2000)
        print('late template rendered:', page.locator('#late-tpl').count() == 1)
        print('body:', repr(page.inner_text('body')[:120]))
        errs = [m for m in msgs if m[0] in ('error', 'pageerror', 'warning')]
        for e in errs:
            print('CONSOLE', e[0], ':', e[1][:300])
        if not errs:
            print('CONSOLE: clean')
        page.close()
    finally:
        browser.close()
