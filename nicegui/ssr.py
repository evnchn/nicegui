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
    # Strip value from number inputs (causes cursor position issues during hydration)
    def _strip_value(match: re.Match[str]) -> str:
        tag = match.group(0)
        if 'type="number"' in tag:
            return re.sub(r'\s+value="[^"]*"', '', tag)
        return tag
    html = re.sub(r'<input\b[^>]*>', _strip_value, html)

    # Replace <a name="..."> (link targets) with <div name="..."> to avoid nested <a> tags.
    # Nested <a> tags are invalid HTML; browsers restructure them, breaking Vue hydration.
    html = _fix_anchor_nesting(html)

    return html


def _fix_anchor_nesting(html: str) -> str:
    """Replace <a> link targets with <div> to prevent invalid nested <a> tags."""
    result: list[str] = []
    i = 0
    length = len(html)
    while i < length:
        if not _is_anchor_open(html, i, length):
            result.append(html[i])
            i += 1
            continue
        tag_end = html.index('>', i) + 1
        tag = html[i:tag_end]
        if not re.search(r'\bname=', tag):
            result.append(html[i])
            i += 1
            continue
        # This is a link target <a name="..."> - replace with <div>
        result.append('<div' + tag[2:])
        i = tag_end
        i = _copy_until_matching_close(html, i, length, result)
    return ''.join(result)


def _is_anchor_open(html: str, i: int, length: int) -> bool:
    """Check if position i starts an <a> opening tag."""
    return (html[i] == '<' and i + 2 < length and html[i + 1] == 'a' and html[i + 2] in (' ', '>'))


def _copy_until_matching_close(html: str, i: int, length: int, result: list[str]) -> int:
    """Copy HTML content until the matching </a> is found, replacing it with </div>."""
    depth = 1
    while i < length and depth > 0:
        if html[i] != '<':
            result.append(html[i])
            i += 1
            continue
        if i + 3 < length and html[i + 1] == '/' and html[i + 2] == 'a' and html[i + 3] == '>':
            depth -= 1
            if depth == 0:
                result.append('</div>')
                return i + 4
            result.append('</a>')
            i += 4
        elif _is_anchor_open(html, i, length):
            depth += 1
            result.append(html[i])
            i += 1
        else:
            result.append(html[i])
            i += 1
    return i


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
