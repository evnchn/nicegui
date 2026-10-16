from nicegui import ui

from . import doc


@doc.demo(ui.dashboard)
def main_demo() -> None:
    with ui.dashboard(columns=4, cell_height=50).classes('w-full'):
        with ui.dashboard_item(x=0, y=0, w=2, h=2):
            with ui.card().props('flat bordered').classes('w-full h-full'):
                ui.label('Temperature')
                ui.label('21 °C').classes('text-2xl')
        with ui.dashboard_item(x=2, y=0, w=2, h=3):
            with ui.card().props('flat bordered').classes('w-full h-full p-0'):
                ui.echart({
                    'xAxis': {'type': 'category', 'show': False},
                    'yAxis': {'type': 'value', 'show': False},
                    'series': [{'type': 'line', 'data': [12, 18, 15, 22, 19]}],
                }).classes('w-full h-full')
        with ui.dashboard_item(w=2, h=1):
            with ui.card().props('flat bordered').classes('w-full h-full justify-center'):
                ui.checkbox('Ship it')


@doc.demo('Reacting to Layout Changes', '''
    When the user moves or resizes tiles, `x`, `y`, `w` and `h` of every affected `ui.dashboard_item` are updated
    and the `on_change` callback receives the changed items.
    The `layout` property returns the geometry of all tiles, e.g. to store it in `app.storage.user`.
''')
def layout_changes() -> None:
    with ui.dashboard(columns=4, cell_height=50, on_change=lambda d: label.set_text(str(d.sender.layout))) \
            .classes('w-full') as dashboard:
        for i in range(3):
            with ui.dashboard_item(x=i, y=0, w=1, h=1):
                ui.label(f'Tile {i}').classes('w-full h-full bg-blue-100 p-2 rounded')
    label = ui.label(str(dashboard.layout))


@doc.demo('Changing Tiles from Python', '''
    Setting `x`, `y`, `w` or `h` moves or resizes a tile; other tiles make room.
    `min_w`, `max_w`, `min_h` and `max_h` limit the size, both for the user and for Python.
    Tiles can also be added and removed at runtime,
    and `editable` locks the whole layout.
''')
def change_from_python() -> None:
    with ui.dashboard(columns=4, cell_height=50).classes('w-full') as dashboard:
        with ui.dashboard_item(x=0, y=0, w=1, h=1, max_w=3) as item:
            ui.label('Grow me (up to 3)').classes('w-full h-full bg-green-100 p-2 rounded')

    def add() -> None:
        with dashboard, ui.dashboard_item(w=1, h=1):
            ui.label('New').classes('w-full h-full bg-orange-100 p-2 rounded')

    with ui.row():
        ui.button('Grow', on_click=lambda: setattr(item, 'w', item.w + 1))
        ui.button('Add', on_click=add)
        ui.switch('Editable', value=True).bind_value(dashboard, 'editable')


doc.reference(ui.dashboard)
doc.reference(ui.dashboard_item, title='Reference for ui.dashboard_item')
