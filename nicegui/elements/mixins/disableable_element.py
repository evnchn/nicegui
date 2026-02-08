from collections.abc import Callable
from typing import Any, cast

from typing_extensions import Self

from ...binding import BindableProperty, bind, bind_from, bind_to
from ...element import Element


class DisableableElement(Element):
    enabled = BindableProperty(
        on_change=lambda sender, value: cast(Self, sender)._handle_enabled_change(value))  # pylint: disable=protected-access

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.enabled = True
        self.ignores_events_when_disabled = True

    @property
    def is_ignoring_events(self) -> bool:
        """Return whether the element is currently ignoring events."""
        if super().is_ignoring_events:
            return True
        return not self.enabled and self.ignores_events_when_disabled

    def enable(self) -> None:
        """Enable the element."""
        self.enabled = True

    def disable(self) -> None:
        """Disable the element."""
        self.enabled = False

    def bind_enabled_to(self,
                        target_object: Any,
                        *target_name: str,
                        forward: Callable[[Any], Any] | None = None,
                        strict: bool | None = None,
                        ) -> Self:
        """Bind the enabled state of this element to the target object's target_name property.

        The binding works one way only, from this element to the target.
        The update happens immediately and whenever a value changes.

        :param target_object: The object to bind to.
        :param target_name: The name(s) of the property to bind to.
            For single keys: ``bind_enabled_to(data, 'enabled')``
            For nested keys: ``bind_enabled_to(storage, 'ui', 'enabled')``
        :param forward: A function to apply to the value before applying it to the target (default: identity).
        :param strict: Whether to check (and raise) if the target object has the specified property (default: None,
            performs a check if the object is not a dictionary, *added in version 3.0.0*).
        """
        # Handle backward compatibility: if last positional arg is callable, treat it as forward function
        if target_name and callable(target_name[-1]):
            *target_name, forward = target_name
        if not target_name:
            target_name = ('enabled',)
        name = target_name if len(target_name) > 1 else target_name[0]
        bind_to(self, 'enabled', target_object, name, forward, self_strict=False, other_strict=strict)
        return self

    def bind_enabled_from(self,
                          target_object: Any,
                          *target_name: str,
                          backward: Callable[[Any], Any] | None = None,
                          strict: bool | None = None,
                          ) -> Self:
        """Bind the enabled state of this element from the target object's target_name property.

        The binding works one way only, from the target to this element.
        The update happens immediately and whenever a value changes.

        :param target_object: The object to bind from.
        :param target_name: The name(s) of the property to bind from.
            For single keys: ``bind_enabled_from(data, 'enabled')``
            For nested keys: ``bind_enabled_from(storage, 'ui', 'enabled')``
        :param backward: A function to apply to the value before applying it to this element (default: identity).
        :param strict: Whether to check (and raise) if the target object has the specified property (default: None,
            performs a check if the object is not a dictionary, *added in version 3.0.0*).
        """
        # Handle backward compatibility: if last positional arg is callable, treat it as backward function
        if target_name and callable(target_name[-1]):
            *target_name, backward = target_name
        if not target_name:
            target_name = ('enabled',)
        name = target_name if len(target_name) > 1 else target_name[0]
        bind_from(self, 'enabled', target_object, name, backward, self_strict=False, other_strict=strict)
        return self

    def bind_enabled(self,
                     target_object: Any,
                     *target_name: str,
                     forward: Callable[[Any], Any] | None = None,
                     backward: Callable[[Any], Any] | None = None,
                     strict: bool | None = None,
                     ) -> Self:
        """Bind the enabled state of this element to the target object's target_name property.

        The binding works both ways, from this element to the target and from the target to this element.
        The update happens immediately and whenever a value changes.
        The backward binding takes precedence for the initial synchronization.

        :param target_object: The object to bind to.
        :param target_name: The name(s) of the property to bind to.
            For single keys: ``bind_enabled(data, 'enabled')``
            For nested keys: ``bind_enabled(storage, 'ui', 'enabled')``
        :param forward: A function to apply to the value before applying it to the target (default: identity).
        :param backward: A function to apply to the value before applying it to this element (default: identity).
        :param strict: Whether to check (and raise) if the target object has the specified property (default: None,
            performs a check if the object is not a dictionary, *added in version 3.0.0*).
        """
        if not target_name:
            target_name = ('enabled',)
        name = target_name if len(target_name) > 1 else target_name[0]
        bind(self, 'enabled', target_object, name,
             forward=forward, backward=backward,
             self_strict=False, other_strict=strict)
        return self

    def set_enabled(self, value: bool) -> None:
        """Set the enabled state of the element."""
        self.enabled = value

    def _handle_enabled_change(self, enabled: bool) -> None:
        """Called when the element is enabled or disabled.

        :param enabled: The new state.
        """
        self._props['disable'] = not enabled
