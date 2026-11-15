#!/usr/bin/env python3
"""Generate Brotli sidecars for the static assets and inject them into a built wheel.

The sidecars are derived artifacts, so they are not tracked in git: they are
regenerated from their sources on every release. That keeps ~1 MB of binaries out
of the repository (and out of every dependency-bump diff), and makes a stale
sidecar structurally impossible rather than something CI has to police.

Usage, as a release step after the wheel exists:

    uv build
    uv run --with brotli python build.py dist/*.whl

Why injection rather than a poetry build hook:
  * `[tool.poetry.build] script = ...` does run, but it makes poetry emit a
    PLATFORM-TAGGED wheel (cp3xx-cp3xx-<os>_<arch>) instead of py3-none-any,
    which is wrong for a pure-Python package.
  * `[tool.poetry] include = [...]` silently skips files matched by .gitignore,
    so it cannot ship a generated-and-ignored artifact. Verified: identical build
    yields 96 sidecars with the ignore removed and 0 with it present.
Injecting into the finished wheel avoids both problems and leaves pyproject.toml
untouched.
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent
STATIC = ROOT / 'nicegui' / 'static'
SUFFIXES = {'.css', '.js', '.json', '.mjs', '.svg'}
MIN_SIZE = 500


def generate() -> list[Path]:
    """Compress every eligible static asset to a .br sidecar and return the ones written."""
    import brotli  # pylint: disable=import-outside-toplevel

    written = []
    for path in sorted(STATIC.rglob('*')):
        if path.suffix not in SUFFIXES or not path.is_file() or path.stat().st_size < MIN_SIZE:
            continue
        compressed = brotli.compress(path.read_bytes(), quality=11)
        if len(compressed) >= path.stat().st_size:
            continue  # a sidecar no smaller than its source is worthless
        sidecar = path.with_name(path.name + '.br')
        sidecar.write_bytes(compressed)
        written.append(sidecar)
    return written


def inject(wheel: Path, sidecars: list[Path]) -> None:
    """Add the sidecars to an existing wheel, next to the assets they compress."""
    existing = set(zipfile.ZipFile(wheel).namelist())
    with zipfile.ZipFile(wheel, 'a', compression=zipfile.ZIP_DEFLATED) as zf:
        for sidecar in sidecars:
            arcname = str(sidecar.relative_to(ROOT))
            if arcname not in existing:
                zf.write(sidecar, arcname)


if __name__ == '__main__':
    written = generate()
    print(f'generated {len(written)} brotli sidecars')
    for arg in sys.argv[1:]:
        inject(Path(arg), written)
        print(f'injected into {arg}')
