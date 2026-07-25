"""Boot the spike app on a random high port, collect all `q-*` classes present in the live DOM."""
from __future__ import annotations

import random
import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
PY = sys.executable


def free_port() -> int:
    for _ in range(50):
        p = random.randint(20000, 60000)
        with socket.socket() as s:
            if s.connect_ex(('127.0.0.1', p)) != 0:
                return p
    raise RuntimeError('no port')


JS = '''() => {
  const s = new Set();
  document.querySelectorAll('*').forEach(e => (e.classList || []).forEach(c => { if (c.startsWith('q-')) s.add(c); }));
  return [...s].sort();
}'''


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
            page = browser.new_page(viewport={'width': 1000, 'height': 800})
            for name in ('', 'rich'):
                page.goto(f'{base}/{name}')
                page.wait_for_timeout(2500)
                classes = page.evaluate(JS)
                (HERE / f'classes_{name or "hello"}.txt').write_text('\n'.join(classes))
                page.screenshot(path=str(HERE / f'shot_{name or "hello"}.png'), full_page=True)
                print(f'/{name}: {len(classes)} q- classes')
            # dynamic page: classes BEFORE the click (what a server-side splitter could know)
            page.goto(f'{base}/dyn')
            page.wait_for_timeout(2500)
            before = page.evaluate(JS)
            (HERE / 'classes_dyn_before.txt').write_text('\n'.join(before))
            page.screenshot(path=str(HERE / 'shot_dyn_before.png'), full_page=True)
            page.click('#c4')  # the button
            page.wait_for_timeout(2500)
            after = page.evaluate(JS)
            (HERE / 'classes_dyn_after.txt').write_text('\n'.join(after))
            page.screenshot(path=str(HERE / 'shot_dyn_after.png'), full_page=True)
            print(f'/dyn before: {len(before)}  after: {len(after)}  NEW: {len(set(after) - set(before))}')
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
