"""SPIKE: a real NiceGUI app whose On Air relay client runs without aiohttp."""
import importlib.util
import os

from nicegui import air, ui

# loaded by explicit path so import-sorting autofixers cannot hoist it above a sys.path tweak
_spec = importlib.util.spec_from_file_location(
    'no_aiohttp', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'no_aiohttp.py'))
no_aiohttp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(no_aiohttp)

print('[app] shim installed:', no_aiohttp.install(only_if_missing=True), flush=True)

air.RELAY_HOST = f'http://127.0.0.1:{os.environ["RELAY_PORT"]}/'


@ui.page('/')
def index() -> None:
    ui.label('HELLO FROM AIR SPIKE')


ui.run(port=int(os.environ['APP_PORT']), on_air='SPIKE-TOKEN', show=False, reload=False)
