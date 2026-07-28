from collections.abc import Callable
from typing import Any

import pytest
import socketio.exceptions

from nicegui import air


class FakeEngineIO:

    def __init__(self) -> None:
        self.state = 'connected'


class FakeRelay:
    """Minimal stand-in for ``socketio.AsyncClient`` reproducing its state semantics.

    In particular ``disconnect()`` only clears ``connected`` if the Engine.IO transport is still alive
    (python-socketio clears the flag from its Engine.IO disconnect handler, which a dead transport never triggers).
    """

    def __init__(self) -> None:
        self.connected = True
        self.eio = FakeEngineIO()
        self.connect_calls = 0

    async def connect(self, *args: Any, **kwargs: Any) -> None:
        if self.connected:
            raise socketio.exceptions.ConnectionError('Already connected')
        self.connect_calls += 1
        self.connected = True
        self.eio.state = 'connected'

    async def disconnect(self) -> None:
        if self.eio.state == 'connected':
            self.connected = False
        self.eio.state = 'disconnected'

    def on(self, *args: Any, **kwargs: Any) -> Callable:
        return lambda handler: handler


@pytest.fixture
def relay(monkeypatch: pytest.MonkeyPatch) -> FakeRelay:
    monkeypatch.setattr(air, 'timer', lambda *args, **kwargs: None)  # avoid a real keep-alive timer
    fake = FakeRelay()
    monkeypatch.setattr(air.socketio, 'AsyncClient', lambda *args, **kwargs: fake)
    return fake


async def test_reconnect_after_transport_died_silently(relay: FakeRelay) -> None:
    relay.eio.state = 'disconnected'  # transport died without a disconnect event, leaving `connected` set
    await air.Air('token').connect()
    assert relay.connect_calls == 1, 'a stale "connected" flag must not block the reconnect'
    assert relay.connected


async def test_no_reconnect_while_healthy(relay: FakeRelay) -> None:
    await air.Air('token').connect()
    assert relay.connect_calls == 0, 'a healthy connection must not be reset'
    assert relay.connected


async def test_no_reconnect_while_disconnecting(relay: FakeRelay) -> None:
    relay.eio.state = 'disconnecting'  # an intentional disconnect is in progress
    await air.Air('token').connect()
    assert relay.connect_calls == 0, 'a disconnect in progress must not be interrupted by the keep-alive timer'
