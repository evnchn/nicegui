"""Spike app: '/' is a hello-world page (size measurement),
'/dynamic' adds an ESM-backed element (echart) AFTER load via a button click."""
import sys

from nicegui import ui


@ui.page('/')
def index():
    ui.label('Hello world')


@ui.page('/dynamic')
def dynamic():
    container = ui.column()

    def add():
        with container:
            ui.echart({
                'xAxis': {'type': 'value'},
                'yAxis': {'type': 'category', 'data': ['A', 'B']},
                'series': [{'type': 'bar', 'data': [0.1, 0.2]}],
            }).classes('w-96 h-64').classes('mychart')
    ui.button('add echart', on_click=add).classes('addbtn')


ui.run(port=int(sys.argv[1]), reload=False, show=False)
