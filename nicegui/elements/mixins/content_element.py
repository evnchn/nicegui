from collections.abc import Callable
from typing import Any, cast

from typing_extensions import Self

from ...binding import BindableProperty, bind, bind_from, bind_to
from ...element import Element


class ContentElement(Element):
    CONTENT_PROP = 'innerHTML'
    content = BindableProperty(
        on_change=lambda sender, content: cast(Self, sender)._handle_content_change(content))  # pylint: disable=protected-access

    def __init__(self, *, content: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.content = content
        self._handle_content_change(content)

    def bind_content_to(self,
                        target_object: Any,
                        *target_name: str,
                        forward: Callable[[Any], Any] | None = None,
                        strict: bool | None = None,
                        ) -> Self:
        """Bind the content of this element to the target object's target_name property.

        The binding works one way only, from this element to the target.
        The update happens immediately and whenever a value changes.

        :param target_object: The object to bind to.
        :param target_name: The name(s) of the property to bind to.
            For single keys: ``bind_content_to(data, 'content')``
            For nested keys: ``bind_content_to(storage, 'ui', 'content')``
        :param forward: A function to apply to the value before applying it to the target (default: identity).
        :param strict: Whether to check (and raise) if the target object has the specified property (default: None,
            performs a check if the object is not a dictionary, *added in version 3.0.0*).
        """
        # Handle backward compatibility: if last positional arg is callable, treat it as forward function
        if target_name and callable(target_name[-1]):
            target_name, forward = target_name[:-1], target_name[-1]
        if not target_name:
            target_name = ('content',)
        name = target_name if len(target_name) > 1 else target_name[0]
        bind_to(self, 'content', target_object, name, forward, self_strict=False, other_strict=strict)
        return self

    def bind_content_from(self,
                          target_object: Any,
                          *target_name: str,
                          backward: Callable[[Any], Any] | None = None,
                          strict: bool | None = None,
                          ) -> Self:
        """Bind the content of this element from the target object's target_name property.

        The binding works one way only, from the target to this element.
        The update happens immediately and whenever a value changes.

        :param target_object: The object to bind from.
        :param target_name: The name(s) of the property to bind from.
            For single keys: ``bind_content_from(data, 'content')``
            For nested keys: ``bind_content_from(storage, 'ui', 'content')``
        :param backward: A function to apply to the value before applying it to this element (default: identity).
        :param strict: Whether to check (and raise) if the target object has the specified property (default: None,
            performs a check if the object is not a dictionary, *added in version 3.0.0*).
        """
        # Handle backward compatibility: if last positional arg is callable, treat it as backward function
        if target_name and callable(target_name[-1]):
            target_name, backward = target_name[:-1], target_name[-1]
        if not target_name:
            target_name = ('content',)
        name = target_name if len(target_name) > 1 else target_name[0]
        bind_from(self, 'content', target_object, name, backward, self_strict=False, other_strict=strict)
        return self

    def bind_content(self,
                     target_object: Any,
                     *target_name: str,
                     forward: Callable[[Any], Any] | None = None,
                     backward: Callable[[Any], Any] | None = None,
                     strict: bool | None = None,
                     ) -> Self:
        """Bind the content of this element to the target object's target_name property.

        The binding works both ways, from this element to the target and from the target to this element.
        The update happens immediately and whenever a value changes.
        The backward binding takes precedence for the initial synchronization.

        :param target_object: The object to bind to.
        :param target_name: The name(s) of the property to bind to.
            For single keys: ``bind_content(data, 'content')``
            For nested keys: ``bind_content(storage, 'ui', 'content')``
        :param forward: A function to apply to the value before applying it to the target (default: identity).
        :param backward: A function to apply to the value before applying it to this element (default: identity).
        :param strict: Whether to check (and raise) if the target object has the specified property (default: None,
            performs a check if the object is not a dictionary, *added in version 3.0.0*).
        """
        if not target_name:
            target_name = ('content',)
        name = target_name if len(target_name) > 1 else target_name[0]
        bind(self, 'content', target_object, name,
             forward=forward, backward=backward,
             self_strict=False, other_strict=strict)
        return self

    def set_content(self, content: str) -> None:
        """Set the content of this element.

        :param content: The new content.
        """
        self.content = content

    def _handle_content_change(self, content: str) -> None:
        """Called when the content of this element changes.

        :param content: The new content.
        """
        if self.CONTENT_PROP == 'innerHTML' and '</script>' in content:
            raise ValueError('HTML elements must not contain <script> tags. Use ui.add_body_html() instead.')
        self._props[self.CONTENT_PROP] = content
