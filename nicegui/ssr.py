"""Server-side rendering for NiceGUI using Vue's SSR renderer via MiniRacer (V8)."""

from __future__ import annotations

import re
from pathlib import Path

from . import json
from .logging import log

_STATIC_DIR = Path(__file__).parent / 'static'
_SSR_POLYFILLS_PATH = _STATIC_DIR / 'ssr-polyfills.js'
_SSR_BUNDLE_PATH = _STATIC_DIR / 'ssr-bundle.js'
_QUASAR_UMD_PATH = _STATIC_DIR / 'quasar.umd.prod.js'
_ctx = None
_import_failed = False
_init_text: str | None = None


def _get_context():
    """Get or create a MiniRacer context with the SSR bundle loaded."""
    global _ctx, _import_failed, _init_text  # pylint: disable=global-statement  # noqa: PLW0603
    if _ctx is not None:
        return _ctx
    if _import_failed:
        return None
    try:
        from py_mini_racer import MiniRacer  # type: ignore[import-not-found]  # pylint: disable=import-outside-toplevel
    except ImportError:
        log.info('mini-racer not installed; SSR disabled. Install with: pip install mini-racer')
        _import_failed = True
        return None
    _ctx = MiniRacer()
    if _init_text is None:
        # Load order matters:
        # 1. Polyfills (browser API stubs for V8)
        # 2. SSR bundle (Vue + server-renderer, exposes Vue on globalThis)
        # 3. Quasar UMD (same build as the browser, reads from window.Vue)
        _init_text = (
            _SSR_POLYFILLS_PATH.read_text()
            + ';\n'
            + _SSR_BUNDLE_PATH.read_text()
            + ';\n'
            + _QUASAR_UMD_PATH.read_text()
        )
    _ctx.eval(_init_text)
    return _ctx


def _reset_context() -> None:
    """Reset the MiniRacer context (e.g., after event loop changes)."""
    global _ctx  # pylint: disable=global-statement  # noqa: PLW0603
    if _ctx is not None:
        try:
            _ctx.close()
        except Exception:
            pass
    _ctx = None


def _postprocess(html: str) -> str:
    """Clean up SSR HTML to avoid hydration quirks."""
    def _strip_value(match: re.Match[str]) -> str:
        tag = match.group(0)
        if 'type="number"' in tag:
            return re.sub(r'\s+value="[^"]*"', '', tag)
        return tag
    return re.sub(r'<input\b[^>]*>', _strip_value, html)


def render_to_string(elements: dict[int, dict]) -> str:
    """Render a NiceGUI element tree to HTML using Vue's server-side renderer."""
    ctx = _get_context()
    if ctx is None:
        return ''

    elements_json = json.dumps(elements)
    try:
        ctx.eval(f'''
          globalThis._ssr_result = '';
          void renderNiceGUIToString({json.dumps(elements_json)}).then(function(html) {{
            globalThis._ssr_result = html;
          }}).catch(function(err) {{
            globalThis._ssr_result = '';
          }});
          undefined;
        ''')
        return _postprocess(ctx.eval('globalThis._ssr_result') or '')
    except RuntimeError:
        # MiniRacer's event loop was closed (e.g., server restart) - recreate context
        _reset_context()
        ctx = _get_context()
        if ctx is None:
            return ''
        ctx.eval(f'''
          globalThis._ssr_result = '';
          void renderNiceGUIToString({json.dumps(elements_json)}).then(function(html) {{
            globalThis._ssr_result = html;
          }}).catch(function(err) {{
            globalThis._ssr_result = '';
          }});
          undefined;
        ''')
        return _postprocess(ctx.eval('globalThis._ssr_result') or '')
