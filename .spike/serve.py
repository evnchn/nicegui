#!/usr/bin/env python3
"""Serve pages for browser verification. Usage: serve.py <port> [vue]"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
PORT = int(sys.argv[1])
WITH_VUE = 'vue' in sys.argv[2:]

from nicegui import ui  # noqa: E402

if WITH_VUE:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'examples' / 'custom_vue_component'))
    from on_off import OnOff  # type: ignore  # noqa: E402


@ui.page('/')
def index() -> None:
    ui.label('Hello world').mark('hello')
    ui.button('Click me', on_click=lambda: ui.notify('clicked!')).mark('btn')
    ui.input('Name', value='abc')
    ui.select(['a', 'b', 'c'], value='a')
    with ui.tabs() as tabs:
        ui.tab('One')
        ui.tab('Two')
    with ui.tab_panels(tabs, value='One'):
        with ui.tab_panel('One'):
            ui.label('panel one')
        with ui.tab_panel('Two'):
            ui.label('panel two')
    ui.table(columns=[{'name': 'x', 'label': 'X', 'field': 'x'}], rows=[{'x': 1}, {'x': 2}])
    with ui.expansion('more'):
        ui.markdown('**markdown** works')


@ui.page('/slot')
def slot_page() -> None:
    el = ui.element('div')
    el.add_slot('default', '<span id="tpl">rendered from a runtime-compiled template</span>')
    ui.label('slot page').mark('slotpage')


@ui.page('/late')
def late_page() -> None:
    """Page that renders WITHOUT any template, then adds one dynamically after load."""
    container = ui.column()
    ui.label('late page').mark('latepage')

    def add_late() -> None:
        with container:
            el = ui.element('div')
            el.add_slot('default', '<span id="late-tpl">LATE TEMPLATE</span>')
    ui.button('add late template', on_click=add_late).mark('latebtn')


if WITH_VUE:
    @ui.page('/vue')
    def vue_page() -> None:
        OnOff('demo', on_change=lambda e: ui.notify(f'toggled {e.args}'))
        ui.label('vue page').mark('vuepage')


ui.run(port=PORT, show=False, reload=False, prod_js=os.environ.get('PRODJS', '1') == '1')
