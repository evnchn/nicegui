from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

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


def _build_sortable_options(
    *,
    options: dict[str, Any] | None = None,
    animation: int = 150,
    handle: str | None = None,
    group: str | dict[str, Any] | None = None,
    filter: str | None = None,
    ghost_class: str = 'opacity-50',
    disabled: bool = False,
) -> dict[str, Any]:
    """Build the SortableJS options dictionary."""
    opts: dict[str, Any] = {
        'animation': animation,
        'ghostClass': ghost_class,
        'disabled': disabled,
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


def _init_sortable(element: Element, options: dict[str, Any]) -> None:
    """Initialize SortableJS on the element via run_javascript.

    If the event loop is not running yet (auto-page mode), the JS is deferred
    to when the client connects.
    """
    from ... import core as _core  # pylint: disable=import-outside-toplevel

    js_code = _INIT_JS.format(
        element_id=element.id,
        options=json.dumps(options),
    )
    if _core.loop:
        element.client.run_javascript(js_code)
    else:
        element.client.on_connect(lambda: element.client.run_javascript(js_code))


def _register_sort_end_event(
    element: Element,
    handler: Handler[SortableEventArguments] | None,
) -> None:
    """Register the sort-end event on the element.

    Always syncs the server-side element tree to match the new order.
    If a user handler is provided, it is called after the sync.
    """
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
                # Same container: reorder within the slot
                parent_slot = item_element.parent_slot
                if parent_slot is not None:
                    parent_slot.children.remove(item_element)
                    parent_slot.children.insert(new_index, item_element)
            else:
                # Cross-container: move to the target container
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
