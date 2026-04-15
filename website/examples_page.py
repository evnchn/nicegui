from nicegui import ui

from .components.examples_section import example_card
from .design import section_heading
from .examples import examples
from .seo import apply_page_seo


def create() -> None:
    title = 'NiceGUI Examples - Python UI Code Samples and Demos'
    description = ('Browse in-depth NiceGUI examples including authentication, chat apps, todo lists, and more. '
                   'See real Python GUI code with live demos.')
    ui.page_title(title)
    apply_page_seo(title=title, description=description, path='/examples',
                   breadcrumbs=[('Home', '/'), ('Examples', '/examples')])
    with ui.column().classes('w-full p-8 lg:p-16 max-w-[1600px] mx-auto'):
        section_heading('In-depth examples', 'Pick your *solution*')
        with ui.grid().classes('w-full grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4'):
            for example in examples:
                example_card(example)
