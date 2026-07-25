"""Serve family-filtered Quasar CSS via request interception and compare against the full sheet.

Answers three questions empirically:
  1. how many bytes does the split actually save (raw + gzip)?
  2. does a component added AFTER page load render unstyled?
  3. does splitting + re-concatenating change any computed style (cascade order)?
"""
from __future__ import annotations

import gzip
import json
import random
import socket
import subprocess
import sys
import time
from pathlib import Path

import tinycss2
from playwright.sync_api import sync_playwright
from split import STATIC, normalize, prelude_families
from tinycss2 import ast

sys.path.insert(0, str(Path(__file__).parent))

HERE = Path(__file__).parent
PY = sys.executable
SHEETS = ('quasar.unimportant.prod.css', 'quasar.important.prod.css')

DUMP_JS = '''() => {
  const out = [];
  document.querySelectorAll('*').forEach((e, i) => {
    const cs = getComputedStyle(e);
    const o = {};
    for (const p of cs) o[p] = cs.getPropertyValue(p);
    const r = e.getBoundingClientRect();
    out.push({i, tag: e.tagName, cls: e.className && e.className.baseVal !== undefined ? '' : String(e.className),
              box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], css: o});
  });
  return out;
}'''

CLASSES_JS = '''() => {
  const s = new Set();
  document.querySelectorAll('*').forEach(e => (e.classList || []).forEach(c => { if (c.startsWith('q-')) s.add(c); }));
  return [...s].sort();
}'''


def filter_sheet(name: str, used: set[str] | None) -> str:
    """Keep rules whose q- families intersect `used`; always keep rules with no q- selector."""
    text = (STATIC / name).read_text()
    if used is None:
        return text
    rules = tinycss2.parse_stylesheet(text, skip_whitespace=True)
    kept = []
    for node in rules:
        if not isinstance(node, (ast.QualifiedRule, ast.AtRule)):
            kept.append(node)
            continue
        fams = prelude_families(node)
        if not fams or (fams & used):
            kept.append(node)
    return tinycss2.serialize(kept)


def free_port() -> int:
    for _ in range(50):
        p = random.randint(20000, 60000)
        with socket.socket() as s:
            if s.connect_ex(('127.0.0.1', p)) != 0:
                return p
    raise RuntimeError('no port')


def diff_styles(a, b):
    diffs = []
    if len(a) != len(b):
        diffs.append(('ELEMENT COUNT', len(a), len(b)))
    for ea, eb in zip(a, b, strict=False):
        if ea['box'] != eb['box']:
            diffs.append((f"{ea['tag']}.{ea['cls'][:60]}", 'box', ea['box'], eb['box']))
        for k, v in ea['css'].items():
            if eb['css'].get(k) != v:
                diffs.append((f"{ea['tag']}.{ea['cls'][:60]}", k, v, eb['css'].get(k)))
    return diffs


def main() -> None:
    port = free_port()
    proc = subprocess.Popen([PY, str(HERE / 'app_hello.py'), str(port)],
                            cwd=HERE.parent, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        base = f'http://127.0.0.1:{port}'
        for _ in range(100):
            with socket.socket() as s:
                if s.connect_ex(('127.0.0.1', port)) == 0:
                    break
            time.sleep(0.2)
        time.sleep(1.5)

        with sync_playwright() as pw:
            browser = pw.chromium.launch()

            def make_page(used: set[str] | None):
                page = browser.new_page(viewport={'width': 1100, 'height': 900})
                bodies = {n: filter_sheet(n, used) for n in SHEETS}
                for n, body in bodies.items():
                    def handler(route, _request=None, b=body):
                        route.fulfill(status=200, content_type='text/css', body=b)
                    page.route(f'**/{n}', handler)
                return page, bodies

            # ---------- pass 1: full CSS, collect used families per page ----------
            page, _ = make_page(None)
            used_by_page = {}
            for route in ('', 'rich'):
                page.goto(f'{base}/{route}')
                page.wait_for_timeout(2500)
                used_by_page[route or 'hello'] = {normalize(c) for c in page.evaluate(CLASSES_JS)}
            full_ref = {}
            for route in ('', 'rich'):
                page.goto(f'{base}/{route}')
                page.wait_for_timeout(2500)
                full_ref[route or 'hello'] = page.evaluate(DUMP_JS)
                page.screenshot(path=str(HERE / f'full_{route or "hello"}.png'), full_page=True)
            page.close()

            # ---------- byte measurements ----------
            print('=== BYTES ===')
            for label, used in (('hello', used_by_page['hello']), ('rich', used_by_page['rich'])):
                raw_full = gz_full = raw_cut = gz_cut = 0
                for n in SHEETS:
                    orig = (STATIC / n).read_text().encode()
                    cut = filter_sheet(n, used).encode()
                    raw_full += len(orig)
                    gz_full += len(gzip.compress(orig, 9))
                    raw_cut += len(cut)
                    gz_cut += len(gzip.compress(cut, 9))
                print(f'{label}: families={len(used)} full={raw_full}B/{gz_full}gz  '
                      f'split={raw_cut}B/{gz_cut}gz  SAVED={raw_full-raw_cut}B raw / {gz_full-gz_cut}B gz '
                      f'({(gz_full-gz_cut)/gz_full:.1%} gz)')

            # ---------- pass 2: split CSS, same pages, compare ----------
            print('\n=== CASCADE / COMPUTED-STYLE DIFF (split vs full, same page) ===')
            for route in ('', 'rich'):
                label = route or 'hello'
                page, _ = make_page(used_by_page[label])
                page.goto(f'{base}/{route}')
                page.wait_for_timeout(2500)
                dump = page.evaluate(DUMP_JS)
                page.screenshot(path=str(HERE / f'split_{label}.png'), full_page=True)
                d = diff_styles(full_ref[label], dump)
                print(f'{label}: {len(d)} computed-style differences')
                for x in d[:15]:
                    print('   ', x)
                page.close()

            # ---------- pass 3: DYNAMIC ELEMENTS ----------
            print('\n=== DYNAMIC ELEMENTS (page shipped with hello-world families only) ===')
            page, _ = make_page(used_by_page['hello'])
            page.goto(f'{base}/dyn')
            page.wait_for_timeout(2500)
            before = set(page.evaluate(CLASSES_JS))
            page.screenshot(path=str(HERE / 'dyn_split_before.png'), full_page=True)
            page.get_by_role('button', name='add').click()
            page.wait_for_timeout(3000)
            after = set(page.evaluate(CLASSES_JS))
            page.screenshot(path=str(HERE / 'dyn_split_after.png'), full_page=True)
            dyn_dump = page.evaluate(DUMP_JS)
            missing = {normalize(c) for c in after} - used_by_page['hello']
            print(f'classes before={len(before)} after={len(after)}; '
                  f'families NOT shipped but now on page: {len(missing)}')
            print('   ', sorted(missing)[:40])
            page.close()

            # same, with full CSS, for the visual reference
            page, _ = make_page(None)
            page.goto(f'{base}/dyn')
            page.wait_for_timeout(2500)
            page.get_by_role('button', name='add').click()
            page.wait_for_timeout(3000)
            page.screenshot(path=str(HERE / 'dyn_full_after.png'), full_page=True)
            full_dyn = page.evaluate(DUMP_JS)
            page.close()

            d = diff_styles(full_dyn, dyn_dump)
            print(f'\n=== DYNAMIC computed-style diff (full vs hello-only split): {len(d)} differences ===')
            for x in d[:25]:
                print('   ', x)
            (HERE / 'dyn_diff.json').write_text(json.dumps(d[:2000], indent=1))
            browser.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        print('\nserver exit code', proc.poll())


if __name__ == '__main__':
    main()
