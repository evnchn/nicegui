"""Forward-compat advisory for httpxyz (#6024).

httpxyz registers itself as `httpx` in `sys.modules` via `setdefault`, so
`import httpx` resolves to httpxyz when httpxyz is imported first. If real
httpx is imported before httpxyz, the alias becomes a no-op and the two
modules sit side by side, breaking `isinstance` checks across libraries.

When this module is imported it warns the user once if that conflict is
present. NiceGUI 4.0 will depend exclusively on httpxyz; until then NiceGUI
itself stays neutral and works with whichever module owns
`sys.modules['httpx']`.
"""
from __future__ import annotations

import sys
import warnings

_httpxyz = sys.modules.get('httpxyz')
if _httpxyz is not None and sys.modules.get('httpx') is not _httpxyz:
    warnings.warn(
        'httpxyz is loaded but real httpx was imported first; '
        'isinstance() checks against httpx types may silently fail on '
        'objects from libraries that already use httpxyz. Move '
        "'import httpxyz' to the very first line of your entry point. "
        'NiceGUI 4.0 will depend exclusively on httpxyz; see '
        'https://github.com/zauberzeug/nicegui/issues/6024.',
        UserWarning,
        stacklevel=3,
    )
del _httpxyz
