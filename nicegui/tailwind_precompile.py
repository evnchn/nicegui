"""Server-side Tailwind precompilation.

Resolves a set of class tokens into a minimal stylesheet using a table that was derived
at build time from the real Tailwind CLI (see ``.spike/gen_table.py``).  When *every*
token can be resolved (or is known to be provided by another stylesheet), the caller can
inline the result and skip shipping the 260 kB browser JIT.  Any unresolvable token makes
``compile_classes`` return ``None`` so the caller falls back to the JIT.
"""
from __future__ import annotations

import functools
import json
import re
from collections.abc import Iterable
from pathlib import Path

STATIC = Path(__file__).parent / 'static'
TABLE_PATH = STATIC / 'tailwind_table.json'

_HOLE = '\x00'
_SAFE_ARBITRARY = re.compile(r'^[\w .,%#()/*+\-]+$')
_CLASS_SELECTOR = re.compile(r'\.(-?[_a-zA-Z][\w-]*)')
_VAR_REFERENCE = re.compile(r'var\((--[\w-]+)')
_ARBITRARY = re.compile(r'^(-?[a-z][a-z-]*)-\[(.+)]$')
_CLASS_ATTRIBUTE = re.compile(r'\bclass=(["\'])(.*?)\1', re.S)
_DYNAMIC_CLASS = re.compile(r'(?::|v-bind:)class\s*=')


@functools.lru_cache(maxsize=1)
def _table() -> dict:
    return json.loads(TABLE_PATH.read_text())


@functools.lru_cache(maxsize=1)
def _classes_covered_by_other_stylesheets() -> frozenset[str]:
    """Class names that Quasar/NiceGUI already style, so they never need Tailwind."""
    names: set[str] = set()
    for name in ('quasar.unimportant.css', 'quasar.important.css', 'nicegui.css', 'headwind.css'):
        path = STATIC / name
        if path.exists():
            names.update(_CLASS_SELECTOR.findall(path.read_text(errors='ignore')))
    return frozenset(names)


def _escape(token: str) -> str:
    """Escape a class token for use in a CSS selector, matching Tailwind's own output."""
    out = []
    for i, char in enumerate(token):
        if (char.isalnum() and char.isascii()) or char in '_-':
            if i == 0 and char.isdigit():
                out.append(f'\\3{char} ')
            else:
                out.append(char)
        else:
            out.append('\\' + char)
    return ''.join(out)


def _split_variants(token: str) -> list[str]:
    """Split ``hover:md:p-4`` into its parts without cutting inside ``[...]``."""
    parts, depth, current = [], 0, ''
    for char in token:
        if char == '[':
            depth += 1
        elif char == ']':
            depth -= 1
        if char == ':' and depth == 0:
            parts.append(current)
            current = ''
        else:
            current += char
    parts.append(current)
    return parts


def _resolve_utility(utility: str) -> tuple[str, list[str]] | None:
    """Return the declaration block and required @property names for a bare utility."""
    table = _table()
    bodies = table['utils'].get(utility)
    if bodies is not None:
        return '\n'.join(bodies), table['util_props'].get(utility, [])
    match = _ARBITRARY.match(utility)
    if match is None:
        return None
    template = table['arbitrary'].get(match.group(1))
    if template is None:
        return None
    value = match.group(2).replace('_', ' ')
    if not _SAFE_ARBITRARY.match(value) or value.count('(') != value.count(')'):
        return None
    if any(fn in value for fn in ('calc(', 'min(', 'max(', 'clamp(')):
        return None  # Tailwind re-spaces math operators; do not risk emitting different CSS
    return template.replace(_HOLE, value), table['arb_props'].get(match.group(1), [])


@functools.lru_cache(maxsize=1)
def _variant_ranks() -> dict[str, int]:
    """Rank variants for sorting; variants with identical wrappers (``sm``/``min-sm``) share a rank."""
    table = _table()
    by_wrapper: dict[str, int] = {}
    ranks: dict[str, int] = {}
    for variant, rank in sorted(table['variant_order'].items(), key=lambda item: item[1]):
        wrapper = table['variants'].get(variant, variant)
        ranks[variant] = by_wrapper.setdefault(wrapper, rank)
    return ranks


def _sort_key(token: str) -> tuple:
    """Reproduce Tailwind's own rule order: unprefixed utilities first, then variants."""
    table = _table()
    *variants, utility = _split_variants(token)
    order = table['util_order'].get(utility)
    if order is None:
        match = _ARBITRARY.match(utility)
        order = table['arb_order'].get(match.group(1), 0) if match else 0
    return ([_variant_ranks().get(v, 0) for v in variants], order)


def _resolve(token: str) -> tuple[str, list[str]] | None:
    """Return the full rule body (variants applied) and required @property names."""
    *variants, utility = _split_variants(token)
    resolved = _resolve_utility(utility)
    if resolved is None:
        return None
    if len(variants) > 1:
        return None  # Tailwind's rule order for stacked variants is not reproduced exactly yet
    body, props = resolved
    props = list(props)
    for variant in reversed(variants):
        wrapper = _table()['variants'].get(variant)
        if wrapper is None:
            return None
        body = wrapper.replace(_HOLE, body)
        props += _table()['variant_props'].get(variant, [])
    return body, props


def compile_classes(tokens: set[str], *, preflight: bool = True) -> str | None:
    """Compile the given class tokens into a stylesheet, or ``None`` if any token is unresolvable."""
    table = _table()
    known = _classes_covered_by_other_stylesheets()
    rules: dict[str, str] = {}
    needed: set[str] = set()
    for token in sorted(tokens, key=_sort_key):
        resolved = _resolve(token)
        if resolved is None:
            if token in known:
                continue  # some other stylesheet defines it, so Tailwind is not needed for it
            return None
        rules[token], props = resolved
        needed.update(props)
    css = '\n'.join(f'.{_escape(token)} {{{body}}}' for token, body in rules.items())

    variables: dict[str, str] = {}
    pending = _VAR_REFERENCE.findall(css) + _VAR_REFERENCE.findall(table['preflight'])
    while pending:
        name = pending.pop()
        if name in variables or name not in table['theme']:
            continue
        variables[name] = table['theme'][name]
        pending.extend(_VAR_REFERENCE.findall(variables[name]))
    keyframes = {name: body for name, body in table['keyframes'].items()
                 if any(re.search(rf'\b{re.escape(name)}\b', value) for value in variables.values())}
    tw_variables = sorted(needed)

    parts = []
    if variables or keyframes:
        theme = ''.join(f'{name}:{value};' for name, value in sorted(variables.items()))
        theme += ''.join(f'@keyframes {name}{{{body}}}' for name, body in sorted(keyframes.items()))
        parts.append('@layer theme{:root,:host{' + theme + '}}' if variables else '@layer theme{' + theme + '}')
    if preflight:
        parts.append('@layer base{' + table['preflight'] + '}')
    if css:
        parts.append('@layer utilities{' + css + '}')
    if tw_variables:
        parts.append(''.join(f'@property {name}{{{table["props"][name]}}}' for name in tw_variables))
        initials = ''.join(f'{name}:{table["prop_init"][name]};'
                           for name in tw_variables if name in table['prop_init'])
        if initials:
            parts.append('@layer properties{' + table['prop_supports_condition'] +
                         '{*,::before,::after,::backdrop{' + initials + '}}}')
    return '\n'.join(parts)


def compile_page(class_tokens: set[str], raw_html: Iterable[str]) -> str | None:
    """Compile a whole page, or return ``None`` when the browser JIT is needed after all.

    ``raw_html`` are the HTML fragments that never pass through :meth:`Element.classes`
    (``head_html``, ``body_html``, Vue templates).  Their static ``class`` attributes are
    added to the token set; a *dynamic* class binding makes the result unpredictable, so
    we decline and let the JIT handle the page.
    """
    tokens = set(class_tokens)
    for html in raw_html:
        if _DYNAMIC_CLASS.search(html):
            return None
        for _, value in _CLASS_ATTRIBUTE.findall(html):
            tokens.update(value.split())
    return compile_classes(tokens)
