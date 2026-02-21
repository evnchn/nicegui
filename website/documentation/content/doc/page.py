from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from nicegui.dataclasses import KWONLY_SLOTS

from .part import DocumentationPart

DifficultyLevel = Literal['beginner', 'intermediate', 'advanced']

_REPO_ROOT = Path(__file__).parents[4]
_GITHUB_BASE = 'https://github.com/zauberzeug/nicegui/blob/main'


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

    @property
    def heading(self) -> str:
        """Return the heading of the page."""
        return self.title or self.parts[0].title or ''

    @property
    def source(self) -> Path | None:
        """Return the local source path: explicit > auto-derived from element > filename-probed."""
        if self._source:
            return self._source
        for candidate in [f'nicegui/elements/{self.name}.py', f'nicegui/functions/{self.name}.py', f'nicegui/{self.name}.py']:
            if (_REPO_ROOT / candidate).exists():
                return Path(candidate)
        return None

    @property
    def source_url(self) -> str | None:
        """Return the GitHub source URL derived from the local source path."""
        return f'{_GITHUB_BASE}/{self.source.as_posix()}' if self.source else None
