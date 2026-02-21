from nicegui import ui

from . import doc

doc.metadata(source_url='https://github.com/zauberzeug/nicegui/blob/main/nicegui/elements/code.py')


@doc.demo(ui.code)
def main_demo() -> None:
    ui.code('''
        from nicegui import ui

        ui.label('Code inception!')

        ui.run()
    ''').classes('w-full')


doc.reference(ui.code)
