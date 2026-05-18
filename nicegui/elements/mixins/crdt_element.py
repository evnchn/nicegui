from typing_extensions import Self

from ... import yjs_room
from ...element import Element
from ...yjs_room import AccessCheck


class CrdtElement(Element):
    """Mixin that exposes ``with_crdt(doc_id, *, access_check=None)`` for opt-in CRDT collaboration.

    Elements that inherit this mixin become eligible to share a Yjs document across
    browser sessions via ``nicegui.yjs_room``. Mixing this in is the *only* server-side
    plumbing required; each element is responsible for the client-side Y.Doc binding
    in its Vue component (reading the ``crdt-doc-id`` prop and attaching an appropriate
    plugin — ``y-codemirror.next`` for codemirror, ``y-prosemirror`` for ProseMirror-based
    editors, etc.).

    The JS-side Yjs runtime is currently bundled per-consumer (each element's bundle
    includes its own yjs copy). A future iteration should hoist yjs into a shared
    ``nicegui-yjs`` ESM module to avoid duplication when multiple CRDT-capable
    elements coexist on a page.
    """

    def with_crdt(self, doc_id: str, *, access_check: AccessCheck | None = None) -> Self:
        """Enable real-time collaborative editing on this element via Yjs (CRDT).

        All elements sharing the same ``doc_id`` — across any number of browser tabs
        connected to a *single* NiceGUI server process — edit a single shared document.
        State is held in a server-side ``pycrdt.Doc`` and relayed over the existing
        Socket.IO transport; no individual server-to-client value sync is performed
        while collaboration is on.

        Multi-process deployments are **not** transparently supported: the room
        registry lives in a per-process in-memory dict, so unless a load balancer
        pins clients sharing a ``doc_id`` to the same worker, they will edit
        divergent copies.

        ``doc_id`` is the room name; any client that knows it can join, so treat it
        as a soft secret (long unguessable strings) or supply ``access_check`` to
        gate joins. ``access_check`` receives ``(doc_id, sid)`` and may be sync or
        async; return ``False`` to deny.

        To seed initial content, fetch the server-side pycrdt ``Doc`` via
        ``nicegui.yjs_room.get_doc(doc_id)`` before any client connects. The Y.Text
        key the element binds to is element-specific (see each element's documentation).

        Requires the ``[crdt]`` extra: ``pip install "nicegui[crdt]"``.

        :param doc_id: name of the shared room (clients sharing this id share the document)
        :param access_check: optional callable ``(doc_id, sid) -> bool`` to gate joins
        """
        self._props['crdt-doc-id'] = doc_id
        if access_check is not None:
            yjs_room.register_access_check(doc_id, access_check)
        else:
            yjs_room.ensure_handlers_installed()
        return self
