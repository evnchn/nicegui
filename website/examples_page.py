from nicegui import ui

from .examples import examples
from .seo import page_seo_html
from .style import example_link, link_target, section_heading


def create() -> None:
    ui.page_title('Examples | NiceGUI')
    ui.add_head_html(page_seo_html(
        title='NiceGUI Examples - Python UI Code Samples and Demos',
        description='Browse in-depth NiceGUI examples including authentication, '
                    'chat apps, todo lists, and more. '
                    'See real Python GUI code with live demos.',
        path='/examples',
    ))
    with ui.column().classes('w-full p-8 lg:p-16 max-w-[1600px] mx-auto'):
        link_target('examples')
        section_heading('In-depth examples', 'Pick your *solution*')
        with ui.row().classes('w-full text-lg leading-tight grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4'):
            for example in examples:
                example_link(example)
