from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from nicegui.dataclasses import KWONLY_SLOTS

from .part import DocumentationPart

DifficultyLevel = Literal['beginner', 'intermediate', 'advanced']

_REPO_ROOT = Path(__file__).parents[4]
_GITHUB_BASE = 'https://github.com/zauberzeug/nicegui/blob/main'


def _auto_source(name: str) -> Path | None:
    """Try to find the source file for a page with the given name."""
    for candidate in [f'nicegui/elements/{name}.py', f'nicegui/functions/{name}.py', f'nicegui/{name}.py']:
        if (_REPO_ROOT / candidate).exists():
            return Path(candidate)
    return None


@dataclass(**KWONLY_SLOTS)
class DocumentationPage:
    name: str
    title: str | None = None
    subtitle: str | None = None
    back_link: str | None = None
    parts: list[DocumentationPart] = field(default_factory=list)
    extra_column: Callable | None = None
    difficulty: DifficultyLevel | None = None
    _source: Path | None = None
    _reference_source: Path | None = None

    @property
    def heading(self) -> str:
        """Return the heading of the page."""
        return self.title or self.parts[0].title or ''

    @property
    def source(self) -> Path | None:
        """Return the local source path: explicit override > reference-derived > filename-probed."""
        return self._source or self._reference_source or _auto_source(self.name)

    @property
    def source_url(self) -> str | None:
        """Return the GitHub source URL derived from the local source path."""
        return f'{_GITHUB_BASE}/{self.source.as_posix()}' if self.source else None
