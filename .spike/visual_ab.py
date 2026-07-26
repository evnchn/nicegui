"""Render the same app with and without precompilation and diff every element's computed style."""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request

from playwright.sync_api import sync_playwright

ROOT = '/Users/evnchn/worktrees/tb2-tailwind-extract'
APP = sys.argv[1]
PROBE = '''() => {
  const out = [];
  for (const el of document.querySelectorAll('#app *')) {
    const s = getComputedStyle(el);
    const rec = {t: el.tagName, c: el.className};
    for (const p of ['padding','margin','width','height','color','background-color','display','flex-direction',
                     'gap','font-size','font-weight','border-radius','box-shadow','opacity','text-align',
                     'letter-spacing','line-height','align-items','justify-content','grid-template-columns',
                     'max-width','position','transform','text-transform','accent-color','animation-name']) {
      rec[p] = s.getPropertyValue(p);
    }
    out.push(rec);
  }
  return out;
}'''


def free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


def snapshot(precompile: str, extra_js: str = '') -> list:
    port = free_port()
    env = dict(os.environ, NICEGUI_PORT=str(port), PYTHONPATH=ROOT, NG_PRECOMPILE=precompile)
    proc = subprocess.Popen([sys.executable, APP], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        url = f'http://127.0.0.1:{port}/'
        for _ in range(120):
            try:
                urllib.request.urlopen(url, timeout=1)
                break
            except Exception:
                time.sleep(0.25)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url, wait_until='networkidle')
            page.wait_for_timeout(1500)
            if extra_js:
                page.evaluate(extra_js)
                page.wait_for_timeout(2000)
            result = page.evaluate(PROBE)
            has_jit = page.evaluate('() => !!document.querySelector(\'script[src*="tailwindcss.min.js"]\')')
            browser.close()
        return result, has_jit
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()
        assert proc.poll() is not None, 'server did not die'


extra = sys.argv[2] if len(sys.argv) > 2 else ''
off, off_jit = snapshot('0', extra)
on, on_jit = snapshot('1', extra)
print(f'JIT present: precompile=OFF {off_jit}, precompile=ON {on_jit}')
print(f'elements: {len(off)} vs {len(on)}')
diffs = 0
for a, b in zip(off, on):
    for key in a:
        if a[key] != b[key]:
            diffs += 1
            if diffs <= 20:
                print(f'  DIFF {a["t"]}.{str(a["c"])[:60]!r} {key}: off={a[key]!r} on={b[key]!r}')
print(f'total computed-style differences: {diffs}')
sys.exit(1 if diffs or len(off) != len(on) else 0)
