from __future__ import annotations

from pathlib import Path
from typing import Any

from typing_extensions import Self

from ...element import Element
from ...events import DashboardChangeEventArguments, GenericEventArguments, Handler, handle_event


class Dashboard(Element, component='dashboard.js', esm={'nicegui-dashboard': 'dist'}, default_classes='nicegui-dashboard'):

    def __init__(self, *,
                 columns: int = 12,
                 cell_height: int | str = 80,
                 margin: int | str = 8,
                 float: bool = False,  # pylint: disable=redefined-builtin
                 editable: bool = True,
                 animate: bool = True,
                 options: dict[str, Any] | None = None,
                 on_change: Handler[DashboardChangeEventArguments] | None = None,
                 ) -> None:
        """Dashboard

        A grid of draggable and resizable tiles based on `GridStack <https://gridstackjs.com/>`_.
        Add tiles with ``ui.dashboard_item`` and fill them with any other elements.
        When the user moves or resizes a tile, its ``x``, ``y``, ``w`` and ``h`` are updated on the server.

        *Added in version 3.x.0*

        :param columns: number of grid columns (default: 12)
        :param cell_height: height of one grid row in pixels or as CSS length (default: 80)
        :param margin: gap between tiles in pixels or as CSS length (default: 8)
        :param float: whether tiles may float upwards to leave empty space (default: ``False``)
        :param editable: whether tiles can be moved and resized by the user (default: ``True``)
        :param animate: whether to animate layout changes (default: ``True``)
        :param options: dictionary of raw GridStack options (overrides named parameters if both are given)
        :param on_change: callback invoked when the user moves or resizes tiles
        """
        super().__init__()
        self._props['options'] = {
            'column': columns,
            'cellHeight': cell_height,
            'margin': margin,
            'float': float,
            'staticGrid': not editable,
            'animate': animate,
            **(options or {}),
        }
        self.add_resource(Path(__file__).parent / 'dist')
        self._change_handlers: list[Handler[DashboardChangeEventArguments]] = []
        self.on('layout_change', self._handle_change)
        if on_change:
            self.on_change(on_change)

    def on_change(self, callback: Handler[DashboardChangeEventArguments]) -> Self:
        """Add a callback to be invoked when the user moves or resizes tiles."""
        self._change_handlers.append(callback)
        return self

    def _handle_change(self, e: GenericEventArguments) -> None:
        items: list[Element] = []
        for entry in e.args:
            item = self.client.elements.get(entry['id'])
            if not isinstance(item, DashboardItem):
                continue
            item.props['options'].update({key: entry[key] for key in ('x', 'y', 'w', 'h')})
            items.append(item)
        for handler in self._change_handlers:
            handle_event(handler, DashboardChangeEventArguments(sender=self, client=self.client, items=items))

    @property
    def editable(self) -> bool:
        """Whether tiles can be moved and resized by the user."""
        return not self._props['options'].get('staticGrid', False)

    @editable.setter
    def editable(self, value: bool) -> None:
        self._props['options']['staticGrid'] = not value

    @property
    def layout(self) -> list[dict[str, int]]:
        """The current position and size of all tiles."""
        return [item.geometry for item in self.default_slot.children if isinstance(item, DashboardItem)]


class DashboardItem(Element, component='dashboard_item.js'):

    def __init__(self, *,
                 x: int | None = None,
                 y: int | None = None,
                 w: int = 1,
                 h: int = 1,
                 min_w: int | None = None,
                 max_w: int | None = None,
                 min_h: int | None = None,
                 max_h: int | None = None,
                 movable: bool = True,
                 resizable: bool = True,
                 ) -> None:
        """Dashboard Item

        A tile inside a ``ui.dashboard``.

        *Added in version 3.x.0*

        :param x: column of the left edge (default: ``None``, placed automatically)
        :param y: row of the top edge (default: ``None``, placed automatically)
        :param w: width in columns (default: 1)
        :param h: height in rows (default: 1)
        :param min_w: minimum width in columns
        :param max_w: maximum width in columns
        :param min_h: minimum height in rows
        :param max_h: maximum height in rows
        :param movable: whether the user can move this tile (default: ``True``)
        :param resizable: whether the user can resize this tile (default: ``True``)
        """
        super().__init__()
        self._props['options'] = {
            'x': x, 'y': y, 'w': w, 'h': h,
            'minW': min_w, 'maxW': max_w, 'minH': min_h, 'maxH': max_h,
            'noMove': not movable, 'noResize': not resizable,
            'autoPosition': x is None or y is None,
        }

    @property
    def geometry(self) -> dict[str, int]:
        """The position and size of this tile as a dictionary with keys ``x``, ``y``, ``w`` and ``h``."""
        return {key: self._props['options'][key] for key in ('x', 'y', 'w', 'h')}

    def _option(self, key: str) -> Any:
        return self._props['options'][key]

    @property
    def x(self) -> int | None:
        """Column of the left edge."""
        return self._option('x')

    @x.setter
    def x(self, value: int) -> None:
        self._props['options'].update(x=value, autoPosition=False)

    @property
    def y(self) -> int | None:
        """Row of the top edge."""
        return self._option('y')

    @y.setter
    def y(self, value: int) -> None:
        self._props['options'].update(y=value, autoPosition=False)

    @property
    def w(self) -> int:
        """Width in columns."""
        return self._option('w')

    @w.setter
    def w(self, value: int) -> None:
        self._props['options']['w'] = value

    @property
    def h(self) -> int:
        """Height in rows."""
        return self._option('h')

    @h.setter
    def h(self, value: int) -> None:
        self._props['options']['h'] = value
