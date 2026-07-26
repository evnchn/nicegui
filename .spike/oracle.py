"""Differential oracle: my Python compiler vs the real Tailwind CLI, for the same tokens."""
from nicegui import tailwind_precompile as TP
from pathlib import Path
import json
import re
import subprocess
import sys

sys.path.insert(0, '/Users/evnchn/worktrees/tb2-tailwind-extract')
sys.path.insert(0, '/Users/evnchn/worktrees/tb2-tailwind-extract/.spike')

import gen_table_lib as G  # noqa


SP = Path('/private/tmp/claude-501/-Users-evnchn/d69e45d1-d13a-4c7c-b633-beca80f25563/scratchpad/tw')
CLI = str(SP / 'node_modules/.bin/tailwindcss')


def norm(css, tag):
    p = G.parse(css)
    utils = {k: [re.sub(r'\s+', ' ', b).strip() for b in v] for k, v in p['utils'].items()}
    return {'utils': utils, 'order': list(p['utils']), 'theme': p['theme'], 'props': set(p['props']),
            'preflight': re.sub(r'\s+', ' ', p['preflight']).strip()}


def cli(tokens):
    (SP / 'c-ora.html').write_text('<div class="' + ' '.join(tokens) + '"></div>')
    (SP / 'i-ora.css').write_text(G.INPUT_CSS.format(content='c-ora.html'))
    subprocess.run([CLI, '-i', str(SP/'i-ora.css'), '-o', str(SP/'o-ora.css')], check=True, capture_output=True)
    return (SP/'o-ora.css').read_text()


def check(tokens, label):
    mine = TP.compile_classes(set(tokens))
    if mine is None:
        return ('SKIP', label, 'compiler declined (fallback to JIT)')
    a, b = norm(mine, 'mine'), norm(cli(tokens), 'cli')
    problems = []
    for k in sorted(set(a['utils']) | set(b['utils'])):
        if a['utils'].get(k) != b['utils'].get(k):
            problems.append(f'RULE {k}:\n   mine={a["utils"].get(k)}\n    cli={b["utils"].get(k)}')
    for k in sorted(set(a['theme']) | set(b['theme'])):
        if a['theme'].get(k) != b['theme'].get(k):
            problems.append(f'VAR {k}: mine={a["theme"].get(k)!r} cli={b["theme"].get(k)!r}')
    if a['props'] != b['props']:
        problems.append(f'PROPS mine-cli={a["props"]-b["props"]} cli-mine={b["props"]-a["props"]}')
    if a['order'] != b['order']:
        first = next(i for i, (x, y) in enumerate(zip(a['order'], b['order'])) if x != y)
        problems.append(
            f'ORDER differs at {first}: mine={a["order"][first-1:first+3]} cli={b["order"][first-1:first+3]}')
    if a['preflight'] != b['preflight']:
        problems.append('PREFLIGHT differs')
    return ('OK' if not problems else 'FAIL', label, problems)
