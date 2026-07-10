from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from ..context import context
from ..element import Element
from ..events import Handler, UiEventArguments, handle_event
from .mixins.value_element import ValueElement


@dataclass(kw_only=True, slots=True)
class PopupEditResult(UiEventArguments):
    """Result carried out of an ``edit(...)`` call (also passed to ``on_submit``)."""
    value: Any
    '''the edited value, or ``None`` on cancel/dismiss'''
    cell: Any
    '''the opaque coordinates passed into ``edit(cell=...)`` -- tells you *which* cell'''


class PopupEditAwaitable(ValueElement[bool]):
    """Popup Edit (awaitable-singleton shape) -- PROTOTYPE for PR #5613 design comparison.

    This is the ALTERNATIVE design to the ``ui.popup_edit`` container primitive.

    Instead of being a dumb container whose children bind their own values, this is a
    single, reusable editor that you *drive imperatively and await*::

        value = await popup.edit('hello', target='#cell-2-3', cell=(2, 3))

    - ONE instance serves MANY anchors (e.g. every cell of a table): it is repositioned
      per call via Quasar ``QMenu``'s ``target`` selector, so you do not create N popups.
    - ``edit(...)`` opens the editor seeded with ``initial``, waits for the user, and
      RESOLVES to the edited value on confirm, or ``None`` on cancel/dismiss.
    - It carries the ``cell`` coordinates through, so the caller knows *which* cell
      resolved (also delivered to ``on_submit`` for a non-awaiting/event-driven style).

    Built on ``QMenu`` (not ``QPopupEdit``) precisely because QPopupEdit anchors to its
    parent slot at creation time and cannot be cheaply re-anchored to an arbitrary cell.
    """

    def __init__(self, *,
                 on_submit: Handler[PopupEditResult] | None = None,
                 ) -> None:
        # Live at the page root, unattached to any anchor: it is retargeted per call.
        with context.client.content:
            super().__init__(tag='q-menu', value=False)
        # Programmatic-only: don't hook the target element's own click events.
        self._props['no-parent-event'] = True
        self._props['anchor'] = 'bottom left'
        self._props['self'] = 'top left'

        self._result: Any = None
        self._submitted: asyncio.Event | None = None
        self._current_cell: Any = None
        self._on_submit = on_submit

        # Rebuilt lazily inside edit() so the caller can supply the editor widget factory.
        self._input: ValueElement | None = None
        self._build_default_body()

    # ------------------------------------------------------------------ body
    def _build_default_body(self) -> None:
        from .button import Button
        from .input import Input
        from .row import Row
        with self:
            with Element('q-card').props('flat').style('padding: 8px; min-width: 180px;'):
                self._input = Input().props('dense autofocus outlined')
                with Row().classes('w-full justify-end q-gutter-xs').style('margin-top: 6px;'):
                    Button('Cancel', on_click=self._cancel).props('flat dense')
                    Button('OK', on_click=self._confirm).props('dense color=primary')

    # ------------------------------------------------------------- awaitable
    @property
    def submitted(self) -> asyncio.Event:
        if self._submitted is None:
            self._submitted = asyncio.Event()
        return self._submitted

    async def edit(self,
                   initial: Any = '',
                   *,
                   target: str | None = None,
                   cell: Any = None,
                   ) -> Any:
        """Open the editor seeded with ``initial`` and await the result.

        :param initial: value to prefill the editor with
        :param target: CSS selector of the anchor element to position the popup at
                       (e.g. ``'#cell-2-3'``); ``None`` keeps the previous anchor
        :param cell: opaque coordinates carried through to the result / ``on_submit``
        :return: the edited value on confirm, or ``None`` on cancel/dismiss
        """
        self._current_cell = cell
        self._result = None
        self.submitted.clear()

        if self._input is not None:
            self._input.value = initial
        if target is not None:
            self._props['target'] = target
        self.value = True  # show
        self.update()

        await self.submitted.wait()

        self.value = False  # hide
        self.update()
        return self._result

    # --------------------------------------------------------------- handlers
    def _confirm(self) -> None:
        self._resolve(self._input.value if self._input is not None else None)

    def _cancel(self) -> None:
        self._resolve(None)

    def _resolve(self, result: Any) -> None:
        self._result = result
        handle_event(self._on_submit, PopupEditResult(sender=self, client=self.client,
                                                      value=result, cell=self._current_cell))
        self.submitted.set()

    def _handle_value_change(self, value: Any) -> None:
        super()._handle_value_change(value)
        # If the menu was dismissed by clicking away / ESC, resolve as a cancel.
        if not value and self._submitted is not None and not self._submitted.is_set():
            self._resolve(None)
