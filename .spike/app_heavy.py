from nicegui import app as _app
import os

from nicegui import ui

with ui.header().classes('items-center justify-between bg-blue-600 shadow-lg'):
    ui.label('Dashboard').classes('text-2xl font-bold text-white tracking-wide')
    ui.button('Menu', icon='menu').classes('hover:bg-blue-700 transition duration-300')
with ui.row().classes('w-full gap-4 p-4 max-md:flex-col'):
    for i in range(3):
        with ui.card().classes('flex-1 shadow-lg rounded-xl hover:shadow-2xl transition dark:bg-gray-800'):
            ui.label(f'Card {i}').classes('text-lg font-semibold text-gray-900 dark:text-gray-100')
            ui.label('Body').classes('text-sm text-gray-500 leading-relaxed')
            ui.button('Act').classes('mt-2 w-full bg-emerald-500 hover:bg-emerald-600 rounded-lg')
with ui.grid().classes('grid-cols-[1fr_auto_1fr] gap-8 p-6 mx-auto max-w-[1250px] border rounded'):
    ui.input('Name').classes('w-full focus:ring-2 focus:ring-blue-400')
    ui.select(['a', 'b'], value='a').classes('w-full md:w-64')
    ui.checkbox('Check').classes('accent-pink-500')
    ui.slider(min=0, max=10, value=5).classes('w-[200px]')
    ui.table(columns=[{'name': 'a', 'label': 'A', 'field': 'a'}], rows=[{'a': 1}]).classes('w-full text-xs')
    ui.spinner().classes('animate-spin text-indigo-500')
ui.label('footer').classes('mt-8 text-center text-xs uppercase tracking-widest opacity-50')

_app.config.precompile_tailwind = os.environ.get('NG_PRECOMPILE', '1') == '1'
ui.run(port=int(os.environ['NICEGUI_PORT']), show=False, reload=False)
