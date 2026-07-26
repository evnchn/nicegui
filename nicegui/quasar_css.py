"""PROTOTYPE: split Quasar's stylesheets into per-family chunks and serve them on demand.

This is the CSS twin of the server-side module-specifier resolution in ``dependencies.py``:
a page ships only the chunks its elements need, and elements created after the page has rendered
get their chunks pushed over the websocket before they are inserted.

NOT production code -- the element-to-family map below is harvested from a browser and is
exactly the hand-maintained manifest that makes this approach expensive.
"""
from __future__ import annotations

import functools
import json
import re
from pathlib import Path

import tinycss2  # type: ignore[import-untyped]

from . import core
from .version import __version__

STATIC = Path(__file__).parent / 'static'
CLASS_PATTERN = re.compile(r'\.(q-[A-Za-z0-9-]+)')
LAYERS = {'unimportant': 'quasar', 'important': 'quasar_importants'}

#: element class name -> Quasar CSS families, harvested by rendering each element in a real browser
ELEMENT_FAMILIES: dict[str, list[str]] = json.loads(
    (Path(__file__).parent / 'quasar_css_manifest.json').read_text(encoding='utf-8')
)
BASE_FAMILIES: list[str] = ELEMENT_FAMILIES.get('', [])


def _normalize(cls: str) -> str:
    return cls.split('__', 1)[0].split('--', 1)[0]


def _families(rule) -> set[str] | None:
    """Families a rule belongs to, or None if it cannot be attributed and must always be shipped."""
    if rule.type == 'qualified-rule':
        return {_normalize(m) for m in CLASS_PATTERN.findall(tinycss2.serialize(rule.prelude))} or None
    if rule.type == 'at-rule' and rule.content is not None:
        found: set[str] = set()
        for sub in tinycss2.parse_rule_list(rule.content, skip_comments=True, skip_whitespace=True):
            sub_families = _families(sub)
            if sub_families is None:
                return None
            found |= sub_families
        return found or None
    return None


@functools.cache
def _chunks(sheet: str, prod: str) -> dict[str, str]:
    """Return ``{'': always-ship CSS, family: CSS}`` for one Quasar stylesheet, preserving source order."""
    rules = tinycss2.parse_stylesheet((STATIC / f'quasar.{sheet}{prod}.css').read_text(encoding='utf-8'),
                                      skip_comments=True, skip_whitespace=True)
    out: dict[str, list[str]] = {'': []}
    for rule in rules:
        text = tinycss2.serialize([rule])
        families = _families(rule)
        for family in [''] if families is None else families:
            out.setdefault(family, []).append(text)
    return {family: ''.join(parts) for family, parts in out.items()}


def chunk(sheet: str, family: str) -> str | None:
    """Return the CSS of one chunk, or None if the family has no rules in that stylesheet."""
    return _chunks(sheet, '.prod' if getattr(core.app.config, 'prod_js', False) else '').get(family)


def paths(families: set[str]) -> list[dict[str, str]]:
    """Return ``{'path', 'layer'}`` entries for the chunks covering the given families.

    The paths are relative to ``/_nicegui/{version}/`` so the client can prepend its own prefix.
    """
    return [
        {'path': f'quasar-css/{sheet}/{family or "_base"}.css', 'layer': layer}
        for sheet, layer in LAYERS.items()
        for family in sorted(families | {''})
        if chunk(sheet, family)
    ]


def urls(prefix: str, families: set[str]) -> list[dict[str, str]]:
    """Return ``{'url', 'layer'}`` entries for the chunks covering the given families."""
    return [{'url': f'{prefix}/_nicegui/{__version__}/{entry["path"]}', 'layer': entry['layer']}
            for entry in paths(families)]


def families_of(elements) -> set[str]:
    """Return the Quasar CSS families the given elements need, according to the harvested manifest."""
    found = set(BASE_FAMILIES)
    for element in elements:
        for cls in type(element).__mro__:
            if cls.__name__ in ELEMENT_FAMILIES:
                found.update(ELEMENT_FAMILIES[cls.__name__])
                break
    return found
