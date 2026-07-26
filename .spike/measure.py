import gzip
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request


def brc(b):
    return len(subprocess.run(['brotli', '-c', '-q', '11'], input=b, capture_output=True).stdout)


ROOT = '/Users/evnchn/worktrees/tb2-tailwind-extract'
sys.path.insert(0, ROOT)


def free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    p = s.getsockname()[1]
    s.close()
    return p


APP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, '.spike/app_hello.py')
port = free_port()
env = dict(os.environ, NICEGUI_PORT=str(port), PYTHONPATH=ROOT)
proc = subprocess.Popen([sys.executable, APP], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    url = f'http://127.0.0.1:{port}/'
    for _ in range(120):
        try:
            urllib.request.urlopen(url, timeout=1)
            break
        except Exception:
            time.sleep(0.25)
    else:
        raise SystemExit('server never came up')
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as r:
        html = r.read()
        page_headers = dict(r.headers)
    srcs = re.findall(r'(?:src|href)="([^"]+)"', html.decode())
    srcs = [s for s in srcs if s.startswith('/_nicegui')]
    # also css @import
    srcs += re.findall(r'@import url\("([^"]+)"\)', html.decode())
    seen, rows = set(), []
    total = brc(html)
    rows.append(('index.html', len(html), total, ''))
    for s in srcs:
        if s in seen:
            continue
        seen.add(s)
        with urllib.request.urlopen(f'http://127.0.0.1:{port}{s}') as r:
            b = r.read()
            cc = r.headers.get('Cache-Control', '')
        br = brc(b)
        total += br
        rows.append((s.split('/')[-1], len(b), br, cc))
    rows.sort(key=lambda r: -r[2])
    print(f'{"resource":40s} {"raw":>10s} {"brotli":>10s}  cache-control')
    for n, raw, br, cc in rows:
        print(f'{n:40s} {raw:10d} {br:10d}  {cc}')
    print(f'{"TOTAL":40s} {"":10s} {total:10d}')
    print('index.html cache-control:', page_headers.get('Cache-Control'))
finally:
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except Exception:
        proc.kill()
    print('server dead:', proc.poll() is not None)
