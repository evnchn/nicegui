import secrets

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from . import core
from .version import __version__


class RedirectWithPrefixMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        prefix = request.headers.get('X-Forwarded-Prefix', '')
        response = await call_next(request)
        if 'Location' in response.headers and response.headers['Location'].startswith('/'):
            new_location = prefix + response.headers['Location']
            response.headers['Location'] = new_location
        return response


class SetCacheControlMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        if request.url.path.startswith(f'/_nicegui/{__version__}/') \
                and not request.url.path.startswith(f'/_nicegui/{__version__}/dynamic_resources/'):
            response.headers['Cache-Control'] = core.app.config.cache_control_directives
        return response


class CSPMiddleware(BaseHTTPMiddleware):
    """Middleware that generates per-request nonces and adds strict Content-Security-Policy headers.

    Tailwind and UnoCSS work under strict CSP because dynamically created <style> elements
    are monkey-patched to include the CSP nonce (see index.html).
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Generate a cryptographically secure nonce for this request
        nonce = secrets.token_urlsafe(16)
        request.state.csp_nonce = nonce

        response = await call_next(request)

        # Only add CSP header to HTML responses (pages, not API endpoints or static files)
        if core.app.config.csp_enabled and response.headers.get('X-NiceGUI-Content') == 'page':
            csp_directives = [
                "default-src 'self'",
                # Scripts: require nonce, use strict-dynamic for dynamically loaded scripts.
                # No unsafe-eval: templates are pre-compiled, eval replaced by dynamic script injection.
                # 'self' is a fallback for browsers that don't support strict-dynamic (ignored by modern browsers).
                f"script-src 'nonce-{nonce}' 'strict-dynamic' 'self'",
                # Styles: nonce for <style> elements (Tailwind/UnoCSS get nonces via monkey-patch),
                # unsafe-inline for style= attributes (used by Vue.js for v-show, transitions, etc.)
                f"style-src 'self' 'nonce-{nonce}'",
                f"style-src-elem 'self' 'nonce-{nonce}'",
                "style-src-attr 'unsafe-inline'",
                # Allow Socket.IO/WebSocket connections
                "connect-src 'self' ws: wss:",
                # Other directives
                "font-src 'self' data:",
                "img-src 'self' data: https:",
                "media-src 'self'",
                "object-src 'none'",
                "base-uri 'none'",
            ]

            # Allow custom CSP directives from config
            if core.app.config.csp_extra_directives:
                csp_directives.extend(core.app.config.csp_extra_directives)

            response.headers['Content-Security-Policy'] = '; '.join(csp_directives)

        return response
