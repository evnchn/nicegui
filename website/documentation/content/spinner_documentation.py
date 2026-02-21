from nicegui import ui

from . import doc

doc.metadata(source_url='https://github.com/zauberzeug/nicegui/blob/main/nicegui/elements/spinner.py')


@doc.demo(ui.spinner)
def main_demo() -> None:
    with ui.row():
        ui.spinner(size='lg')
        ui.spinner('audio', size='lg', color='green')
        ui.spinner('dots', size='lg', color='red')


doc.reference(ui.spinner)
