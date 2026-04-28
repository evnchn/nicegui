import re

from nicegui import ui
from nicegui.elements.restructured_text import prepare_content

_REST_LINK = re.compile(r'`([^`<\n]+?)\s*<([^>\s]+)>`_')
_REST_FIELD = re.compile(r'^:([^:\n]+):\s*(.*)$')


def _rest_to_markdown(text: str) -> str:
    """Convert a small subset of ReST syntax to markdown for the agent stream.

    Currently handles:
    - external links: ``Title <url>``_  ->  [Title](url)
    - field lists: ``:name: text``       ->  - **name**: text
    Everything else is passed through verbatim.
    """
    text = _REST_LINK.sub(r'[\1](\2)', text)
    out_lines = []
    for line in text.splitlines():
        match = _REST_FIELD.match(line)
        if match:
            out_lines.append(f'- **{match.group(1).strip()}**: {match.group(2)}')
        else:
            out_lines.append(line)
    return '\n'.join(out_lines)


class CustomRestructuredText(ui.restructured_text):
    """Custom restructured text element that avoids field lists being interpreted as document-level fields (see #4647)."""

    def _handle_content_change(self, content: str) -> None:
        html = prepare_content('__PLACEHOLDER__\n\n' + content).replace('<p>__PLACEHOLDER__</p>\n', '')
        if self._props.get('innerHTML') != html:
            self._props['innerHTML'] = html

    def _render_markdown(self) -> str:
        return _rest_to_markdown(self.content)
