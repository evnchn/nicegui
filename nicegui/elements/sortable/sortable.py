from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ... import core as _core
from ... import json
from ...dataclasses import KWONLY_SLOTS
from ...events import GenericEventArguments, Handler, UiEventArguments, handle_event

if TYPE_CHECKING:
    from ...element import Element


@dataclass(**KWONLY_SLOTS)
class SortableEventArguments(UiEventArguments):
    """Event arguments for sortable sort-end events."""

    old_index: int
    new_index: int
    item_id: int
    from_id: int
    to_id: int


_INIT_JS = '''\
(async () => {{
    const {{ Sortable }} = await import("nicegui-sortable");
    const el = document.getElementById("c{element_id}");
    if (!el) return;
    if (el._nicegui_sortable) el._nicegui_sortable.destroy();
    const sortable = Sortable.create(el, {{
        ...{options},
        onEnd: (evt) => {{
            if (evt.from === evt.to) {{
                const el_data = mounted_app.elements[{element_id}];
                const slot = el_data.slots?.default || el_data;
                const children = slot.ids || el_data.children;
                if (children) {{
                    const [moved] = children.splice(evt.oldIndex, 1);
                    children.splice(evt.newIndex, 0, moved);
                }}
            }}
            el.dispatchEvent(new CustomEvent("sortend", {{
                detail: {{
                    oldIndex: evt.oldIndex,
                    newIndex: evt.newIndex,
                    itemId: parseInt(evt.item.id.replace("c", "")),
                    fromId: parseInt(evt.from.id.replace("c", "")),
                    toId: parseInt(evt.to.id.replace("c", "")),
                }}
            }}));
        }},
    }});
    el._nicegui_sortable = sortable;
}})();\
'''


class Sortable:
    """Companion object that attaches SortableJS drag & drop behavior to any NiceGUI container.

    Created via ``element.make_sortable()``, not directly. The container stays its original type
    (``ui.column`` remains a ``ui.column``), and this object provides methods to control the
    sorting behavior.

    Usage::

        with ui.column() as column:
            ui.label('A')
            ui.label('B')
            with ui.row():
                ui.icon('drag_handle').classes('handle')
                ui.label('C')

        sortable = column.make_sortable(handle='.handle', on_sort_end=lambda e: print(e))
        sortable.disable()
    """

    def __init__(
        self,
        element: Element,
        *,
        options: dict[str, Any] | None = None,
        on_sort_end: Handler[SortableEventArguments] | None = None,
        animation: int = 150,
        handle: str | None = None,
        group: str | dict[str, Any] | None = None,
        filter: str | None = None,
        ghost_class: str = 'opacity-50',
    ) -> None:
        self._element = element
        self._options = self._build_options(
            options=options,
            animation=animation,
            handle=handle,
            group=group,
            filter=filter,
            ghost_class=ghost_class,
        )
        self._register_sort_end_event(on_sort_end)
        self._init_js()

    @staticmethod
    def _build_options(
        *,
        options: dict[str, Any] | None = None,
        animation: int = 150,
        handle: str | None = None,
        group: str | dict[str, Any] | None = None,
        filter: str | None = None,
        ghost_class: str = 'opacity-50',
    ) -> dict[str, Any]:
        opts: dict[str, Any] = {
            'animation': animation,
            'ghostClass': ghost_class,
        }
        if handle is not None:
            opts['handle'] = handle
        if group is not None:
            opts['group'] = group
        if filter is not None:
            opts['filter'] = filter
        if options:
            opts.update(options)
        return opts

    def _init_js(self) -> None:
        """Initialize SortableJS on the element's DOM node."""
        js_code = _INIT_JS.format(
            element_id=self._element.id,
            options=json.dumps(self._options),
        )
        if _core.loop:
            self._element.client.run_javascript(js_code)
        else:
            self._element.client.on_connect(lambda: self._element.client.run_javascript(js_code))

    def _register_sort_end_event(self, handler: Handler[SortableEventArguments] | None) -> None:
        """Register the sort-end event.

        Always syncs the server-side element tree.
        Calls the user handler (if any) after sync.
        """
        element = self._element

        def _handle_sort_end(e: GenericEventArguments) -> None:
            old_index = e.args['oldIndex']
            new_index = e.args['newIndex']
            from_id = e.args['fromId']
            to_id = e.args['toId']
            item_id = e.args['itemId']

            # Sync the server-side element tree
            item_element = element.client.elements.get(item_id)
            if item_element is not None:
                if from_id == to_id:
                    parent_slot = item_element.parent_slot
                    if parent_slot is not None:
                        parent_slot.children.remove(item_element)
                        parent_slot.children.insert(new_index, item_element)
                else:
                    target_container = element.client.elements.get(to_id)
                    if target_container is not None:
                        item_element.move(target_container, target_index=new_index)

            if handler is not None:
                args = SortableEventArguments(
                    sender=element,
                    client=element.client,
                    old_index=old_index,
                    new_index=new_index,
                    item_id=item_id,
                    from_id=from_id,
                    to_id=to_id,
                )
                handle_event(handler, args)

        element.on(
            'sort-end',
            _handle_sort_end,
            args=None,
            js_handler='(event) => emit(event.detail)',
        )

    def on_sort_end(self, handler: Handler[SortableEventArguments]) -> Sortable:
        """Add an additional sort-end handler.

        :param handler: callback when a drag operation ends
        """
        element = self._element

        def _handle(e: GenericEventArguments) -> None:
            args = SortableEventArguments(
                sender=element,
                client=element.client,
                old_index=e.args['oldIndex'],
                new_index=e.args['newIndex'],
                item_id=e.args['itemId'],
                from_id=e.args['fromId'],
                to_id=e.args['toId'],
            )
            handle_event(handler, args)

        element.on(
            'sort-end',
            _handle,
            args=None,
            js_handler='(event) => emit(event.detail)',
        )
        return self

    @property
    def element(self) -> Element:
        """The container element this Sortable is attached to."""
        return self._element

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
        self._element.client.run_javascript(
            f'document.getElementById("c{self._element.id}")?._nicegui_sortable'
            f'?.option({json.dumps(key)}, {json.dumps(value)});'
        )

    def destroy(self) -> None:
        """Destroy the SortableJS instance and clean up."""
        self._element.client.run_javascript(
            f'const el = document.getElementById("c{self._element.id}");'
            f'if (el?._nicegui_sortable) {{ el._nicegui_sortable.destroy(); el._nicegui_sortable = null; }}'
        )
