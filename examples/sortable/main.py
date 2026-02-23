#!/usr/bin/env python3
"""Sortable drag & drop demo using the mixin API (Approach 2)."""
from nicegui import ui

# --- Basic sortable list ---
ui.label('Basic Sortable List').classes('text-h5')

items = ['Apple', 'Banana', 'Cherry', 'Date', 'Elderberry']


def handle_sort(e) -> None:
    """Sync the Python list with the new order after a drag."""
    item = items.pop(e.old_index)
    items.insert(e.new_index, item)
    result.set_text(f'Order: {", ".join(items)}')


with ui.column().sortable(on_sort_end=handle_sort, ghost_class='opacity-30'):
    for item in items:
        with ui.card().classes('w-full cursor-grab'):
            ui.label(item)

result = ui.label(f'Order: {", ".join(items)}')

# --- Cross-container drag demo ---
ui.separator()
ui.label('Cross-container drag & drop').classes('text-h5')

with ui.row().classes('w-full gap-4'):
    with ui.column().sortable(group='shared', ghost_class='opacity-30') \
            .classes('w-1/3 p-4 bg-blue-50 min-h-[200px]'):
        for i in range(3):
            with ui.card().classes('w-full cursor-grab'):
                ui.label(f'A-{i}')

    with ui.column().sortable(group='shared', ghost_class='opacity-30') \
            .classes('w-1/3 p-4 bg-green-50 min-h-[200px]'):
        for i in range(3):
            with ui.card().classes('w-full cursor-grab'):
                ui.label(f'B-{i}')

# --- Handle demo ---
ui.separator()
ui.label('Drag handle demo').classes('text-h5')

with ui.column().sortable(handle='.drag-handle', ghost_class='opacity-30'):
    for i in range(4):
        with ui.row().classes('items-center w-full'):
            ui.icon('drag_indicator').classes('drag-handle cursor-grab text-grey-6')
            ui.label(f'Item with handle {i}')

# --- Enable/disable demo ---
ui.separator()
ui.label('Enable/disable demo').classes('text-h5')

with ui.column().sortable(ghost_class='opacity-30') as toggleable:
    for i in range(4):
        with ui.card().classes('w-full cursor-grab'):
            ui.label(f'Toggleable {i}')

controller = toggleable.sortable_controller
with ui.row():
    ui.button('Disable sorting', on_click=lambda: controller.disable())
    ui.button('Enable sorting', on_click=lambda: controller.enable())

ui.run()
