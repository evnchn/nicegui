from nicegui import ui

from . import doc

doc.metadata(source_url='https://github.com/zauberzeug/nicegui/blob/main/nicegui/elements/knob.py')


@doc.demo(ui.knob)
def main_demo() -> None:
    knob = ui.knob(0.3, show_value=True)

    with ui.knob(color='orange', track_color='grey-2').bind_value(knob, 'value'):
        ui.icon('volume_up')


doc.reference(ui.knob)
