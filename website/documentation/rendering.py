import functools

from nicegui import ui

from ..design import section_heading, subheading
from ..seo import DEFAULT_DESCRIPTION, TAGLINE, apply_page_seo, extract_description
from .content import DocumentationPage
from .content.overview import tiles
from .custom_restructured_text import CustomRestructuredText as custom_restructured_text
from .demo import demo
from .reference import generate_class_doc


@functools.cache
def _get_tile_descriptions() -> dict[str, str]:
    from .content import registry  # NOTE: deferred to avoid circular import
    result: dict[str, str] = {}
    for module, description in tiles:
        name = module.__name__.rsplit('.', 1)[-1]
        desc = extract_description(description)
        if name in registry and desc is not None:
            result[name] = desc
    return result


def _build_page_description(documentation: DocumentationPage) -> str:
    tile_desc = _get_tile_descriptions().get(documentation.name)
    if tile_desc:
        return tile_desc
    for part in documentation.parts:
        if part.description and not part.link:
            desc = extract_description(part.description)
            if desc is not None:
                return desc
        if part.search_text and not part.link:
            desc = extract_description(part.search_text)
            if desc is not None:
                return desc
    if documentation.subtitle:
        desc = extract_description(documentation.subtitle)
        if desc is not None:
            return desc
    for part in documentation.parts:
        if part.description:
            desc = extract_description(part.description)
            if desc is not None:
                return desc
    return DEFAULT_DESCRIPTION


def render_page(documentation: DocumentationPage) -> None:
    """Render the documentation."""
    title = (documentation.title or '').replace('*', '')
    if not title:
        seo_title = f'NiceGUI Documentation - {TAGLINE}'
    elif title.split()[0] == 'NiceGUI':
        seo_title = f'{title} - {TAGLINE}'
    else:
        seo_title = f'{title} - NiceGUI Documentation'
    ui.page_title('NiceGUI' if not title else title if title.split()[0] == 'NiceGUI' else f'{title} | NiceGUI')

    description = _build_page_description(documentation)
    path = f'/documentation/{documentation.name}' if documentation.name else '/documentation'

    breadcrumbs = [('Home', '/'), ('Documentation', '/documentation')]
    if documentation.name:
        if documentation.back_link is not None:
            from .content import registry
            parent = registry.get(documentation.back_link)
            if parent and parent.title:
                parent_title = parent.title.replace('*', '')
                breadcrumbs.append((parent_title, f'/documentation/{documentation.back_link}'))
        breadcrumbs.append((title, path))
    apply_page_seo(title=seo_title, description=description, path=path,
                   breadcrumbs=breadcrumbs, og_type='article')

    def render_content():
        first_demo_seen = False
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
                element.classes('w-full overflow-x-auto')
                if ':param' in part.description:
                    element.classes('rst-param-tables')
            if part.ui:
                part.ui()
            if part.demo:
                demo(part.demo.function, lazy=part.demo.lazy and first_demo_seen, tab=part.demo.tab)
                first_demo_seen = True
            if part.reference:
                generate_class_doc(part.reference, part.title)
            if part.link:
                ui.markdown(f'[See more \u2192](/documentation/{part.link})')
    with ui.column().classes('w-full p-8 lg:p-16 max-w-[1250px] mx-auto'):
        if documentation.extra_column:
            with ui.grid().classes('grid-cols-[2fr_1fr] max-[600px]:grid-cols-[1fr] gap-x-8 gap-y-16'):
                with ui.column().classes('w-full'):
                    render_content()
                with ui.column():
                    documentation.extra_column()
        else:
            render_content()
