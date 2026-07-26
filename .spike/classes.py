"""Dump every class token that appears in a rendered NiceGUI page."""
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request

ROOT = '/Users/evnchn/worktrees/tb2-tailwind-extract'


def free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    p = s.getsockname()[1]
    s.close()
    return p


APP = sys.argv[1]
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
    html = urllib.request.urlopen(url).read().decode()
    toks = set()
    for m in re.finditer(r'class="([^"]*)"', html):
        toks.update(m.group(1).split())
    for m in re.finditer(r'\\"class\\":\s*\\"([^"]*?)\\"', html):
        toks.update(m.group(1).split())
    # elements JSON is embedded raw inside String.raw`...`
    m = re.search(r'parseElements\(String\.raw`(.*?)`\)', html, re.S)
    if m:
        try:
            data = json.loads(m.group(1))

            def walk(o):
                if isinstance(o, dict):
                    for k, v in o.items():
                        if k == 'class':
                            if isinstance(v, str):
                                toks.update(v.split())
                            elif isinstance(v, list):
                                toks.update(t for x in v for t in str(x).split())
                        else:
                            walk(v)
                elif isinstance(o, list):
                    for v in o:
                        walk(v)
            walk(data)
        except Exception as e:
            print('json parse failed', e, file=sys.stderr)
    print(json.dumps(sorted(toks)))
finally:
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except Exception:
        proc.kill()
