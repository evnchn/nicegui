from __future__ import annotations

from typing import TYPE_CHECKING

from . import core
from .slot import Slot

if TYPE_CHECKING:
    from .client import Client


class Context:

    @property
    def slot_stack(self) -> list[Slot]:
        """Return the slot stack of the current asyncio task."""
        stack = Slot.get_stack()
        if not stack and not core.script_mode and not core.app.is_started:
            # create a pseudo client to "survive" until reaching `ui.run()`
            from .client import Client  # pylint: disable=import-outside-toplevel,cyclic-import
            from .page import page  # pylint: disable=import-outside-toplevel,cyclic-import
            if not Client.instances:  # in case some kind of dummy client is already created
                core.script_mode = True
                core.script_client = Client(page('/')).__enter__()  # pylint: disable=unnecessary-dunder-call
                stack = Slot.get_stack()
        return stack

    @property
    def slot(self) -> Slot:
        """Return the current slot."""
        slot_stack = self.slot_stack
        if not slot_stack:
            raise RuntimeError('The current slot cannot be determined because the slot stack for this task is empty.\n'
                               'This may happen if you try to create UI from a background task.\n'
                               'To fix this, enter the target slot explicitly using `with container_element:`.')
        return slot_stack[-1]

    @property
    def client(self) -> Client:
        """Return the current client."""
        return self.slot.parent.client

    @property
    def nonce(self) -> str:
        """Return the CSP nonce for the current request, or an empty string when CSP is disabled.

        Intended for user code that injects its own inline ``<script>``/``<style>`` tags via
        ``ui.add_head_html`` or ``ui.add_body_html`` under a strict Content Security Policy.

        WARNING: the nonce is a trust token. Only stamp it on content that the server fully
        controls. Never embed the nonce into output derived from untrusted user input.
        """
        from .storage import request_contextvar  # pylint: disable=import-outside-toplevel,cyclic-import
        request = request_contextvar.get()
        if request is None:
            return ''
        return getattr(request.state, 'csp_nonce', '')


context = Context()
