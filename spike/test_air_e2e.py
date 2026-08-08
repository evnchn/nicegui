"""SPIKE end-to-end: the REAL nicegui.air.Air client, in a venv with NO aiohttp
installed at all, connects to a local stand-in relay and serves a real NiceGUI
page through the On Air 'http' round-trip.

Run:  .spike-venv/bin/python spike/test_air_e2e.py
"""
from __future__ import annotations

import asyncio
import gzip
import importlib.util
import os
import socket
import subprocess
import sys

assert importlib.util.find_spec('aiohttp') is None, 'aiohttp must NOT be installed for this test'
print('[env] aiohttp is genuinely not installed in this interpreter')

import socketio  # noqa: E402
import uvicorn  # noqa: E402


def free_port() -> int:
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


RELAY_PORT = free_port()
APP_PORT = free_port()

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
relay_app = socketio.ASGIApp(sio, socketio_path='/on_air/socket.io')
connected = asyncio.Event()
state: dict = {}


@sio.event
async def connect(sid, environ, auth):
    state['sid'] = sid
    state['query'] = environ.get('QUERY_STRING', '')
    print(f'[relay] NiceGUI connected: sid={sid} query={state["query"]}', flush=True)
    connected.set()


async def main() -> int:
    config = uvicorn.Config(relay_app, host='127.0.0.1', port=RELAY_PORT, log_level='warning')
    server = uvicorn.Server(config)
    server_task = asyncio.create_task(server.serve())
    while not server.started:
        await asyncio.sleep(0.05)
    print(f'[relay] listening on {RELAY_PORT}', flush=True)

    env = {**os.environ, 'RELAY_PORT': str(RELAY_PORT), 'APP_PORT': str(APP_PORT)}
    proc = subprocess.Popen([sys.executable, os.path.join(os.path.dirname(__file__), 'e2e_app.py')],
                            env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    ok = False
    try:
        await asyncio.wait_for(connected.wait(), 45)
        assert 'device_token=SPIKE-TOKEN' in state['query'], state['query']

        reply = await sio.call('http', {
            'headers': {'host': 'localhost', 'user-agent': 'spike'},
            'prefix': '', 'path': '/', 'method': 'GET', 'params': {},
            'body': b'', 'instance-id': 'spike-instance',
        }, to=state['sid'], timeout=30)

        body = gzip.decompress(reply['content'])
        print(f'[relay] status={reply["status_code"]} gzip={len(reply["content"])}B '
              f'raw={len(body)}B', flush=True)
        marker = b'HELLO FROM AIR SPIKE' in body
        is_nicegui = b'nicegui' in body.lower()
        print(f'[relay] page contains label text: {marker}')
        print(f'[relay] response is a real NiceGUI page: {is_nicegui}')
        # informational only: air rewrites this when the template still has the hook
        print(f'[relay] (info) extraHeaders hook present: {b"extraHeaders" in body}, '
              f'instance-id injected: {b"fly-force-instance-id" in body}')
        ok = reply['status_code'] == 200 and marker and is_nicegui
    finally:
        proc.terminate()
        try:
            out, _ = proc.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            out, _ = proc.communicate()
        print('---- app subprocess output ----')
        print('\n'.join(out.splitlines()[:12]))
        print(f'---- app exited rc={proc.returncode} ----')
        server.should_exit = True
        await server_task
        print('[relay] stopped')

    print(f'\n==== E2E {"PASS" if ok else "FAIL"} ====')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
