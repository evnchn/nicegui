from nicegui import ui

from . import doc

doc.metadata(source_url='https://github.com/zauberzeug/nicegui/blob/main/nicegui/elements/row.py')


@doc.demo(ui.row)
def main_demo() -> None:
    with ui.row():
        ui.label('label 1')
        ui.label('label 2')
        ui.label('label 3')


doc.reference(ui.row)
