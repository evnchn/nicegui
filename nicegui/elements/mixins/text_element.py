from collections.abc import Callable
from typing import Any, cast

from typing_extensions import Self

from ...binding import BindableProperty, bind, bind_from, bind_to
from ...element import Element


class TextElement(Element):
    text = BindableProperty(
        on_change=lambda sender, text: cast(Self, sender)._handle_text_change(text))  # pylint: disable=protected-access

    def __init__(self, *, text: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.text = text
        self._text_to_model_text(text)

    def bind_text_to(self,
                     target_object: Any,
                     *target_name: str,
                     forward: Callable[[Any], Any] | None = None,
                     strict: bool | None = None,
                     ) -> Self:
        """Bind the text of this element to the target object's target_name property.

        The binding works one way only, from this element to the target.
        The update happens immediately and whenever a value changes.

        :param target_object: The object to bind to.
        :param target_name: The name(s) of the property to bind to.
            For single keys: ``bind_text_to(data, 'message')``
            For nested keys: ``bind_text_to(storage, 'config', 'message')``
        :param forward: A function to apply to the value before applying it to the target (default: identity).
        :param strict: Whether to check (and raise) if the target object has the specified property (default: None,
            performs a check if the object is not a dictionary, *added in version 3.0.0*).
        """
        # Handle backward compatibility: if last positional arg is callable, treat it as forward function
        if target_name and callable(target_name[-1]):
            target_name, forward = target_name[:-1], target_name[-1]

        if not target_name:
            target_name = ('text',)
        name = target_name if len(target_name) > 1 else target_name[0]
        bind_to(self, 'text', target_object, name, forward, self_strict=False, other_strict=strict)
        return self

    def bind_text_from(self,
                       target_object: Any,
                       *target_name: str,
                       backward: Callable[[Any], Any] | None = None,
                       strict: bool | None = None,
                       ) -> Self:
        """Bind the text of this element from the target object's target_name property.

        The binding works one way only, from the target to this element.
        The update happens immediately and whenever a value changes.

        :param target_object: The object to bind from.
        :param target_name: The name(s) of the property to bind from.
            For single keys: ``bind_text_from(data, 'message')``
            For nested keys: ``bind_text_from(storage, 'config', 'message')``
        :param backward: A function to apply to the value before applying it to this element (default: identity).
        :param strict: Whether to check (and raise) if the target object has the specified property (default: None,
            performs a check if the object is not a dictionary, *added in version 3.0.0*).
        """
        # Handle backward compatibility: if last positional arg is callable, treat it as backward function
        if target_name and callable(target_name[-1]):
            target_name, backward = target_name[:-1], target_name[-1]

        if not target_name:
            target_name = ('text',)
        name = target_name if len(target_name) > 1 else target_name[0]
        bind_from(self, 'text', target_object, name, backward, self_strict=False, other_strict=strict)
        return self

    def bind_text(self,
                  target_object: Any,
                  *target_name: str,
                  forward: Callable[[Any], Any] | None = None,
                  backward: Callable[[Any], Any] | None = None,
                  strict: bool | None = None,
                  ) -> Self:
        """Bind the text of this element to the target object's target_name property.

        The binding works both ways, from this element to the target and from the target to this element.
        The update happens immediately and whenever a value changes.
        The backward binding takes precedence for the initial synchronization.

        :param target_object: The object to bind to.
        :param target_name: The name(s) of the property to bind to.
            For single keys: ``bind_text(data, 'message')``
            For nested keys: ``bind_text(storage, 'config', 'message')``
        :param forward: A function to apply to the value before applying it to the target (default: identity).
        :param backward: A function to apply to the value before applying it to this element (default: identity).
        :param strict: Whether to check (and raise) if the target object has the specified property (default: None,
            performs a check if the object is not a dictionary, *added in version 3.0.0*).
        """
        # Note: bind() requires keyword arguments for forward/backward, no positional compatibility needed
        if not target_name:
            target_name = ('text',)
        name = target_name if len(target_name) > 1 else target_name[0]
        bind(self, 'text', target_object, name,
             forward=forward, backward=backward,
             self_strict=False, other_strict=strict)
        return self

    def set_text(self, text: str) -> None:
        """Set the text of this element.

        :param text: The new text.
        """
        self.text = text

    def _handle_text_change(self, text: str) -> None:
        """Called when the text of this element changes.

        :param text: The new text.
        """
        self._text_to_model_text(text)
        self.update()

    def _text_to_model_text(self, text: str) -> None:
        self._text = text
