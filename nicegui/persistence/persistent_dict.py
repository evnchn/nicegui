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
        """
        try:
            json.dumps(value)
        except (TypeError, ValueError) as e:
            raise TypeError(f'cannot store value in persistent storage: {e}') from e
