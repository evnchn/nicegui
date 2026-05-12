import abc
from typing import Any

from .. import json, observables


class PersistentDict(observables.ObservableDict, abc.ABC):

    @abc.abstractmethod
    async def initialize(self) -> None:
        """Load initial data from the persistence layer."""

    @abc.abstractmethod
    def initialize_sync(self) -> None:
        """Load initial data from the persistence layer in a synchronous context."""

    async def close(self) -> None:
        """Clean up the persistence layer."""

    def _validate(self, value: Any) -> None:
        """Reject ``value`` if it cannot be JSON-serialized for persistence.

        The check runs at insert time, so the traceback points at the line that wrote the
        bad value rather than at the deferred backup task. The cost is bounded by the size
        of ``value`` (the upserted content), not the size of the full storage.

        Most stored values are str-keyed dicts of primitives, which the walker confirms in
        pure-Python isinstance checks without invoking the JSON encoder. Only nodes that
        are not in the known-good set (e.g. ``datetime``, ``UUID``, NumPy arrays, custom
        classes covered by ``_orjson_converter``) are individually passed to
        ``json.dumps`` — so the steady-state hot path on ``app.storage.user["counter"] += 1``
        does no JSON work.
        """
        _check(value)


_KNOWN_BAD_LEAF: tuple[type, ...] = (set, frozenset, bytes, bytearray)


def _check(value: Any) -> None:
    if isinstance(value, _KNOWN_BAD_LEAF):
        if isinstance(value, (set, frozenset)):
            type_name = 'frozenset' if isinstance(value, frozenset) else 'set'
            hint = 'JSON has no set type'
        else:
            type_name = 'bytearray' if isinstance(value, bytearray) else 'bytes'
            hint = 'JSON has no bytes type; encode as str first'
        raise TypeError(f"cannot store value of type '{type_name}' in persistent storage ({hint})")
    if isinstance(value, json.KNOWN_GOOD_LEAF):
        return
    if isinstance(value, dict):
        if all(isinstance(k, json.KNOWN_GOOD_KEY) for k in value):
            for v in value.values():
                _check(v)
            return
        # keys outside the wrapper's known-good set (e.g. ``datetime``, ``UUID``, ``tuple``):
        # defer to the encoder for the whole dict — one encoder call per such mutation, an
        # acceptable trade-off vs. re-implementing per-wrapper key-acceptance rules
    elif isinstance(value, (list, tuple)):
        for item in value:
            _check(item)
        return
    try:
        json.dumps(value)
    except (TypeError, ValueError) as e:
        raise TypeError(f'cannot store value in persistent storage: {e}') from e
