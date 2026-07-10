from __future__ import annotations

import asyncio
import copyreg
import dataclasses
import itertools
import time
import weakref
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, MutableMapping
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any, Literal, TypeVar

from typing_extensions import dataclass_transform

from . import core
from .logging import log

if TYPE_CHECKING:
    from _typeshed import DataclassInstance, IdentityFunction

MAX_PROPAGATION_TIME = 0.01

propagation_visited: ContextVar[set[tuple[int, tuple[str, ...]]] | None] = \
    ContextVar('propagation_visited', default=None)

BindingKey = tuple[int, tuple[str, ...]]

# Each key maps to a dict of {entry id -> (source, target, target_name, transform)} so that a single
# entry can be removed in O(1) by id, even when many bindings share one source (and thus one key).
bindings: defaultdict[
    BindingKey,
    dict[int, tuple[Any, Any, tuple[str, ...], Callable[[Any], Any] | None]]
] = defaultdict(dict)
_binding_entry_ids = itertools.count()
# Reverse index: object id -> set of (key, entry id) the object participates in (as source or target).
# Lets ``remove`` touch only the bindings of the given objects instead of scanning all of them.
_bindings_by_obj: defaultdict[int, set[tuple[BindingKey, int]]] = defaultdict(set)
bindable_properties: weakref.WeakValueDictionary[BindingKey, Any] = weakref.WeakValueDictionary()
active_links: dict[int, tuple[Any, tuple[str, ...], Any, tuple[str, ...], Callable[[Any], Any] | None]] = {}
_active_link_ids = itertools.count()
# Reverse index: object id -> set of active-link ids the object participates in (as source or target).
_active_links_by_obj: defaultdict[int, set[int]] = defaultdict(set)
_active_links_added = asyncio.Event()

TC = TypeVar('TC', bound=type)
T = TypeVar('T')

_MISSING = object()


def _get_attribute(obj: object | Mapping, name: tuple[str, ...]) -> Any:
    try:
        for key in name:
            obj = obj[key] if isinstance(obj, Mapping) else getattr(obj, key)
    except (KeyError, AttributeError):
        return _MISSING
    return obj


def _set_attribute(obj: object | Mapping, name: tuple[str, ...], value: Any) -> None:
    for key in name[:-1]:
        if isinstance(obj, MutableMapping):
            obj = obj.setdefault(key, {})
        else:
            type_ = obj.__class__.__name__
            obj = getattr(obj, key, _MISSING)
            if obj is _MISSING:
                raise AttributeError(f'Cannot traverse intermediate attribute "{key}" on object of type {type_}. '
                                     'Only dict intermediates are auto-created for missing keys.')
    if isinstance(obj, MutableMapping):
        obj[name[-1]] = value
    else:
        setattr(obj, name[-1], value)


async def refresh_loop() -> None:
    """Refresh all bindings in an endless loop."""
    global _active_links_added  # pylint: disable=global-statement # noqa: PLW0603
    _active_links_added = asyncio.Event()
    await _active_links_added.wait()
    if core.app.config.binding_refresh_interval is None:
        core.app.config.binding_refresh_interval = 0.1
        log.warning('Starting active binding loop even though it was disabled via binding_refresh_interval=None.')
    while True:
        _refresh_step()
        try:
            await asyncio.sleep(core.app.config.binding_refresh_interval)
        except asyncio.CancelledError:
            break


def _refresh_step() -> None:
    t = time.time()
    for link_id, link in list(active_links.items()):  # snapshot: a transform may call remove() and mutate active_links
        if link_id not in active_links:  # this link was removed reentrantly (e.g. remove() from a transform)
            continue
        (source_obj, source_name, target_obj, target_name, transform) = link
        if (source_value := _get_attribute(source_obj, source_name)) is not _MISSING:
            value = transform(source_value) if transform else source_value
            if (target_value := _get_attribute(target_obj, target_name)) is _MISSING or target_value != value:
                _set_attribute(target_obj, target_name, value)
                _propagate(target_obj, target_name)
        del link, source_obj, target_obj  # pylint: disable=modified-iterating-list
    if time.time() - t > MAX_PROPAGATION_TIME:
        log.warning(f'binding propagation for {len(active_links)} active links took {time.time() - t:.3f} s')


def _propagate(source_obj: Any, source_name: tuple[str, ...]) -> None:
    token = propagation_visited.set(set())
    try:
        _propagate_recursively(source_obj, source_name)
    finally:
        propagation_visited.reset(token)


def _propagate_recursively(source_obj: Any, source_name: tuple[str, ...]) -> None:
    visited = propagation_visited.get()
    assert visited is not None, 'propagation_visited is not set'

    source_obj_id = id(source_obj)
    if (source_obj_id, source_name) in visited:
        return
    visited.add((source_obj_id, source_name))

    if (source_value := _get_attribute(source_obj, source_name)) is _MISSING:
        return

    # snapshot: a transform may call remove() and mutate this binding dict during iteration
    entries = bindings.get((source_obj_id, source_name), {})
    for entry_id, entry in list(entries.items()):
        if entry_id not in entries:  # this binding was removed reentrantly (e.g. remove() from a transform)
            continue
        _, target_obj, target_name, transform = entry
        if (id(target_obj), target_name) in visited:
            continue

        target_value = transform(source_value) if transform else source_value
        if (current := _get_attribute(target_obj, target_name)) is _MISSING or current != target_value:
            _set_attribute(target_obj, target_name, target_value)
            _propagate_recursively(target_obj, target_name)


def _check_attribute_exists(obj: Any, name: tuple[str, ...], *, role: Literal['self', 'other']) -> None:
    if _get_attribute(obj, name) is not _MISSING:
        return
    for key in name:
        try:
            obj = obj[key] if isinstance(obj, Mapping) else getattr(obj, key)
        except (KeyError, AttributeError):
            break
    if isinstance(obj, Mapping):
        raise KeyError(
            f'Could not bind non-existing key "{".".join(name)}". '
            f'To allow missing keys (lazy binding), remove {role}_strict=True or add the key before binding.'
        )
    else:
        raise AttributeError(
            f'Could not bind non-existing attribute "{".".join(name)}" on object of type {obj.__class__.__name__}. '
            f'To allow missing attributes (lazy binding), add {role}_strict=False or add the attribute before binding.'
        )


def _check_self_and_other_attribute(self_obj: Any, self_name: tuple[str, ...], other_obj: Any,
                                    other_name: tuple[str, ...],
                                    self_strict: bool | None, other_strict: bool | None) -> None:
    if self_strict or (self_strict is None and not _path_contains_dict(self_obj, self_name)):
        _check_attribute_exists(self_obj, self_name, role='self')
    if other_strict or (other_strict is None and not _path_contains_dict(other_obj, other_name)):
        _check_attribute_exists(other_obj, other_name, role='other')


def _register_binding(source_obj: Any, source_name: tuple[str, ...], target_obj: Any, target_name: tuple[str, ...],
                      transform: Callable[[Any], Any] | None) -> None:
    """Register a one-way binding ``source_obj.source_name`` -> ``target_obj.target_name`` and index it."""
    key = (id(source_obj), source_name)
    entry_id = next(_binding_entry_ids)
    bindings[key][entry_id] = (source_obj, target_obj, target_name, transform)
    _bindings_by_obj[id(source_obj)].add((key, entry_id))
    _bindings_by_obj[id(target_obj)].add((key, entry_id))
    if key not in bindable_properties:
        link_id = next(_active_link_ids)
        active_links[link_id] = (source_obj, source_name, target_obj, target_name, transform)
        _active_links_by_obj[id(source_obj)].add(link_id)
        _active_links_by_obj[id(target_obj)].add(link_id)
        _active_links_added.set()


def bind_to(self_obj: Any, self_name: str | tuple[str, ...], other_obj: Any, other_name: str | tuple[str, ...],
            forward: Callable[[Any], Any] | None = None, *,
            self_strict: bool | None = None, other_strict: bool | None = None) -> None:
    """Bind the property of one object to the property of another object.

    The binding works one way only, from the first object to the second.
    The update happens immediately and whenever a value changes.
    The name parameters also accept a tuple of strings for nested keys (*since version 3.10.0*).

    :param self_obj: The object to bind from.
    :param self_name: The name of the property to bind from.
    :param other_obj: The object to bind to.
    :param other_name: The name of the property to bind to.
    :param forward: A function to apply to the value before applying it (default: identity).
    :param self_strict: Whether to check (and raise) if the first object has the specified property
        (default: None, performs a check if the object is not a dictionary, *added in version 3.0.0*).
    :param other_strict: Whether to check (and raise) if the second object has the specified property
        (default: None, performs a check if the object is not a dictionary, *added in version 3.0.0*).
    """
    self_name_tuple = _normalize_name(self_name)
    other_name_tuple = _normalize_name(other_name)
    _check_self_and_other_attribute(self_obj, self_name_tuple, other_obj, other_name_tuple, self_strict, other_strict)
    _register_binding(self_obj, self_name_tuple, other_obj, other_name_tuple, forward)
    _propagate(self_obj, self_name_tuple)


def bind_from(self_obj: Any, self_name: str | tuple[str, ...], other_obj: Any, other_name: str | tuple[str, ...],
              backward: Callable[[Any], Any] | None = None, *,
              self_strict: bool | None = None, other_strict: bool | None = None) -> None:
    """Bind the property of one object from the property of another object.

    The binding works one way only, from the second object to the first.
    The update happens immediately and whenever a value changes.
    The name parameters also accept a tuple of strings for nested keys (*since version 3.10.0*).

    :param self_obj: The object to bind to.
    :param self_name: The name of the property to bind to.
    :param other_obj: The object to bind from.
    :param other_name: The name of the property to bind from.
    :param backward: A function to apply to the value before applying it (default: identity).
    :param self_strict: Whether to check (and raise) if the first object has the specified property (default: None,
        performs a check if the object is not a dictionary, *added in version 3.0.0*).
    :param other_strict: Whether to check (and raise) if the second object has the specified property (default: None,
        performs a check if the object is not a dictionary, *added in version 3.0.0*).
    """
    self_name_tuple = _normalize_name(self_name)
    other_name_tuple = _normalize_name(other_name)
    _check_self_and_other_attribute(self_obj, self_name_tuple, other_obj, other_name_tuple, self_strict, other_strict)
    _register_binding(other_obj, other_name_tuple, self_obj, self_name_tuple, backward)
    _propagate(other_obj, other_name_tuple)


def bind(self_obj: Any, self_name: str | tuple[str, ...], other_obj: Any, other_name: str | tuple[str, ...], *,
         forward: Callable[[Any], Any] | None = None,
         backward: Callable[[Any], Any] | None = None,
         self_strict: bool | None = None,
         other_strict: bool | None = None) -> None:
    """Bind the property of one object to the property of another object.

    The binding works both ways, from the first object to the second and from the second to the first.
    The update happens immediately and whenever a value changes.
    The backward binding takes precedence for the initial synchronization.
    The name parameters also accept a tuple of strings for nested keys (*since version 3.10.0*).

    :param self_obj: First object to bind.
    :param self_name: The name of the first property to bind.
    :param other_obj: The second object to bind.
    :param other_name: The name of the second property to bind.
    :param forward: A function to apply to the value before applying it to the second object (default: identity).
    :param backward: A function to apply to the value before applying it to the first object (default: identity).
    :param self_strict: Whether to check (and raise) if the first object has the specified property (default: None,
        performs a check if the object is not a dictionary, *added in version 3.0.0*).
    :param other_strict: Whether to check (and raise) if the second object has the specified property (default: None,
        performs a check if the object is not a dictionary, *added in version 3.0.0*).
    """
    self_name_tuple = _normalize_name(self_name)
    other_name_tuple = _normalize_name(other_name)
    _check_self_and_other_attribute(self_obj, self_name_tuple, other_obj, other_name_tuple, self_strict, other_strict)
    bind_from(self_obj, self_name_tuple, other_obj, other_name_tuple,
              backward=backward, self_strict=False, other_strict=False)
    bind_to(self_obj, self_name_tuple, other_obj, other_name_tuple,
            forward=forward, self_strict=False, other_strict=False)


def _normalize_name(name: str | tuple[str, ...]) -> tuple[str, ...]:
    """Convert property name to normalized tuple format."""
    assert name, 'Property name cannot be empty'
    if isinstance(name, tuple):
        assert all(isinstance(key, str) for key in name), 'Property name tuple must contain only strings'
    return name if isinstance(name, tuple) else (name,)


def _path_contains_dict(obj: Any, name: tuple[str, ...]) -> bool:
    """Check if the nested path traverses through any dict/Mapping."""
    for key in name:
        if isinstance(obj, Mapping):
            return True
        if not hasattr(obj, key):
            return False
        obj = getattr(obj, key)
    return False


class BindableProperty:

    def __init__(self, on_change: Callable[..., Any] | None = None) -> None:
        self._change_handler = on_change

    def __set_name__(self, _, name: str) -> None:
        self.name = name  # pylint: disable=attribute-defined-outside-init
        _bindable_property_names_cache.clear()  # a class gained a bindable property; drop the memoized names

    def __get__(self, owner: Any, _=None) -> Any:
        return getattr(owner, '___' + self.name)

    def __set__(self, owner: Any, value: Any) -> None:
        has_attr = hasattr(owner, '___' + self.name)
        if not has_attr:
            _make_copyable(type(owner))
        value_changed = has_attr and getattr(owner, '___' + self.name) != value
        if has_attr and not value_changed:
            return
        setattr(owner, '___' + self.name, value)
        bindable_properties[(id(owner), (self.name,))] = owner
        _propagate(owner, (self.name,))
        if value_changed and self._change_handler is not None:
            self._change_handler(owner, value)


_bindable_property_names_cache: dict[type, tuple[tuple[str, ...], ...]] = {}


def _bindable_property_names(cls: type) -> tuple[tuple[str, ...], ...]:
    """Return the ``bindable_properties`` key-names a class can register (cached per class).

    Entries in ``bindable_properties`` are only ever created by ``BindableProperty.__set__``,
    always keyed by a single-element name tuple whose descriptor lives on the owner's class.
    The cache is invalidated by ``BindableProperty.__set_name__`` whenever a class gains one.
    """
    if cls not in _bindable_property_names_cache:
        _bindable_property_names_cache[cls] = tuple({
            (attr,)
            for base in cls.__mro__
            for attr, value in vars(base).items()
            if isinstance(value, BindableProperty)
        })
    return _bindable_property_names_cache[cls]


def _discard_from_index(index: defaultdict[int, set], obj_id: int, value: Any) -> None:
    """Discard ``value`` from ``index[obj_id]``, dropping the entry entirely once empty."""
    entries = index.get(obj_id)
    if entries is not None:
        entries.discard(value)
        if not entries:
            del index[obj_id]


def remove(objects: Iterable[Any]) -> None:
    """Remove all bindings that involve the given objects.

    :param objects: The objects to remove.
    """
    objects = list(objects)  # may be a one-shot iterable, and we iterate it more than once
    object_ids = set(map(id, objects))

    link_ids = set().union(*(_active_links_by_obj.pop(obj_id, set()) for obj_id in object_ids))
    for link_id in link_ids:
        link = active_links.pop(link_id, None)
        if link is None:
            continue
        for participant in (link[0], link[2]):
            if id(participant) not in object_ids:  # keep the surviving counterpart's index consistent
                _discard_from_index(_active_links_by_obj, id(participant), link_id)

    refs = set().union(*(_bindings_by_obj.pop(obj_id, set()) for obj_id in object_ids))
    for key, entry_id in refs:
        entries = bindings.get(key)
        if entries is None:
            continue
        entry = entries.pop(entry_id, None)
        if entry is None:
            continue
        for participant in (entry[0], entry[1]):  # keep the surviving counterpart's index consistent
            if id(participant) not in object_ids:
                _discard_from_index(_bindings_by_obj, id(participant), (key, entry_id))
        if not entries:
            del bindings[key]

    for obj in objects:
        for name in _bindable_property_names(type(obj)):
            bindable_properties.pop((id(obj), name), None)


def reset() -> None:
    """Clear all bindings.

    This function is intended for testing purposes only.
    """
    bindings.clear()
    _bindings_by_obj.clear()
    bindable_properties.clear()
    active_links.clear()
    _active_links_by_obj.clear()
    _bindable_property_names_cache.clear()


@dataclass_transform()
def bindable_dataclass(cls: TC | None = None, /, *,
                       bindable_fields: Iterable[str] | None = None,
                       **kwargs: Any) -> type[DataclassInstance] | IdentityFunction:
    """A decorator that transforms a class into a dataclass with bindable fields.

    This decorator extends the functionality of ``dataclasses.dataclass`` by making specified fields bindable.
    If ``bindable_fields`` is provided, only the listed fields are made bindable.
    Otherwise, all fields are made bindable by default.

    *Added in version 2.11.0*

    :param cls: class to be transformed into a dataclass
    :param bindable_fields: optional list of field names to make bindable (defaults to all fields)
    :param kwargs: optional keyword arguments to be forwarded to ``dataclasses.dataclass``.
    Usage of ``slots=True`` and ``frozen=True`` are not supported and will raise a ValueError.

    :return: resulting dataclass type
    """
    if cls is None:
        def wrap(cls_):
            return bindable_dataclass(cls_, bindable_fields=bindable_fields, **kwargs)
        return wrap

    for unsupported_option in ('slots', 'frozen'):
        if kwargs.get(unsupported_option):
            raise ValueError(f'`{unsupported_option}=True` is not supported with bindable_dataclass')

    dataclass: type[DataclassInstance] = dataclasses.dataclass(**kwargs)(cls)
    field_names = {field.name for field in dataclasses.fields(dataclass)}
    if bindable_fields is None:
        bindable_fields = field_names
    for field_name in bindable_fields:
        if field_name not in field_names:
            raise ValueError(f'"{field_name}" is not a dataclass field')
        bindable_property = BindableProperty()
        bindable_property.__set_name__(dataclass, field_name)
        setattr(dataclass, field_name, bindable_property)
    return dataclass


def _make_copyable(cls: type[T]) -> None:
    """Tell the copy module to update the ``bindable_properties`` dictionary when an object is copied."""
    if cls in copyreg.dispatch_table:
        return

    def _pickle_function(obj: T) -> tuple[Callable[..., T], tuple[Any, ...]]:
        reduced = obj.__reduce__()
        assert isinstance(reduced, tuple)
        creator = reduced[0]

        def creator_with_hook(*args, **kwargs) -> T:
            copy = creator(*args, **kwargs)
            for attr_name in dir(obj):
                if (id(obj), (attr_name,)) in bindable_properties:
                    bindable_properties[(id(copy), (attr_name,))] = copy
            return copy
        return (creator_with_hook, *reduced[1:])
    copyreg.pickle(cls, _pickle_function)
