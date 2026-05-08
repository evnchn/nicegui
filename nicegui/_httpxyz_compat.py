"""Forward-compat advisory for httpxyz (#6024).

httpxyz registers itself as `httpx` in `sys.modules` via `setdefault`, so
`import httpx` resolves to httpxyz when httpxyz is imported first. NiceGUI
4.0 will depend exclusively on httpxyz; until then NiceGUI itself stays
neutral and works with whichever module owns `sys.modules['httpx']`.

When this module is imported it warns the user once if real httpx is loaded
in this process — i.e. the user (or a library they imported before NiceGUI)
is using real httpx, and adding `import httpxyz` as the first line of their
entry point would prepare them for 4.0 and route every HTTP library through
the same stack today.
"""
from __future__ import annotations

import sys
import warnings

_httpxyz = sys.modules.get('httpxyz')
_httpx = sys.modules.get('httpx')
if _httpx is not None and _httpx is not _httpxyz:
    warnings.warn(
        'Real httpx is loaded in this process. NiceGUI 4.0 will depend '
        'exclusively on httpxyz; add '
        "'import httpxyz' "
        'as the first line of your entry point (installing httpxyz first if '
        'needed) to alias httpx -> httpxyz process-wide so every HTTP '
        'library (NiceGUI, anthropic, openai, ...) routes through the same '
        'stack. See https://github.com/zauberzeug/nicegui/issues/6024.',
        UserWarning,
        stacklevel=3,
    )
del _httpxyz, _httpx
