"""Yjs collaboration primitive for NiceGUI.

Server-side Y.Doc rooms backed by pycrdt, relayed over the existing Socket.IO server.
The primitive is element-agnostic: any element whose client side can bind to a Y.Doc
(e.g. ``ui.codemirror`` via ``y-codemirror.next``, future ``ui.tiptap`` via
``y-prosemirror``) can join a named room by emitting ``yjs_join`` / ``yjs_update`` /
``yjs_awareness`` from its Vue component.

Socket.IO handlers are lazily registered on first room preparation, so processes that
never opt in pay zero cost. Rooms are evicted when the last client leaves.
"""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from . import core, optional_features

try:
    from pycrdt import Doc as _PycrdtDoc
    optional_features.register('pycrdt')
except ImportError:
    _PycrdtDoc = None  # type: ignore[assignment, misc]

AccessCheck = Callable[[str, str], bool | Awaitable[bool]]
'''Callable ``(doc_id, sid) -> bool`` invoked on every join; may be async.'''

# Bytes payloads larger than this are applied via ``asyncio.to_thread`` to keep the
# event loop responsive (pycrdt's Rust calls are blocking).
_OFFLOAD_BYTES = 32 * 1024

_rooms: dict[str, _Room] = {}
_access_checks: dict[str, list[AccessCheck]] = {}
_handlers_installed = False


class _Room:

    def __init__(self, doc_id: str) -> None:
        assert _PycrdtDoc is not None
        self.doc_id = doc_id
        self.doc = _PycrdtDoc()
        self.sids: set[str] = set()


def ensure_handlers_installed() -> None:
    """Install Socket.IO handlers if needed; idempotent.

    Call this from an element's opt-in path (e.g. ``ui.codemirror.with_crdt(...)``).
    The room itself is created lazily on the first client ``yjs_join``.
    """
    _install_handlers_once()


def register_access_check(doc_id: str, check: AccessCheck) -> None:
    """Register an access-check callable for ``doc_id``.

    Multiple checks for the same ``doc_id`` are AND-combined. Without any registered
    check the room is open to any connected client (matches ``ui.codemirror`` and other
    NiceGUI elements whose URLs already serve as soft auth).
    """
    ensure_handlers_installed()
    _access_checks.setdefault(doc_id, []).append(check)


async def _check_access(doc_id: str, sid: str) -> bool:
    for check in _access_checks.get(doc_id, ()):
        result = check(doc_id, sid)
        if asyncio.iscoroutine(result):
            result = await result
        if not result:
            return False
    return True


def _install_handlers_once() -> None:
    global _handlers_installed  # pylint: disable=global-statement # noqa: PLW0603
    if _handlers_installed:
        return
    if _PycrdtDoc is None:
        raise RuntimeError(
            'pycrdt is not installed; install with `pip install "nicegui[crdt]"` '
            'or `pip install pycrdt` to use ui.codemirror.with_crdt(...).'
        )
    sio = core.sio

    @sio.on('yjs_join')
    async def _on_join(sid: str, data: dict[str, Any]) -> None:
        doc_id = data.get('doc_id')
        if not isinstance(doc_id, str):
            return
        if not await _check_access(doc_id, sid):
            return
        room = _rooms.setdefault(doc_id, _Room(doc_id))
        room.sids.add(sid)
        await sio.enter_room(sid, _sio_room(doc_id))
        state: bytes = room.doc.get_update()
        await sio.emit('yjs_init', {'doc_id': doc_id, 'update': state}, to=sid)

    @sio.on('yjs_update')
    async def _on_update(sid: str, data: dict[str, Any]) -> None:
        doc_id = data.get('doc_id')
        update = data.get('update')
        if not isinstance(doc_id, str) or not isinstance(update, (bytes, bytearray)):
            return
        room = _rooms.get(doc_id)
        if room is None or sid not in room.sids:
            return
        update_bytes = bytes(update)
        if len(update_bytes) > _OFFLOAD_BYTES:
            await asyncio.to_thread(room.doc.apply_update, update_bytes)
        else:
            room.doc.apply_update(update_bytes)
        await sio.emit(
            'yjs_update',
            {'doc_id': doc_id, 'update': update_bytes},
            room=_sio_room(doc_id),
            skip_sid=sid,
        )

    @sio.on('yjs_awareness')
    async def _on_awareness(sid: str, data: dict[str, Any]) -> None:
        doc_id = data.get('doc_id')
        update = data.get('update')
        if not isinstance(doc_id, str) or not isinstance(update, (bytes, bytearray)):
            return
        room = _rooms.get(doc_id)
        if room is None or sid not in room.sids:
            return
        await sio.emit(
            'yjs_awareness',
            {'doc_id': doc_id, 'update': bytes(update), 'sid': sid},
            room=_sio_room(doc_id),
            skip_sid=sid,
        )

    @sio.on('yjs_leave')
    async def _on_leave(sid: str, data: dict[str, Any]) -> None:
        doc_id = data.get('doc_id')
        if isinstance(doc_id, str):
            await _drop_client(sid, doc_id)

    @sio.on('disconnect')
    async def _on_disconnect(sid: str) -> None:  # pylint: disable=unused-variable
        # Coexists with NiceGUI core's disconnect handler — Socket.IO fans out to all.
        for doc_id in list(_rooms):
            if sid in _rooms[doc_id].sids:
                await _drop_client(sid, doc_id)

    _handlers_installed = True


async def _drop_client(sid: str, doc_id: str) -> None:
    room = _rooms.get(doc_id)
    if room is None:
        return
    room.sids.discard(sid)
    await core.sio.leave_room(sid, _sio_room(doc_id))
    # Tell remaining clients to forget this peer's awareness state.
    await core.sio.emit(
        'yjs_awareness_remove',
        {'doc_id': doc_id, 'sid': sid},
        room=_sio_room(doc_id),
    )
    if not room.sids:
        _rooms.pop(doc_id, None)


def _sio_room(doc_id: str) -> str:
    return f'yjs:{doc_id}'
