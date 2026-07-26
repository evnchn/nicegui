from nicegui import app as _app
import os

from nicegui import ui

with ui.header().classes('items-center justify-between'):
    ui.label('Dashboard').classes('text-2xl font-bold text-white')
    ui.button('Menu', icon='menu').props('flat color=white')
with ui.row().classes('w-full gap-4 p-4'):
    for i in range(3):
        with ui.card().classes('flex-1 shadow-lg rounded-xl'):
            ui.label(f'Card {i}').classes('text-lg font-semibold')
            ui.label('Some body text here').classes('text-sm text-gray-500')
            ui.button('Act').classes('mt-2 w-full')
with ui.column().classes('mx-auto max-w-md gap-2 p-6 border rounded'):
    ui.input('Name').classes('w-full')
    ui.select(['a', 'b'], value='a').classes('w-full')
    ui.checkbox('Check')
    ui.slider(min=0, max=10, value=5)
    ui.table(columns=[{'name': 'a', 'label': 'A', 'field': 'a'}], rows=[{'a': 1}]).classes('w-full')
ui.markdown('**hello** _world_')

_app.config.precompile_tailwind = os.environ.get('NG_PRECOMPILE', '1') == '1'
ui.run(port=int(os.environ['NICEGUI_PORT']), show=False, reload=False)
