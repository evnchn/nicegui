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

CLI, WORK, OUT = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])

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


# --------------------------------------------------------------------------------------
# 1. base utilities
# --------------------------------------------------------------------------------------
BASE = (WORK / 'base.txt').read_text().split()
base_parsed = parse(compile_tokens(BASE, 'base'))
print(f'base utilities derived: {len(base_parsed["utils"])} / {len(BASE)} tokens')


# --------------------------------------------------------------------------------------
# 1b. per-utility @property dependencies
#
# Tailwind emits an @property block (plus a @layer properties fallback) for a *group* of
# --tw-* variables whenever a utility needs any of them, so the dependency cannot be read
# off the declaration text.  Utilities that mention the same set of --tw-* variables turn
# out to share the same dependency set, so we probe one representative per signature.
# --------------------------------------------------------------------------------------
needs_probe = [token for token, bodies in base_parsed['utils'].items()
               if re.search(r'--tw-[\w-]+', ' '.join(bodies))]
print(f'utilities needing an @property probe: {len(needs_probe)}')


def _probe(item):
    index, token = item
    probed = parse(compile_tokens([token], f'probe{threading.get_ident()}'))
    return token, sorted(probed['props'])


with ThreadPoolExecutor(max_workers=16) as pool:
    util_props = {token: props
                  for token, props in pool.map(_probe, enumerate(needs_probe))
                  if props}

# --------------------------------------------------------------------------------------
# 2. variant wrappers  (probe each variant against a known base utility)
# --------------------------------------------------------------------------------------
PROBE = 'p-4'
PROBE_BODY = base_parsed['utils'][PROBE][0]
VARIANTS = [
    'hover', 'focus', 'focus-within', 'focus-visible', 'active', 'visited', 'target',
    'disabled', 'enabled', 'checked', 'indeterminate', 'required', 'invalid', 'read-only',
    'placeholder-shown', 'autofill', 'default', 'empty', 'open',
    'first', 'last', 'only', 'odd', 'even', 'first-of-type', 'last-of-type',
    'group-hover', 'group-focus', 'group-active', 'group-disabled', 'group-checked', 'group-open',
    'peer-hover', 'peer-focus', 'peer-checked', 'peer-disabled', 'peer-invalid',
    'dark', 'motion-safe', 'motion-reduce', 'contrast-more', 'contrast-less',
    'print', 'portrait', 'landscape', 'rtl', 'ltr', 'forced-colors',
    'sm', 'md', 'lg', 'xl', '2xl',
    'max-sm', 'max-md', 'max-lg', 'max-xl', 'max-2xl',
    'min-sm', 'min-md', 'min-lg', 'min-xl', 'min-2xl',
    'before', 'after', 'placeholder', 'selection', 'marker', 'file', 'backdrop',
    'first-line', 'first-letter',
]
var_tokens = [f'{v}:{PROBE}' for v in VARIANTS]
var_parsed = parse(compile_tokens(var_tokens, 'var'))
variants: dict[str, str] = {}
variant_props: dict[str, list[str]] = {}
for v in VARIANTS:
    bodies = var_parsed['utils'].get(f'{v}:{PROBE}')
    if not bodies or len(bodies) != 1:
        print(f'  skip variant {v}: no unique rule')
        continue
    body = bodies[0]
    if PROBE_BODY not in body:
        print(f'  skip variant {v}: probe body not found verbatim')
        continue
    variants[v] = body.replace(PROBE_BODY, '\x00')
    probed = parse(compile_tokens([f'{v}:{PROBE}'], 'vprobe'))
    if probed['props']:
        variant_props[v] = sorted(probed['props'])
print(f'variant wrappers derived: {len(variants)} / {len(VARIANTS)}')

# --------------------------------------------------------------------------------------
# 3. arbitrary-value templates  (probe each family with a sentinel value)
# --------------------------------------------------------------------------------------
FAMILY_PROBES = {
    **{f: '9px' for f in [
        'w', 'h', 'min-w', 'min-h', 'max-w', 'max-h', 'size', 'basis',
        'p', 'px', 'py', 'pt', 'pr', 'pb', 'pl', 'm', 'mx', 'my', 'mt', 'mr', 'mb', 'ml',
        'gap', 'gap-x', 'gap-y', 'top', 'right', 'bottom', 'left', 'inset', 'inset-x', 'inset-y',
        'translate-x', 'translate-y', 'leading', 'tracking', 'text', 'rounded', 'border',
        'space-x', 'space-y', 'indent', 'scroll-m', 'scroll-p', 'blur',
    ]},
    **{f: '1fr' for f in ['grid-cols', 'grid-rows', 'flex']},
    **{f: '#123456' for f in ['bg', 'fill', 'stroke', 'ring', 'shadow', 'outline', 'accent', 'caret', 'decoration']},
    **{f: '3' for f in ['z', 'order', 'opacity', 'col-span', 'row-span', 'columns', 'grow', 'shrink']},
    **{f: '3deg' for f in ['rotate']},
    **{f: '1.5' for f in ['scale']},
    **{f: '300ms' for f in ['duration', 'delay']},
    **{f: '16/9' for f in ['aspect']},
}
arb_tokens = [f'{f}-[{v}]' for f, v in FAMILY_PROBES.items()]
arb_parsed = parse(compile_tokens(arb_tokens, 'arb'))
order_parsed = parse(compile_tokens(BASE + arb_tokens, 'order'))
util_order = {token: index for index, token in enumerate(order_parsed['utils'])}
arb_order = {fam: util_order[f'{fam}-[{val}]'] for fam, val in FAMILY_PROBES.items()
             if f'{fam}-[{val}]' in util_order}
variant_order = {v: index for index, (token, _) in enumerate(var_parsed['utils'].items())
                 for v in [token[:-len(':' + PROBE)]] if token.endswith(':' + PROBE)}
arbitrary: dict[str, str] = {}
arb_props: dict[str, list[str]] = {}
for fam, val in FAMILY_PROBES.items():
    bodies = arb_parsed['utils'].get(f'{fam}-[{val}]')
    if not bodies or len(bodies) != 1:
        continue
    body = bodies[0]
    if val not in body:
        continue
    arbitrary[fam] = body.replace(val, '\x00')
    probed = parse(compile_tokens([f'{fam}-[{val}]'], 'probe'))
    if probed['props']:
        arb_props[fam] = sorted(probed['props'])
print(f'arbitrary templates derived: {len(arbitrary)} / {len(FAMILY_PROBES)}')

# --------------------------------------------------------------------------------------
# 4. emit
# --------------------------------------------------------------------------------------
table = {
    'version': re.search(r'tailwindcss v([\d.]+)', (WORK / 'o-base.css').read_text()).group(1),
    'preflight': base_parsed['preflight'],
    'theme': base_parsed['theme'],
    'keyframes': base_parsed['keyframes'],
    'utils': {k: v for k, v in base_parsed['utils'].items()},
    'props': ALL_PROPS,
    'prop_init': ALL_INIT,
    'prop_supports_condition': base_parsed['prop_supports'].split('{')[0].strip(),
    'util_props': util_props,
    'arb_props': arb_props,
    'util_order': util_order,
    'arb_order': arb_order,
    'variant_order': variant_order,
    'variants': variants,
    'variant_props': variant_props,
    'arbitrary': arbitrary,
}
OUT.write_text(json.dumps(table, separators=(',', ':'), sort_keys=True))
print(f'wrote {OUT} ({OUT.stat().st_size} bytes)')
