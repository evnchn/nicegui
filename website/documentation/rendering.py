import math
import re

from nicegui import ui

from ..style import section_heading, subheading
from .content import DocumentationPage
from .custom_restructured_text import CustomRestructuredText as custom_restructured_text
from .demo import demo
from .reference import generate_class_doc

_GITHUB_REPO = 'https://github.com/zauberzeug/nicegui'

# NOTE: average reading speed in words per minute for technical content
_WORDS_PER_MINUTE = 200

_DIFFICULTY_LABELS = {
    'beginner': ('Beginner', 'text-green-700 bg-green-100 dark:text-green-300 dark:bg-green-900'),
    'intermediate': ('Intermediate', 'text-yellow-700 bg-yellow-100 dark:text-yellow-300 dark:bg-yellow-900'),
    'advanced': ('Advanced', 'text-red-700 bg-red-100 dark:text-red-300 dark:bg-red-900'),
}


def _estimate_reading_time(documentation: DocumentationPage) -> int:
    """Estimate reading time in minutes based on all text content in the page."""
    text_parts = [
        documentation.title or '',
        documentation.subtitle or '',
    ]
    for part in documentation.parts:
        if part.description:
            text_parts.append(part.description)
        if part.title:
            text_parts.append(part.title)
        if part.search_text:
            text_parts.append(part.search_text)
    combined = ' '.join(text_parts)
    word_count = len(re.findall(r'\w+', combined))
    return max(1, math.ceil(word_count / _WORDS_PER_MINUTE))


def _render_page_metadata(documentation: DocumentationPage) -> None:
    """Render reading time, difficulty badge, and source link for a documentation page."""
    reading_time = _estimate_reading_time(documentation)
    has_metadata = documentation.difficulty is not None or documentation.source_url is not None
    if not has_metadata and reading_time < 2:
        return
    with ui.row().classes('items-center gap-3 mb-2 flex-wrap'):
        ui.label(f'{reading_time} min read').classes(
            'text-sm text-gray-500 dark:text-gray-400 flex items-center gap-1'
        )
        if documentation.difficulty:
            label_text, label_classes = _DIFFICULTY_LABELS.get(
                documentation.difficulty,
                (documentation.difficulty.capitalize(), 'text-gray-600 bg-gray-100'),
            )
            ui.label(label_text).classes(
                f'text-xs font-semibold px-2 py-0.5 rounded-full {label_classes}'
            )
        if documentation.source_url:
            ui.link('View source', documentation.source_url) \
                .classes('text-sm text-primary opacity-70 hover:opacity-100') \
                .props('target=_blank')


def _render_suggest_edit_button(documentation: DocumentationPage) -> None:
    """Render a 'Suggest an Edit' button that links to a pre-filled GitHub issue."""
    page_url = f'https://nicegui.io/documentation/{documentation.name}'
    issue_title = f'Docs improvement: {(documentation.title or documentation.name).replace("*", "")}'
    issue_body = (
        f'**Page:** [{page_url}]({page_url})\n\n'
        '**Suggestion:**\n\n'
        '<!-- Please describe your suggested improvement here -->'
    )
    import urllib.parse
    params = urllib.parse.urlencode({'title': issue_title, 'body': issue_body, 'labels': 'documentation'})
    issue_url = f'{_GITHUB_REPO}/issues/new?{params}'
    with ui.row().classes('items-center gap-1 mt-2'):
        ui.icon('edit', size='xs').classes('text-gray-400')
        ui.link('Suggest an Edit', issue_url) \
            .classes('text-xs text-gray-400 hover:text-primary') \
            .props('target=_blank')


def render_page(documentation: DocumentationPage) -> None:
    """Render the documentation."""
    title = (documentation.title or '').replace('*', '')
    ui.page_title('NiceGUI' if not title else title if title.split()[0] == 'NiceGUI' else f'{title} | NiceGUI')

    def render_content():
        first_demo_seen = False
        section_heading(documentation.subtitle or '', documentation.heading)
        _render_page_metadata(documentation)
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
                demo(part.demo.function, lazy=part.demo.lazy and first_demo_seen, tab=part.demo.tab)
                first_demo_seen = True
            if part.reference:
                generate_class_doc(part.reference, part.title)
            if part.link:
                ui.markdown(f'See [more...](/documentation/{part.link})').classes('bold-links arrow-links')
    with ui.column().classes('w-full p-8 lg:p-16 max-w-[1250px] mx-auto'):
        if documentation.extra_column:
            with ui.grid().classes('grid-cols-[2fr_1fr] max-[600px]:grid-cols-[1fr] gap-x-8 gap-y-16'):
                with ui.column().classes('w-full'):
                    render_content()
                with ui.column():
                    documentation.extra_column()
        else:
            render_content()
    with ui.column().classes('w-full p-4 items-end gap-1'):
        if documentation.name:
            _render_suggest_edit_button(documentation)
        ui.link('Imprint & Privacy', '/imprint_privacy').classes('text-sm')
