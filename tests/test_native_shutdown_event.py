"""Mechanism test for #5845: ``shutdown_event.set()`` must not deadlock after a worker process died mid-wait.

In native mode with ``reload=True``, the supervisor process creates a spawn-context ``multiprocessing.Event``
(see ``ui_run.py``) and the uvicorn worker monitors it in ``Server.run`` (see ``server.py``).
When the auto-reloader kills a worker, a thread blocking in ``event.wait()`` would leave a stale waiter
registration on the event's internal condition variable (``_sleeping_count`` in CPython's
``multiprocessing/synchronize.py``); a later ``event.set()`` then blocks forever inside
``Condition.notify_all()`` waiting for an acknowledgment the dead process can never send.
The fix polls ``event.is_set()`` instead, which never registers a waiter.

This test exercises the real code path: it spawns a worker process that runs ``Server.run`` with a
``shutdown_event`` (starting the monitor thread, like a native-mode reload worker), SIGKILLs the worker
mid-monitoring (like the auto-reloader does), and asserts that the supervisor side's ``event.set()``
returns promptly instead of deadlocking. ``set()`` runs in a watchdog thread so a deadlock fails the
test instead of hanging the pytest process.

Negative control (verified locally, not shipped as a perpetually-deadlocking CI test):
with the monitor thread reverted to plain ``event.wait()``, this test fails deterministically —
``event.set()`` is still blocked after the 5-second watchdog deadline.
"""

import multiprocessing
import socket
import sys
import threading
import time

import pytest


def _find_open_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def _wait_for_port(port: int, timeout: float) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=1):
                return
        except OSError:
            time.sleep(0.05)
    raise TimeoutError(f'server did not start listening on port {port} within {timeout} seconds')


def _run_worker(port: int,
                method_queue: multiprocessing.Queue,
                response_queue: multiprocessing.Queue,
                shutdown_event) -> None:
    """Entry point of the spawned worker process; runs the real ``Server.run`` with a minimal ASGI app."""
    from nicegui.server import CustomServerConfig, Server  # heavy import, keep it in the child

    async def app(scope, receive, send) -> None:
        if scope['type'] == 'lifespan':
            while True:
                message = await receive()
                if message['type'] == 'lifespan.startup':
                    await send({'type': 'lifespan.startup.complete'})
                elif message['type'] == 'lifespan.shutdown':
                    await send({'type': 'lifespan.shutdown.complete'})
                    return
        elif scope['type'] == 'http':
            await send({'type': 'http.response.start', 'status': 200, 'headers': []})
            await send({'type': 'http.response.body', 'body': b'ok'})

    config = CustomServerConfig(app, host='127.0.0.1', port=port, log_level='error', ws='wsproto')
    config.storage_secret = None
    config.method_queue = method_queue
    config.response_queue = response_queue
    config.shutdown_event = shutdown_event
    config.session_middleware_kwargs = None
    Server.create_singleton(config)
    Server.instance.run()


@pytest.mark.skipif(sys.platform == 'win32', reason='the deadlock is specific to POSIX semaphores (#5845)')
def test_shutdown_event_set_survives_killed_worker() -> None:
    context = multiprocessing.get_context('spawn')  # ui_run.py creates the event from the spawn context
    shutdown_event = context.Event()
    method_queue: multiprocessing.Queue = context.Queue()
    response_queue: multiprocessing.Queue = context.Queue()
    port = _find_open_port()
    worker = context.Process(target=_run_worker, args=(port, method_queue, response_queue, shutdown_event),
                             daemon=True)
    worker.start()
    try:
        _wait_for_port(port, timeout=15)  # the monitor thread starts before uvicorn begins serving
        time.sleep(0.5)  # give the monitor thread time to settle into its wait
        worker.kill()  # SIGKILL, like the auto-reloader killing the worker mid-wait
        worker.join(timeout=5)
        assert not worker.is_alive()

        setter = threading.Thread(target=shutdown_event.set, daemon=True)  # watchdog: a deadlock must not hang pytest
        setter.start()
        setter.join(timeout=5)
        assert not setter.is_alive(), 'shutdown_event.set() deadlocked after the worker process was killed (#5845)'
    finally:
        if worker.is_alive():
            worker.kill()
