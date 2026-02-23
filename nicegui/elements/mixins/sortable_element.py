from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from typing_extensions import Self

from ...events import Handler

if TYPE_CHECKING:
    from ...element import Element
    from ..sortable.sortable_controller import SortableEventArguments


class SortableElement:
    """Mixin that adds sortable drag & drop to any container element.

    Usage::

        with ui.column().sortable(on_sort_end=handle) as col:
            ui.label('A').sortable_item(data='first')
            ui.label('B').sortable_item(data='second')

        # Programmatic control:
        col.sortable_controller.disable()
        col.sortable_controller.enable()
    """

    _sortable_controller: SortableController | None

    def sortable(
        self,
        options: dict[str, Any] | None = None,
        *,
        on_sort_end: Handler[SortableEventArguments] | None = None,
        animation: int = 150,
        handle: str | None = None,
        group: str | dict[str, Any] | None = None,
        filter: str | None = None,
        ghost_class: str = 'opacity-50',
    ) -> Self:
        """Make this container's children sortable via drag & drop using SortableJS.

        :param options: raw SortableJS options dictionary (overrides named parameters)
        :param on_sort_end: callback when a drag operation ends
        :param animation: animation speed in ms (default: 150)
        :param handle: CSS selector for drag handle elements
        :param group: group name or config for cross-container dragging
        :param filter: CSS selector for elements that should not be draggable
        :param ghost_class: CSS class applied to the ghost element (default: 'opacity-50')
        """
        # Lazy import to avoid circular dependencies and only load SortableJS when needed
        from ..sortable import sortable_controller as sc  # pylint: disable=import-outside-toplevel

        element = cast('Element', self)
        opts = sc._build_sortable_options(
            options=options,
            animation=animation,
            handle=handle,
            group=group,
            filter=filter,
            ghost_class=ghost_class,
        )
        controller = SortableController(element, opts)
        self._sortable_controller = controller

        sc._register_sort_end_event(element, on_sort_end)
        sc._init_sortable(element, opts)

        return cast(Self, self)

    @property
    def sortable_controller(self) -> SortableController | None:
        """The sortable controller for this element, or None if not sortable."""
        return getattr(self, '_sortable_controller', None)

    def sortable_item(self, *, data: Any = None) -> Self:
        """Mark this element as a sortable item with optional attached data.

        The data can be retrieved from the element later when handling sort events.

        :param data: arbitrary data to associate with this draggable item
        """
        element = cast('Element', self)
        element._sortable_data = data  # type: ignore[attr-defined]
        return cast(Self, self)


class SortableController:
    """Controls sortable behavior on a container element.

    Provides methods to enable/disable sorting and update options programmatically.
    """

    def __init__(self, element: Element, options: dict[str, Any]) -> None:
        self._element = element
        self._options = options

    def enable(self) -> None:
        """Enable drag & drop sorting."""
        self._element.client.run_javascript(
            f'document.getElementById("c{self._element.id}")?._nicegui_sortable?.option("disabled", false);'
        )

    def disable(self) -> None:
        """Disable drag & drop sorting."""
        self._element.client.run_javascript(
            f'document.getElementById("c{self._element.id}")?._nicegui_sortable?.option("disabled", true);'
        )

    def set_option(self, key: str, value: Any) -> None:
        """Set a SortableJS option at runtime.

        :param key: SortableJS option name
        :param value: option value
        """
        from ... import json as nicegui_json  # pylint: disable=import-outside-toplevel
        self._element.client.run_javascript(
            f'document.getElementById("c{self._element.id}")?._nicegui_sortable'
            f'?.option({nicegui_json.dumps(key)}, {nicegui_json.dumps(value)});'
        )

    def destroy(self) -> None:
        """Destroy the SortableJS instance and clean up."""
        self._element.client.run_javascript(
            f'const el = document.getElementById("c{self._element.id}");'
            f'if (el?._nicegui_sortable) {{ el._nicegui_sortable.destroy(); el._nicegui_sortable = null; }}'
        )
