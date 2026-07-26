from nicegui import app as _app
import os

from nicegui import ui

box = ui.label('target').classes('p-2')
ui.button('add', on_click=lambda: box.classes('p-8 bg-rose-500 text-white rounded-xl hover:bg-rose-600 md:p-12')) \
    .props('id=addbtn')
ui.button('exotic', on_click=lambda: box.classes('mask-none')).props('id=exoticbtn')

_app.config.precompile_tailwind = os.environ.get('NG_PRECOMPILE', '1') == '1'
ui.run(port=int(os.environ['NICEGUI_PORT']), show=False, reload=False)
