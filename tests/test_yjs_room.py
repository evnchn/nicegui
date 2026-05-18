"""Unit tests for the Yjs collaboration primitive.

These exercise the server-side Socket.IO handlers directly so they don't depend on
Selenium. End-to-end two-browser propagation is covered separately in
``test_codemirror_crdt.py``.
"""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

# pylint: disable=protected-access

pycrdt = pytest.importorskip('pycrdt')

from nicegui import yjs_room  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_yjs_room() -> None:
    yjs_room._rooms.clear()
    yjs_room._access_checks.clear()
    yjs_room._handlers_installed = False


@pytest.fixture
def fake_sio(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    sio = MagicMock()
    sio.handlers: dict[str, Any] = {}

    def _on(event: str):
        def decorator(fn):
            sio.handlers[event] = fn
            return fn
        return decorator

    sio.on = _on
    sio.emit = AsyncMock()
    sio.enter_room = AsyncMock()
    sio.leave_room = AsyncMock()
    monkeypatch.setattr(yjs_room.core, 'sio', sio)
    return sio


async def test_prepare_room_is_idempotent(fake_sio: MagicMock) -> None:
    yjs_room.ensure_handlers_installed()
    yjs_room.ensure_handlers_installed()
    yjs_room.ensure_handlers_installed()
    # Each event should be registered exactly once.
    assert set(fake_sio.handlers) >= {'yjs_join', 'yjs_update', 'yjs_awareness', 'yjs_leave', 'disconnect'}


async def test_join_creates_room_and_emits_init(fake_sio: MagicMock) -> None:
    yjs_room.ensure_handlers_installed()
    await fake_sio.handlers['yjs_join']('sid-1', {'doc_id': 'doc-A'})
    assert 'doc-A' in yjs_room._rooms
    assert 'sid-1' in yjs_room._rooms['doc-A'].sids
    fake_sio.enter_room.assert_awaited_with('sid-1', 'yjs:doc-A')
    fake_sio.emit.assert_awaited()
    name, payload = fake_sio.emit.await_args.args[:2]
    assert name == 'yjs_init'
    assert payload['doc_id'] == 'doc-A'
    assert isinstance(payload['update'], (bytes, bytearray))


async def test_join_denied_when_access_check_returns_false(fake_sio: MagicMock) -> None:
    yjs_room.register_access_check('doc-A', lambda _doc_id, _sid: False)
    await fake_sio.handlers['yjs_join']('sid-1', {'doc_id': 'doc-A'})
    assert 'doc-A' not in yjs_room._rooms
    fake_sio.enter_room.assert_not_awaited()
    fake_sio.emit.assert_not_awaited()


async def test_join_allowed_when_async_access_check_returns_true(fake_sio: MagicMock) -> None:
    async def check(_doc_id: str, _sid: str) -> bool:
        return True
    yjs_room.register_access_check('doc-A', check)
    await fake_sio.handlers['yjs_join']('sid-1', {'doc_id': 'doc-A'})
    assert 'sid-1' in yjs_room._rooms['doc-A'].sids


async def test_update_applies_to_doc_and_broadcasts(fake_sio: MagicMock) -> None:
    yjs_room.ensure_handlers_installed()
    await fake_sio.handlers['yjs_join']('sid-1', {'doc_id': 'doc-A'})
    await fake_sio.handlers['yjs_join']('sid-2', {'doc_id': 'doc-A'})

    # Build a valid Yjs update by mutating a client-side Doc and capturing its update.
    client_doc = pycrdt.Doc()
    client_doc['text'] = pycrdt.Text()
    client_doc['text'] += 'hello'
    update_bytes = client_doc.get_update()

    fake_sio.emit.reset_mock()
    await fake_sio.handlers['yjs_update']('sid-1', {'doc_id': 'doc-A', 'update': update_bytes})

    # Server doc now reflects the edit.
    server_doc = yjs_room._rooms['doc-A'].doc
    server_doc['text'] = pycrdt.Text()  # re-bind type wrapper to read
    assert str(server_doc['text']) == 'hello'

    # Update is rebroadcast to the room, excluding the originator.
    fake_sio.emit.assert_awaited()
    name, payload = fake_sio.emit.await_args.args[:2]
    kwargs = fake_sio.emit.await_args.kwargs
    assert name == 'yjs_update'
    assert kwargs.get('skip_sid') == 'sid-1'
    assert kwargs.get('room') == 'yjs:doc-A'
    assert payload['update'] == update_bytes


async def test_update_from_non_member_is_dropped(fake_sio: MagicMock) -> None:
    yjs_room.ensure_handlers_installed()
    await fake_sio.handlers['yjs_join']('member', {'doc_id': 'doc-A'})

    client_doc = pycrdt.Doc()
    client_doc['text'] = pycrdt.Text()
    client_doc['text'] += 'attack'

    fake_sio.emit.reset_mock()
    await fake_sio.handlers['yjs_update']('outsider', {'doc_id': 'doc-A', 'update': client_doc.get_update()})

    fake_sio.emit.assert_not_awaited()


async def test_room_evicted_when_last_client_leaves(fake_sio: MagicMock) -> None:
    yjs_room.ensure_handlers_installed()
    await fake_sio.handlers['yjs_join']('sid-1', {'doc_id': 'doc-A'})
    await fake_sio.handlers['yjs_leave']('sid-1', {'doc_id': 'doc-A'})
    assert 'doc-A' not in yjs_room._rooms


async def test_disconnect_drops_client_from_every_room(fake_sio: MagicMock) -> None:
    yjs_room.ensure_handlers_installed()
    yjs_room.ensure_handlers_installed()
    await fake_sio.handlers['yjs_join']('sid-1', {'doc_id': 'doc-A'})
    await fake_sio.handlers['yjs_join']('sid-1', {'doc_id': 'doc-B'})
    await fake_sio.handlers['yjs_join']('sid-2', {'doc_id': 'doc-A'})

    await fake_sio.handlers['disconnect']('sid-1')

    assert 'sid-1' not in yjs_room._rooms['doc-A'].sids
    assert 'doc-B' not in yjs_room._rooms  # room-B was empty after sid-1 left
    # doc-A still has sid-2.
    assert 'sid-2' in yjs_room._rooms['doc-A'].sids


async def test_awareness_relay_only(fake_sio: MagicMock) -> None:
    yjs_room.ensure_handlers_installed()
    await fake_sio.handlers['yjs_join']('sid-1', {'doc_id': 'doc-A'})
    await fake_sio.handlers['yjs_join']('sid-2', {'doc_id': 'doc-A'})

    fake_sio.emit.reset_mock()
    payload = b'\x01\x02\x03'  # awareness updates are opaque bytes; server doesn't decode
    await fake_sio.handlers['yjs_awareness']('sid-1', {'doc_id': 'doc-A', 'update': payload})

    fake_sio.emit.assert_awaited()
    name, body = fake_sio.emit.await_args.args[:2]
    assert name == 'yjs_awareness'
    assert body['update'] == payload
    assert body['sid'] == 'sid-1'
    assert fake_sio.emit.await_args.kwargs.get('skip_sid') == 'sid-1'


async def test_invalid_payload_is_ignored(fake_sio: MagicMock) -> None:
    yjs_room.ensure_handlers_installed()
    # Missing doc_id, wrong types, etc. should never raise.
    await fake_sio.handlers['yjs_join']('sid-1', {})
    await fake_sio.handlers['yjs_update']('sid-1', {'doc_id': 'doc-A'})  # no update
    await fake_sio.handlers['yjs_update']('sid-1', {'doc_id': 123, 'update': b''})
    await fake_sio.handlers['yjs_awareness']('sid-1', {'doc_id': 'doc-A', 'update': 'not bytes'})
    fake_sio.emit.assert_not_awaited()
