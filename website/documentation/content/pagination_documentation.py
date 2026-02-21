from nicegui import ui

from . import doc

doc.metadata(source_url='https://github.com/zauberzeug/nicegui/blob/main/nicegui/elements/pagination.py')


@doc.demo(ui.pagination)
def main_demo() -> None:
    p = ui.pagination(1, 5, direction_links=True)
    ui.label().bind_text_from(p, 'value', lambda v: f'Page {v}')


doc.reference(ui.pagination)
