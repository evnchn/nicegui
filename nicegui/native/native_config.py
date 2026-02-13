from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ..events import Handler, NativeEventArguments

try:
    from .event_manager import event_manager
except ImportError:
    event_manager = None  # type: ignore

if TYPE_CHECKING:
    from .native import WindowProxy


@dataclass(kw_only=True, slots=True)
class NativeConfig:
    start_args: dict[str, Any] = field(default_factory=dict)
    window_args: dict[str, Any] = field(default_factory=dict)
    settings: dict[str, Any] = field(default_factory=dict)
    main_window: WindowProxy | None = None

    def on(self, event_type: str, handler: Handler[NativeEventArguments]) -> None:
        """Register a handler for a native window event.

        Supported events: shown, loaded, minimized, maximized, restored, resized, moved, closed, drop.

        :param event_type: the event name
        :param handler: callback, may accept a NativeEventArguments parameter or no parameters
        """
        event_manager.on(event_type, handler)
