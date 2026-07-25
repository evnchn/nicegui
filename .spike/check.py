#!/usr/bin/env python3
"""Browser check: load pages, capture console errors, verify rendering + interaction."""
import sys

from playwright.sync_api import sync_playwright

TARGETS = [
    ('http://127.0.0.1:48731/', 'runtime-only rich page'),
    ('http://127.0.0.1:48731/slot', 'template-slot page (full build)'),
    ('http://127.0.0.1:48732/vue', '.vue component page (full build)'),
]

with sync_playwright() as p:
    browser = p.chromium.launch()
    try:
        for url, name in TARGETS:
            page = browser.new_page()
            msgs = []
            page.on('console', lambda m: msgs.append((m.type, m.text)))
            page.on('pageerror', lambda e: msgs.append(('pageerror', str(e))))
            page.goto(url, wait_until='networkidle')
            page.wait_for_timeout(2000)
            vue_src = page.evaluate(
                '() => [...document.querySelectorAll("link[rel=modulepreload]")].map(l=>l.href)'
                '.find(h=>h.includes("vue")) || document.querySelector("script[type=importmap]").textContent')
            body = page.inner_text('body')
            print(f'--- {name} ({url})')
            print(f'    vue: {str(vue_src).split("/")[-1][:60]}')
            print(f'    body starts: {body[:90]!r}')
            if 'slot' in url:
                print(f'    template slot rendered: {page.locator("#tpl").count() == 1}')
            if url.endswith('/vue'):
                page.click('.q-btn' if page.locator('.q-btn').count() else 'body')
                page.wait_for_timeout(800)
                print(f'    after click body: {page.inner_text("body")[:90]!r}')
            if url.endswith('48731/'):
                page.click('text=Click me')
                page.wait_for_timeout(800)
                print(f'    notify visible: {"clicked!" in page.inner_text("body")}')
            errs = [m for m in msgs if m[0] in ('error', 'pageerror', 'warning')]
            print(f'    console errors/warnings: {errs if errs else "NONE"}')
            page.close()
    finally:
        browser.close()
