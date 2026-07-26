from nicegui import app as _app
import os

from nicegui import ui

ui.label('Hello world')

_app.config.precompile_tailwind = os.environ.get('NG_PRECOMPILE', '1') == '1'
ui.run(port=int(os.environ['NICEGUI_PORT']), show=False, reload=False)
