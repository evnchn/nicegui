from nicegui import ui

from . import doc

doc.metadata(source_url='https://github.com/zauberzeug/nicegui/blob/main/nicegui/functions/page_title.py')


@doc.demo(ui.page_title)
def main_demo() -> None:
    ui.button('Change page title', on_click=lambda: ui.page_title('New Title'))
