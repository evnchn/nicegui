#!/usr/bin/env python3
"""Measure hello-world page weight with runtime-only vs full Vue.

Usage: measure.py [plain|slot|vue] [full]
  plain -> ui.label('Hello world') only
  slot  -> a page using Element.add_slot(template=...)
  vue   -> a page using a .vue single-file component
  full  -> force the original (full, compiler-included) Vue build
"""
import gzip
import re
import socket
import sys
import threading
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

MODE = sys.argv[1] if len(sys.argv) > 1 else 'plain'
FORCE_FULL = 'full' in sys.argv[1:]

from nicegui import (  # noqa: E402
    app,
    dependencies,  # noqa: E402
    ui,
)

if FORCE_FULL:
    _orig = dependencies.generate_resources

    def _patched(prefix, elements):
        vue_html, vue_styles, vue_scripts, imports, js_imports, js_imports_urls = _orig(prefix, elements)
        old = imports['vue']
        new = old.replace('vue.runtime.esm-browser', 'vue.esm-browser')
        imports['vue'] = new
        js_imports_urls = [new if u == old else u for u in js_imports_urls]
        return vue_html, vue_styles, vue_scripts, imports, js_imports, js_imports_urls
    dependencies.generate_resources = _patched
    from nicegui import client as _client_mod
    _client_mod.generate_resources = _patched

if MODE == 'plain':
    ui.label('Hello world')
elif MODE == 'slot':
    with ui.element('div') as el:
        el.add_slot('default', '<span>from a template slot</span>')
elif MODE == 'vue':
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'examples' / 'custom_vue_component'))
    from on_off import OnOff  # type: ignore  # noqa: E402
    OnOff('demo', on_change=lambda e: ui.notify(str(e.args)))
    ui.label('vue page')

PORT = 0
with socket.socket() as s:
    s.bind(('127.0.0.1', 0))
    PORT = s.getsockname()[1]

BASE = f'http://127.0.0.1:{PORT}'


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=20) as r:
        return r.read()


def report() -> None:
    html = fetch(BASE + '/').decode()
    # only what a browser actually fetches for this page:
    # modulepreload links, <script src>, CSS @import, plus the bare-specifier modules imported in <script type=module>
    urls = set()
    for m in re.finditer(r'<link rel="modulepreload" href="([^"]+)"', html):
        urls.add(m.group(1))
    for m in re.finditer(r'url\("([^"]*/_nicegui/[^"]+)"\)', html):
        urls.add(m.group(1))
    for m in re.finditer(r'src="([^"]*/_nicegui/[^"]+)"', html):
        urls.add(m.group(1))
    importmap = re.search(r'<script type="importmap">\s*(\{.*?\})\s*</script>', html, re.S)
    assert importmap
    import json
    imports = json.loads(importmap.group(1))['imports']
    for spec in ('vue', 'dompurify'):
        urls.add(imports[spec])
    urls = {u for u in urls if not u.endswith('/')}
    total_raw = len(html.encode())
    total_gz = len(gzip.compress(html.encode(), 9))
    rows = [('index.html', total_raw, total_gz)]
    for u in sorted(urls):
        try:
            data = fetch(BASE + u)
        except Exception as e:  # noqa: BLE001
            print(f'  SKIP {u}: {e}')
            continue
        gz = len(gzip.compress(data, 9))
        rows.append((u.split('/')[-1], len(data), gz))
        total_raw += len(data)
        total_gz += gz
    print(f'=== MODE={MODE} FORCE_FULL={FORCE_FULL} ===')
    for name, raw, gz in rows:
        print(f'  {name:45s} raw={raw:8d} gz={gz:8d}')
    print(f'  {"TOTAL":45s} raw={total_raw:8d} gz={total_gz:8d}')
    vue_ref = re.search(r'static/(vue[^"]*?\.js)', html)
    print(f'  vue build served: {vue_ref.group(1) if vue_ref else "??"}')


def run() -> None:
    time.sleep(3.0)
    try:
        report()
    finally:
        app.shutdown()


threading.Thread(target=run, daemon=True).start()
try:
    ui.run(port=PORT, show=False, reload=False, prod_js=True)
finally:
    print('server stopped')
