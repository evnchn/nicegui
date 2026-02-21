from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal

from nicegui.dataclasses import KWONLY_SLOTS

from .part import DocumentationPart

DifficultyLevel = Literal['beginner', 'intermediate', 'advanced']


@dataclass(**KWONLY_SLOTS)
class DocumentationPage:
    name: str
    title: str | None = None
    subtitle: str | None = None
    back_link: str | None = None
    parts: list[DocumentationPart] = field(default_factory=list)
    extra_column: Callable | None = None
    difficulty: DifficultyLevel | None = None  # NOTE: used for developer-experience metadata (Task 4)
    source_url: str | None = None  # NOTE: direct GitHub source link for this page's primary element (Task 3)

    @property
    def heading(self) -> str:
        """Return the heading of the page."""
        return self.title or self.parts[0].title or ''
