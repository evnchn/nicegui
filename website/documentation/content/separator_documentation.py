from nicegui import ui

from . import doc

doc.metadata(source_url='https://github.com/zauberzeug/nicegui/blob/main/nicegui/elements/separator.py')


@doc.demo(ui.separator)
def main_demo() -> None:
    ui.label('text above')
    ui.separator()
    ui.label('text below')


doc.reference(ui.separator)
