from nicegui import ui

from ..style import section_heading, subheading
from .content import DocumentationPage
from .custom_restructured_text import CustomRestructuredText as custom_restructured_text
from .demo import demo
from .reference import generate_class_doc

WIDE = 'min-[2001px]'


def render_page(documentation: DocumentationPage) -> None:
    """Render the documentation."""
    title = (documentation.title or '').replace('*', '')
    ui.page_title('NiceGUI' if not title else title if title.split()[0] == 'NiceGUI' else f'{title} | NiceGUI')

    reference_parts = [(p.reference, p.title) for p in documentation.parts if p.reference]
    side_panels: list[ui.column] = []

    def render_content():
        section_heading(documentation.subtitle or '', documentation.heading)
        for part in documentation.parts:
            if part.title:
                if part.link_target:
                    ui.link_target(part.link_target)
                subheading(part.title,
                           link=f'/documentation/{part.link}' if part.link else None,
                           major=part.reference is not None)
            if part.description:
                if part.description_format == 'rst':
                    element = custom_restructured_text(part.description.replace(':param ', ':'))
                else:
                    element = ui.markdown(part.description)
                element.classes('bold-links arrow-links w-full overflow-x-auto')
                if ':param' in part.description:
                    element.classes('rst-param-tables')
            if part.ui:
                part.ui()
            if part.demo:
                demo(part.demo.function, lazy=part.demo.lazy, tab=part.demo.tab)
            if part.reference:
                if reference_parts:
                    panel = ui.column().classes('w-full')
                    side_panels.append(panel)
                    generate_class_doc(part.reference, part.title, side_panel=panel)
                else:
                    generate_class_doc(part.reference, part.title)
            if part.link:
                ui.markdown(f'See [more...](/documentation/{part.link})').classes('bold-links arrow-links')

    row = ui.row().classes(f'w-full justify-center items-start {WIDE}:!gap-0')
    if reference_parts:
        row.classes(f'{WIDE}:h-[calc(100vh-70px)] {WIDE}:overflow-hidden')
    with row:
        main_col = ui.column().classes(f'w-full p-8 lg:p-16 max-w-[1250px] mx-auto {WIDE}:!mx-0')
        if reference_parts:
            main_col.classes(f'{WIDE}:h-full {WIDE}:!p-0 {WIDE}:!gap-0')
        with main_col:
            if reference_parts:
                scroll = ui.element('div').classes(
                    f'w-full {WIDE}:overflow-y-auto {WIDE}:h-full {WIDE}:p-8 lg:{WIDE}:p-16'
                )
            else:
                scroll = ui.element('div').classes('w-full')
            with scroll:
                with ui.column().classes('w-full'):
                    if documentation.extra_column:
                        with ui.grid().classes('grid-cols-[2fr_1fr] max-[600px]:grid-cols-[1fr] gap-x-8 gap-y-16'):
                            with ui.column().classes('w-full'):
                                render_content()
                            with ui.column():
                                documentation.extra_column()
                    else:
                        render_content()
                    with ui.column().classes('w-full p-4 items-end'):
                        ui.link('Imprint & Privacy', '/imprint_privacy').classes('text-sm')
        if reference_parts:
            side = ui.element('div').classes(
                f'!hidden {WIDE}:!block max-w-[500px] shrink-0'
                f' {WIDE}:overflow-y-auto {WIDE}:h-full'
            )
            with side:
                ui.column().classes('w-full p-8 lg:p-16').props(f'id="side-panel-{side.id}"')
            _setup_side_panel_js(side_panels, side)


def _setup_side_panel_js(panels: list[ui.column], side: ui.element) -> None:
    """Set up JavaScript to move side panel content between main and side column based on viewport width."""
    if not panels:
        return
    ids = [f'c{panel.id}' for panel in panels]
    side_inner_id = f'side-panel-{side.id}'
    ui.run_javascript(f'''
        (function setup() {{
            const ids = {ids};
            const sideInner = document.getElementById("{side_inner_id}");
            const elements = ids.map(id => document.getElementById(id));
            if (!sideInner || elements.some(el => !el)) {{
                requestAnimationFrame(setup);
                return;
            }}
            const mql = window.matchMedia("(min-width: 2001px)");
            const placeholders = elements.map(el => {{
                const ph = document.createComment("side-ph");
                el.parentNode.insertBefore(ph, el);
                return {{ el, ph }};
            }});
            function update(e) {{
                placeholders.forEach(({{ el, ph }}) => {{
                    if (e.matches) {{
                        sideInner.appendChild(el);
                    }} else {{
                        ph.parentNode.insertBefore(el, ph);
                    }}
                }});
            }}
            mql.addEventListener("change", update);
            update(mql);
        }})();
    ''')
