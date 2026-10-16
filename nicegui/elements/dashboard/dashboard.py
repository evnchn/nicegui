from __future__ import annotations

from pathlib import Path
from typing import Any

from typing_extensions import Self

from ...element import Element
from ...events import (
    DashboardChangeEventArguments,
    DashboardItemResizeEventArguments,
    GenericEventArguments,
    Handler,
    handle_event,
)

_LIMITS = {'min_w': 'minW', 'max_w': 'maxW', 'min_h': 'minH', 'max_h': 'maxH'}


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
        self.on('layout_sync', self._sync)
        self.on('item_resize', self._handle_item_resize)
        if on_change:
            self.on_change(on_change)

    def on_change(self, callback: Handler[DashboardChangeEventArguments]) -> Self:
        """Add a callback to be invoked when the user moves or resizes tiles."""
        self._change_handlers.append(callback)
        return self

    def _sync(self, e: GenericEventArguments) -> list[Element]:
        items: list[Element] = []
        for entry in e.args:
            item = self.client.elements.get(entry['id'])
            if isinstance(item, DashboardItem):
                item.props['options'].update({key: entry[key] for key in ('x', 'y', 'w', 'h')}, autoPosition=False)
                items.append(item)
        return items

    def _handle_item_resize(self, e: GenericEventArguments) -> None:
        for item in self._sync(e):
            if isinstance(item, DashboardItem):
                item._handle_resize()  # pylint: disable=protected-access

    def _handle_change(self, e: GenericEventArguments) -> None:
        items = self._sync(e)
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
    def layout(self) -> list[dict[str, int | None]]:
        """The current position and size of all tiles (``x`` and ``y`` are ``None`` for auto-placed tiles not yet shown)."""
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
                 on_resize: Handler[DashboardItemResizeEventArguments] | None = None,
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
        :param on_resize: callback invoked when the user changes the width or height of this tile
        """
        super().__init__()
        self._props['options'] = {
            'x': x, 'y': y, 'w': w, 'h': h,
            'minW': None, 'maxW': None, 'minH': None, 'maxH': None,
            'noMove': not movable, 'noResize': not resizable,
            'autoPosition': x is None or y is None,
        }
        self._set_limits(min_w=min_w, max_w=max_w, min_h=min_h, max_h=max_h)
        self._resize_handlers: list[Handler[DashboardItemResizeEventArguments]] = []
        if on_resize:
            self.on_resize(on_resize)

    def on_resize(self, callback: Handler[DashboardItemResizeEventArguments]) -> Self:
        """Add a callback to be invoked when the user changes the width or height of this tile."""
        self._resize_handlers.append(callback)
        return self

    def _handle_resize(self) -> None:
        for handler in self._resize_handlers:
            handle_event(handler, DashboardItemResizeEventArguments(
                sender=self, client=self.client, w=self.w, h=self.h))

    def _set_limits(self, **limits: int | None) -> None:
        options = {**self._props['options'], **{_LIMITS[name]: value for name, value in limits.items()}}
        for name, key in _LIMITS.items():
            value = options[key]
            if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 1):
                raise ValueError(f'{name} must be a positive integer or None, got {value!r}')
        for size in ('w', 'h'):
            low, high = options[f'min{size.upper()}'], options[f'max{size.upper()}']
            if low is not None and high is not None and low > high:
                raise ValueError(f'min_{size} ({low}) must not be greater than max_{size} ({high})')
            options[size] = _clamp(options[size], low, high)
        self._props['options'].update(options)
        self._fit_grid()

    def _fit_grid(self) -> None:
        options = self._props['options']
        grid = self.parent_slot.parent._props.get('options', {}) if self.parent_slot else {
        }  # pylint: disable=protected-access
        columns, max_row = grid.get('column'), grid.get('maxRow')
        if isinstance(columns, int) and columns > 0:
            options['w'] = min(options['w'], columns)
            if options['x'] is not None:
                options['x'] = max(0, min(options['x'], columns - options['w']))
        if isinstance(max_row, int) and max_row > 0:
            options['h'] = min(options['h'], max_row)
            if options['y'] is not None:
                options['y'] = max(0, min(options['y'], max_row - options['h']))

    @property
    def geometry(self) -> dict[str, int | None]:
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
        self._fit_grid()

    @property
    def y(self) -> int | None:
        """Row of the top edge."""
        return self._option('y')

    @y.setter
    def y(self, value: int) -> None:
        self._props['options'].update(y=value, autoPosition=False)
        self._fit_grid()

    @property
    def w(self) -> int:
        """Width in columns."""
        return self._option('w')

    @w.setter
    def w(self, value: int) -> None:
        self._props['options']['w'] = _clamp(value, self.min_w, self.max_w)
        self._fit_grid()

    @property
    def h(self) -> int:
        """Height in rows."""
        return self._option('h')

    @h.setter
    def h(self, value: int) -> None:
        self._props['options']['h'] = _clamp(value, self.min_h, self.max_h)
        self._fit_grid()

    @property
    def min_w(self) -> int | None:
        """Minimum width in columns (``None`` for no limit); the current width grows to meet it."""
        return self._option('minW')

    @min_w.setter
    def min_w(self, value: int | None) -> None:
        self._set_limits(min_w=value)

    @property
    def max_w(self) -> int | None:
        """Maximum width in columns (``None`` for no limit); the current width shrinks to meet it."""
        return self._option('maxW')

    @max_w.setter
    def max_w(self, value: int | None) -> None:
        self._set_limits(max_w=value)

    @property
    def min_h(self) -> int | None:
        """Minimum height in rows (``None`` for no limit); the current height grows to meet it."""
        return self._option('minH')

    @min_h.setter
    def min_h(self, value: int | None) -> None:
        self._set_limits(min_h=value)

    @property
    def max_h(self) -> int | None:
        """Maximum height in rows (``None`` for no limit); the current height shrinks to meet it."""
        return self._option('maxH')

    @max_h.setter
    def max_h(self, value: int | None) -> None:
        self._set_limits(max_h=value)


def _clamp(value: int, low: int | None, high: int | None) -> int:
    if high is not None:
        value = min(value, high)
    if low is not None:
        value = max(value, low)
    return value
