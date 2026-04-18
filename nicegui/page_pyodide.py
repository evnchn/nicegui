"""Minimal page class for Pyodide — no FastAPI, no route registration."""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from . import core
from .language import Language


class page:
    """Lightweight page stub for Pyodide environments.

    Stores page configuration but does not register HTTP routes.
    Provides the same resolve_*() interface that Client and Outbox expect.
    """

    def __init__(self,
                 path: str = '/', *,
                 title: str | None = None,
                 viewport: str | None = None,
                 favicon: str | Path | None = None,
                 dark: bool | None = ...,  # type: ignore
                 language: Language = ...,  # type: ignore
                 response_timeout: float = 3.0,
                 reconnect_timeout: float | None = None,
                 **kwargs: Any,
                 ) -> None:
        self._path = path
        self.title = title
        self.viewport = viewport
        self.favicon = favicon
        self.dark = dark
        self.language = language
        self.response_timeout = response_timeout
        self.reconnect_timeout = reconnect_timeout
        self.kwargs = kwargs

    @property
    def path(self) -> str:
        """Return the page path."""
        return self._path

    def resolve_title(self) -> str:
        """Resolve the page title, falling back to the app config."""
        return self.title if self.title is not None else core.app.config.title

    def resolve_viewport(self) -> str:
        """Resolve the viewport meta value, falling back to the app config."""
        return self.viewport if self.viewport is not None else core.app.config.viewport

    def resolve_dark(self) -> bool | None:
        """Resolve the dark mode setting, falling back to the app config."""
        return self.dark if self.dark is not ... else core.app.config.dark

    def resolve_language(self) -> Language:
        """Resolve the page language, falling back to the app config."""
        return self.language if self.language is not ... else core.app.config.language

    def resolve_reconnect_timeout(self) -> float:
        """Resolve the reconnect timeout, falling back to the app config."""
        return self.reconnect_timeout if self.reconnect_timeout is not None else core.app.config.reconnect_timeout

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """No-op decorator in Pyodide — no routes to register."""
        return func
