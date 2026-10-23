import mimetypes

import anyio.to_thread
from starlette.datastructures import Headers
from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.types import Scope


class CacheControlledStaticFiles(StaticFiles):

    def __init__(self, *args, max_cache_age: int = 3600, **kwargs) -> None:
        self.max_cache_age = max_cache_age
        super().__init__(*args, **kwargs)

    async def get_response(self, path: str, scope: Scope) -> Response:
        brotli = 'br' in Headers(scope=scope).get('accept-encoding', '') and \
            (await anyio.to_thread.run_sync(self.lookup_path, path + '.br'))[1] is not None
        response = await super().get_response(path + '.br' if brotli else path, scope)
        if brotli and response.status_code == 200:
            media_type = mimetypes.guess_type(path)[0] or 'application/octet-stream'
            response.headers['Content-Encoding'] = 'br'
            response.headers['Content-Type'] = \
                media_type + ('; charset=utf-8' if media_type.startswith('text/') else '')
            response.headers['Vary'] = 'Accept-Encoding'  # GZipMiddleware sets this itself, but skips encoded responses
        response.headers['Cache-Control'] = f'public, max-age={self.max_cache_age}'
        return response
