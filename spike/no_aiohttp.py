"""SPIKE: an aiohttp-free transport layer for python-engineio's AsyncClient.

engineio.async_client hard-codes aiohttp for BOTH transports (polling + websocket).
This module implements the *exact* slice of the aiohttp API that
engineio/async_client.py touches, backed by httpx (HTTP) + websockets (WS),
and injects it as the module-global `aiohttp` inside engineio.async_client.

Surface engineio actually uses (verified by reading engineio 4.13.1 source):
  aiohttp.ClientSession()            -> .closed .close() .cookie_jar.update_cookies()
                                        .get()/.post() (via getattr(session, method.lower()))
                                        .ws_connect()
  response                           -> .status, await .read(), await .json()
  aiohttp.ClientTimeout(total=)      aiohttp.ClientWSTimeout(ws_close=)
  aiohttp.WSMsgType.{CLOSE,CLOSING}  ws -> .send_str .send_bytes .receive() .close()
  aiohttp.ClientError
  aiohttp.client_exceptions.{WSServerHandshakeError,ServerConnectionError,
                             ClientConnectionError,ServerDisconnectedError}
"""
from __future__ import annotations

import ssl as ssl_module
import types

import httpx
import websockets
from websockets.asyncio.client import connect as ws_connect_impl


# --- exceptions (mirror the aiohttp names engineio catches) ------------------
class ClientError(Exception):
    pass


class ClientConnectionError(ClientError):
    pass


class ServerConnectionError(ClientConnectionError):
    pass


class ServerDisconnectedError(ServerConnectionError):
    pass


class WSServerHandshakeError(ClientConnectionError):
    pass


class ClientTimeout:
    def __init__(self, total=None):
        self.total = total


class ClientWSTimeout:
    def __init__(self, ws_close=None):
        self.ws_close = ws_close


class WSMsgType:
    TEXT = 1
    BINARY = 2
    CLOSE = 8
    CLOSING = 9
    CLOSED = 10


class WSMessage:
    __slots__ = ('data', 'type')

    def __init__(self, type_, data):
        self.type = type_
        self.data = data


class _Response:
    def __init__(self, response: httpx.Response):
        self._r = response

    @property
    def status(self):
        return self._r.status_code

    @property
    def headers(self):
        return self._r.headers

    async def read(self):
        return self._r.content

    async def json(self):
        try:
            return self._r.json()
        except ValueError as e:
            raise ClientError(str(e)) from e


class _WebSocket:
    def __init__(self, conn):
        self._conn = conn

    async def _send(self, data):
        try:
            await self._conn.send(data)
        except websockets.exceptions.ConnectionClosed as e:
            # engineio's write loop catches (ServerDisconnectedError, BrokenPipeError, OSError)
            raise ServerDisconnectedError(str(e)) from e

    async def send_str(self, data):
        await self._send(data)

    async def send_bytes(self, data):
        await self._send(data)

    async def receive(self):
        try:
            data = await self._conn.recv()
        except websockets.exceptions.ConnectionClosed as e:
            raise ServerDisconnectedError(str(e)) from e
        return WSMessage(WSMsgType.BINARY if isinstance(data, bytes) else WSMsgType.TEXT, data)

    async def close(self):
        await self._conn.close()


class _CookieJar:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    def update_cookies(self, cookies):
        for k, v in dict(cookies).items():
            self._client.cookies.set(k, v)


class ClientSession:
    """Drop-in for the sliver of aiohttp.ClientSession that engineio uses."""

    def __init__(self, **_kwargs):
        self._client = httpx.AsyncClient(follow_redirects=True)
        self.cookie_jar = _CookieJar(self._client)
        self._closed = False

    @property
    def closed(self):
        return self._closed

    async def close(self):
        self._closed = True
        await self._client.aclose()

    async def _request(self, method, url, headers=None, data=None, timeout=None, ssl=None):
        to = timeout.total if isinstance(timeout, ClientTimeout) else timeout
        try:
            r = await self._client.request(method, url, headers=headers, content=data, timeout=to)
        except httpx.HTTPError as e:
            raise ClientConnectionError(str(e)) from e
        return _Response(r)

    async def get(self, url, **kwargs):
        return await self._request('GET', url, **kwargs)

    async def post(self, url, **kwargs):
        return await self._request('POST', url, **kwargs)

    async def ws_connect(self, url, timeout=None, ssl=None, headers=None, **kwargs):
        headers = dict(headers or {})
        cookies = '; '.join(f'{c.name}={c.value}' for c in self._client.cookies.jar)
        if cookies:
            headers['Cookie'] = cookies
        ws_url = url.replace('https://', 'wss://').replace('http://', 'ws://')
        kwargs.pop('compress', None)
        try:
            conn = await ws_connect_impl(
                ws_url,
                additional_headers=headers,
                ssl=ssl if isinstance(ssl, ssl_module.SSLContext) else None,
                max_size=None,
                **kwargs,
            )
        except websockets.exceptions.InvalidStatus as e:
            raise WSServerHandshakeError(str(e)) from e
        except (OSError, websockets.exceptions.WebSocketException, TimeoutError) as e:
            raise ClientConnectionError(str(e)) from e
        return _WebSocket(conn)


def _module() -> types.ModuleType:
    m = types.ModuleType('aiohttp_httpx_shim')
    exc = types.ModuleType('aiohttp_httpx_shim.client_exceptions')
    for name in ('ClientError', 'ClientConnectionError', 'ServerConnectionError',
                 'ServerDisconnectedError', 'WSServerHandshakeError'):
        setattr(exc, name, globals()[name])
    m.client_exceptions = exc
    for name in ('ClientError', 'ClientConnectionError', 'ServerConnectionError',
                 'ServerDisconnectedError', 'WSServerHandshakeError',
                 'ClientTimeout', 'ClientWSTimeout', 'WSMsgType', 'ClientSession'):
        setattr(m, name, globals()[name])
    return m


def install(only_if_missing: bool = False) -> bool:
    """Point engineio.async_client's `aiohttp` global at the httpx/websockets shim.

    With ``only_if_missing`` the real aiohttp keeps precedence when installed, so this
    is purely additive: aiohttp becomes an optional dependency instead of a required one.
    """
    import engineio.async_client  # pylint: disable=import-outside-toplevel
    if only_if_missing and engineio.async_client.aiohttp is not None:
        return False
    engineio.async_client.aiohttp = _module()
    return True
