"""httpxyz forward-compat advisory; see https://github.com/zauberzeug/nicegui/issues/6024."""
import sys
import warnings

# httpxyz registers itself as `httpx` in `sys.modules` via `setdefault` (no-op if real
# httpx was imported first). NiceGUI 4.0 will require httpxyz; until then we stay
# neutral and just warn when real httpx is loaded so the user can prepare with one line.
_httpxyz = sys.modules.get('httpxyz')
_httpx = sys.modules.get('httpx')
if _httpx is not None and _httpx is not _httpxyz:
    warnings.warn(
        'Real httpx is loaded in this process. NiceGUI 4.0 will require '
        "httpxyz; install and 'import httpxyz' as the first line of your "
        'entry point. This aliases httpx -> httpxyz process-wide so every '
        'HTTP library (NiceGUI, anthropic, openai, ...) uses httpxyz. See '
        'https://github.com/zauberzeug/nicegui/issues/6024.',
        UserWarning,
        stacklevel=3,
    )
del _httpxyz, _httpx
