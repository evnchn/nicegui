from nicegui import ui

from . import doc

doc.metadata(source_url='https://github.com/zauberzeug/nicegui/blob/main/nicegui/elements/editor.py')


@doc.demo(ui.editor)
def main_demo() -> None:
    editor = ui.editor(placeholder='Type something here')
    ui.markdown().bind_content_from(editor, 'value',
                                    backward=lambda v: f'HTML code:\n```\n{v}\n```')


doc.reference(ui.editor)
