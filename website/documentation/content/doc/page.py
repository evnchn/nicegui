from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from nicegui.dataclasses import KWONLY_SLOTS

from .part import DocumentationPart

DifficultyLevel = Literal['beginner', 'intermediate', 'advanced']

_REPO_ROOT = Path(__file__).parents[4]
_GITHUB_BASE = 'https://github.com/zauberzeug/nicegui/blob/main'


def _auto_source_url(name: str) -> str | None:
    """Try to find the source file for a page with the given name."""
    for candidate in [f'nicegui/elements/{name}.py', f'nicegui/functions/{name}.py', f'nicegui/{name}.py']:
        if (_REPO_ROOT / candidate).exists():
            return f'{_GITHUB_BASE}/{candidate}'
    return None


@dataclass(**KWONLY_SLOTS)
class DocumentationPage:
    name: str
    title: str | None = None
    subtitle: str | None = None
    back_link: str | None = None
    parts: list[DocumentationPart] = field(default_factory=list)
    extra_column: Callable | None = None
    difficulty: DifficultyLevel | None = None  # NOTE: used for developer-experience metadata (Task 4)
    _source_url: str | None = None  # NOTE: explicit override via doc.metadata(source_url=...)
    _reference_source_url: str | None = None  # NOTE: derived from the element passed to doc.reference()

    @property
    def heading(self) -> str:
        """Return the heading of the page."""
        return self.title or self.parts[0].title or ''

    @property
    def source_url(self) -> str | None:
        """Return the source URL: explicit override > reference-derived > filename-probed."""
        return self._source_url or self._reference_source_url or _auto_source_url(self.name)
