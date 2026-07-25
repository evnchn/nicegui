"""Split Quasar CSS into `.q-<family>` buckets and report attribution stats."""
from __future__ import annotations

import gzip
import re
import sys
from pathlib import Path

import tinycss2
from tinycss2 import ast

STATIC = Path(__file__).parent.parent / 'nicegui' / 'static'

CLASS_RE = re.compile(r'\.(q-[A-Za-z0-9_-]+)')


def normalize(token: str) -> str:
    """q-btn__wrapper -> q-btn ; q-btn--flat -> q-btn ; q-btn-group -> q-btn-group."""
    return re.split(r'__|--', token, maxsplit=1)[0]


def prelude_families(node) -> set[str]:
    """All q- families mentioned in the selector preludes of a node (recursing into at-rules)."""
    families: set[str] = set()
    if isinstance(node, ast.QualifiedRule):
        text = tinycss2.serialize(node.prelude)
        families |= {normalize(m) for m in CLASS_RE.findall(text)}
    elif isinstance(node, ast.AtRule):
        if node.content is None:
            return families
        # at-rule prelude itself (e.g. @media (...)) has no selectors; recurse into body
        inner = tinycss2.parse_rule_list(node.content, skip_whitespace=True)
        for sub in inner:
            if isinstance(sub, (ast.QualifiedRule, ast.AtRule)):
                families |= prelude_families(sub)
            elif isinstance(sub, ast.Declaration):
                pass
    return families


def analyse(path: Path):
    rules = tinycss2.parse_stylesheet(path.read_text(), skip_whitespace=True)
    entries = []  # (families, serialized_text)
    for node in rules:
        if not isinstance(node, (ast.QualifiedRule, ast.AtRule)):
            continue
        text = tinycss2.serialize([node])
        entries.append((prelude_families(node), text))
    return entries


def size(texts) -> tuple[int, int]:
    blob = ''.join(texts).encode()
    return len(blob), len(gzip.compress(blob, 9))


def main(used_file: str | None) -> None:
    used: set[str] | None = None
    if used_file:
        used = {normalize(t) for t in Path(used_file).read_text().split() if t.startswith('q-')}

    total_raw = total_gz = 0
    kept_raw_all = kept_gz_all = 0
    for name in ('quasar.unimportant.prod.css', 'quasar.important.prod.css'):
        path = STATIC / name
        entries = analyse(path)
        unattributed = [t for f, t in entries if not f]
        attributed = [(f, t) for f, t in entries if f]
        r, g = size([t for _, t in entries])
        ur, ug = size(unattributed)
        print(f'\n== {name}: {r} B raw / {g} B gz, {len(entries)} top-level rules')
        print(f'   no .q-* selector at all: {len(unattributed)} rules, {ur} B raw ({ur/r:.1%}) / {ug} B gz')
        all_fams = sorted({f for fs, _ in attributed for f in fs})
        print(f'   distinct families: {len(all_fams)}')
        if used is not None:
            kept = unattributed + [t for f, t in attributed if f & used]
            kr, kg = size(kept)
            print(f'   kept for page: {len(kept)} rules, {kr} B raw ({kr/r:.1%}) / {kg} B gz ({kg/g:.1%})')
            print(f'   SAVED: {r-kr} B raw / {g-kg} B gz')
            kept_raw_all += kr
            kept_gz_all += kg
        total_raw += r
        total_gz += g
    print(f'\n== TOTAL quasar css: {total_raw} B raw / {total_gz} B gz')
    if used is not None:
        print(f'== TOTAL kept:       {kept_raw_all} B raw / {kept_gz_all} B gz')
        print(f'== TOTAL SAVED:      {total_raw-kept_raw_all} B raw / {total_gz-kept_gz_all} B gz')
        print(f'   used families on page: {len(used)}')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else None)
