"""Build-time generator: derive a Tailwind rule table from the REAL Tailwind CLI.

Nothing here is hand-written CSS knowledge: every rule body, variant wrapper and
arbitrary-value template is produced by running `@tailwindcss/cli` and parsing its output.

Usage:  python3 gen_table.py <tailwindcss-cli> <workdir> <out.json>
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

CLI = WORK = OUT = None

INPUT_CSS = '''@import "tailwindcss" source(none);
@custom-variant dark (&:where(body.body--dark, body.body--dark *));
@source "./{content}";
'''


def compile_tokens(tokens: list[str], tag: str) -> str:
    """Run the real Tailwind CLI over the given class tokens and return the CSS."""
    (WORK / f'c-{tag}.html').write_text('<div class="' + ' '.join(tokens) + '"></div>')
    (WORK / f'i-{tag}.css').write_text(INPUT_CSS.format(content=f'c-{tag}.html'))
    subprocess.run([CLI, '-i', str(WORK / f'i-{tag}.css'), '-o', str(WORK / f'o-{tag}.css')],
                   check=True, capture_output=True)
    return (WORK / f'o-{tag}.css').read_text()


def _balanced(css: str, open_idx: int) -> tuple[str, int]:
    """Return the body inside the braces starting at ``open_idx`` and the index past the close."""
    depth, i = 0, open_idx
    while i < len(css):
        if css[i] == '{':
            depth += 1
        elif css[i] == '}':
            depth -= 1
            if depth == 0:
                return css[open_idx + 1:i], i + 1
        i += 1
    raise ValueError('unbalanced')


def top_level_blocks(css: str) -> list[tuple[str, str]]:
    """Split CSS into (prelude, body) pairs at nesting depth 0."""
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    out, i, start = [], 0, 0
    while i < len(css):
        if css[i] == '{':
            body, nxt = _balanced(css, i)
            out.append((css[start:i].strip(), body))
            i = start = nxt
        elif css[i] == ';':
            out.append((css[start:i].strip(), ''))
            i = start = i + 1
        else:
            i += 1
    return out


def unescape(sel: str) -> str:
    """Turn a CSS-escaped class selector back into the class token."""
    return re.sub(r'\\(?:([0-9a-fA-F]{1,6})[ ]?|(.))',
                  lambda m: chr(int(m.group(1), 16)) if m.group(1) else m.group(2), sel)


ALL_PROPS: dict[str, str] = {}
ALL_INIT: dict[str, str] = {}


def parse(css: str) -> dict:
    """Parse a Tailwind CLI output into theme vars, preflight, utilities and @property machinery."""
    res = {'theme': {}, 'keyframes': {}, 'preflight': '', 'utils': {},
           'props': {}, 'prop_init': {}, 'prop_supports': ''}
    for prelude, body in top_level_blocks(css):
        if prelude == '@layer theme':
            for inner_prelude, inner_body in top_level_blocks(body):
                if inner_prelude.startswith('@keyframes '):
                    res['keyframes'][inner_prelude.split(None, 1)[1].strip()] = inner_body.strip()
                    continue
                for decl in re.findall(r'(--[\w-]+)\s*:\s*([^;]+);', inner_body):
                    res['theme'][decl[0]] = ' '.join(decl[1].split())
        elif prelude == '@layer base':
            res['preflight'] = body.strip()
        elif prelude == '@layer utilities':
            for sel, rule_body in top_level_blocks(body):
                if not sel.startswith('.'):
                    continue
                res['utils'].setdefault(unescape(sel[1:]), []).append(rule_body.strip())
        elif prelude.startswith('@property '):
            var = prelude.split(None, 1)[1].strip()
            res['props'][var] = body.strip()
        elif prelude == '@layer properties':
            res['prop_supports'] = body.strip()
            for decl in re.findall(r'(--tw-[\w-]+)\s*:\s*([^;]+);', body):
                res['prop_init'][decl[0]] = decl[1].strip()
    ALL_PROPS.update(res['props'])
    ALL_INIT.update(res['prop_init'])
    return res
