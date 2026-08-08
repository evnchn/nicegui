"""SPIKE test: aiohttp is made UNIMPORTABLE, then a real socket.io handshake +
event round-trip is performed against a local uvicorn/ASGI socket.io server.

Run:  python spike/test_roundtrip.py
"""
from __future__ import annotations

import asyncio
import socket
import sys


# ---------------------------------------------------------------- block aiohttp
class _Blocker:
    def find_module(self, name, path=None):  # legacy API, harmless
        return None

    def find_spec(self, name, path=None, target=None):
        if name == 'aiohttp' or name.startswith('aiohttp.'):
            raise ImportError(f'SPIKE: {name} is blocked (simulating not-installed)')


USE_AIOHTTP = '--aiohttp' in sys.argv
if not USE_AIOHTTP:
    sys.meta_path.insert(0, _Blocker())
if USE_AIOHTTP:
    import aiohttp
    print(f'[env] CONTROL RUN using real aiohttp {aiohttp.__version__}')
else:
    try:
        import aiohttp
        raise SystemExit('FAIL: aiohttp was importable despite the blocker')
    except ImportError as e:
        print(f'[env] aiohttp blocked: {e}')

import engineio.async_client  # noqa: E402
import socketio  # noqa: E402
import uvicorn  # noqa: E402

print(f'[env] engineio.async_client.aiohttp is {engineio.async_client.aiohttp!r}')
sys.path.insert(0, __file__.rsplit('/', 1)[0])
if not USE_AIOHTTP:
    assert engineio.async_client.aiohttp is None, 'expected the not-installed state'
    import no_aiohttp
    no_aiohttp.install()
    print('[env] shim installed ->', engineio.async_client.aiohttp)


def free_port() -> int:
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


PORT = free_port()

# ---------------------------------------------------------------- server
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = socketio.ASGIApp(sio, socketio_path='/on_air/socket.io')


LAST_SID = {}


@sio.event
async def connect(sid, environ, auth):
    LAST_SID['sid'] = sid
    print(f'[server] client connected sid={sid} query={environ.get("QUERY_STRING")}')
    await sio.emit('ready', {'device_url': 'https://example.invalid/abc'}, to=sid)


@sio.on('forward')
async def forward(sid, data):
    print(f'[server] got forward: {data}')
    return {'echo': data, 'ok': True}


# air.py's handlers RETURN values -> the relay emits with a callback and the
# client must ACK back. Also exercises a large BINARY payload (gzipped HTML).
AIR_RESULT: dict = {}


async def air_style_call(sid) -> None:
    reply = await sio.call('http', {'path': '/', 'method': 'GET'}, to=sid, timeout=10)
    AIR_RESULT.update({'status': reply['status_code'], 'len': len(reply['content']),
                       'is_bytes': isinstance(reply['content'], bytes)})
    print(f'[server] air-style call ACKed by client: {AIR_RESULT}')


async def run_server(stop: asyncio.Event) -> None:
    config = uvicorn.Config(app, host='127.0.0.1', port=PORT, log_level='warning')
    server = uvicorn.Server(config)
    task = asyncio.create_task(server.serve())
    while not server.started:
        await asyncio.sleep(0.05)
    await stop.wait()
    server.should_exit = True
    await task


# ---------------------------------------------------------------- client
async def exercise(transports: list[str]) -> bool:
    client = socketio.AsyncClient(reconnection=False)
    got_ready = asyncio.Event()
    payload = {}

    @client.on('ready')
    def _ready(data):
        payload.update(data)
        got_ready.set()

    # polling base64-inflates payloads past socket.io's 1 MB max_http_buffer_size
    # (upstream limit -- air.py chunks at 1 MB for exactly this reason), so the
    # big-binary case is exercised on the websocket transport.
    size = 900_000 if 'websocket' in transports else 100_000

    @client.on('http')
    async def _http(data):  # mirrors air.py's _handle_http: returns a dict with bytes
        assert data['method'] == 'GET'
        return {'status_code': 200, 'headers': [('content-encoding', 'gzip')],
                'content': b'x' * size}

    await client.connect(f'http://127.0.0.1:{PORT}?device_token=SPIKE',
                         socketio_path='/on_air/socket.io',
                         transports=transports, wait_timeout=5)
    print(f'[client {transports}] connected={client.connected} '
          f'transport={client.eio.current_transport} sid={client.sid}')
    await asyncio.wait_for(got_ready.wait(), 5)
    print(f'[client {transports}] server->client event OK: {payload}')

    ack = await client.call('forward', {'event': 'update', 'room': 'r1'}, timeout=5)
    print(f'[client {transports}] client->server emit+ack OK: {ack}')

    # the air.py shape: server calls us, our handler returns -> client sends the ACK
    AIR_RESULT.clear()
    await air_style_call(LAST_SID['sid'])
    air_ok = AIR_RESULT.get('status') == 200 and AIR_RESULT.get('len') == size \
        and AIR_RESULT.get('is_bytes')
    print(f'[client {transports}] server->client call + client ACK (binary): {air_ok}')

    final_transport = client.eio.current_transport
    await client.disconnect()
    print(f'[client {transports}] disconnected, connected={client.connected}')
    expected = 'websocket' if 'websocket' in transports else 'polling'
    return final_transport == expected and ack['ok'] and not client.connected and air_ok


async def exercise_reconnect() -> bool:
    """air.py relies on reconnection; test the automatic reconnect path."""
    client = socketio.AsyncClient(reconnection=True, reconnection_delay=0.2,
                                  reconnection_delay_max=0.5)
    disconnected = asyncio.Event()
    connects = []

    @client.on('connect')
    def _c():
        connects.append(1)

    @client.on('disconnect')
    def _d(*_):
        disconnected.set()

    stop1 = asyncio.Event()
    s1 = asyncio.create_task(run_server(stop1))
    await asyncio.sleep(0.6)
    await client.connect(f'http://127.0.0.1:{PORT}', socketio_path='/on_air/socket.io',
                         transports=['websocket'], wait_timeout=5)
    print(f'[reconnect] initial connect ok, connects={len(connects)}')
    stop1.set()
    await s1
    await asyncio.wait_for(disconnected.wait(), 15)
    print('[reconnect] server killed -> client saw disconnect')

    stop2 = asyncio.Event()
    s2 = asyncio.create_task(run_server(stop2))
    try:
        for _ in range(120):
            if client.connected:
                break
            await asyncio.sleep(0.25)
        print(f'[reconnect] after server restart: connected={client.connected} '
              f'connect-events={len(connects)}')
        ok = client.connected and len(connects) >= 2
        await client.disconnect()
        return ok
    finally:
        stop2.set()
        await s2


async def main() -> int:
    results = {}
    stop = asyncio.Event()
    server_task = asyncio.create_task(run_server(stop))
    try:
        await asyncio.sleep(0.6)
        import time
        for label, tr in [('websocket', ['websocket']), ('polling', ['polling']),
                          ('polling->ws upgrade', ['polling', 'websocket'])]:
            t0 = time.monotonic()
            results[label] = await exercise(tr)
            print(f'[timing] {label}: {time.monotonic() - t0:.2f}s')
    finally:
        stop.set()
        await server_task
        print('[server] stopped')

    results['reconnect'] = await exercise_reconnect()

    print('\n==== RESULTS ====')
    for k, v in results.items():
        print(f'{"PASS" if v else "FAIL"}  {k}')
    return 0 if all(results.values()) else 1


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
