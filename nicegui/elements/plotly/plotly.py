from __future__ import annotations

from contextlib import suppress

from ... import optional_features
from ...awaitable_response import AwaitableResponse
from ...element import Element

with suppress(ImportError):
    import plotly.graph_objects as go
    optional_features.register('plotly')

LIGHT_TRACE_TYPES = {  # trace types registered in dist/index.js, see src/index.mjs
    'bar', 'box', 'contour', 'heatmap', 'histogram', 'histogram2d', 'histogram2dcontour',
    'image', 'indicator', 'pie', 'scatter', 'table', 'violin',
}


class Plotly(Element, component='plotly.js', esm={'nicegui-plotly': 'dist'}):

    def __init__(self, figure: dict | go.Figure) -> None:
        """Plotly Element

        Renders a Plotly chart.
        There are two ways to pass a Plotly figure for rendering, see parameter `figure`:

        * Pass a `go.Figure` object, see https://plotly.com/python/

        * Pass a Python `dict` object with keys `data`, `layout`, `config` (optional), see https://plotly.com/javascript/

        For best performance, use the declarative `dict` approach for creating a Plotly chart.

        Figures using only common trace types load a light plotly.js bundle roughly a third the size of the full one.
        The full bundle is fetched instead as soon as a figure needs a trace type the light bundle does not contain.

        :param figure: Plotly figure to be rendered. Can be either a `go.Figure` instance, or
                       a `dict` object with keys `data`, `layout`, `config` (optional).
        """
        super().__init__()

        self.figure = figure
        self.update()
        self._classes.append('js-plotly-plot')
        self._update_method = 'update'

    def update_figure(self, figure: dict | go.Figure):
        """Overrides figure instance of this Plotly chart and updates chart on client side."""
        self.figure = figure
        self.update()

    def run_plot_method(self, name: str, *args, timeout: float = 1) -> AwaitableResponse:
        """Run a plotly.js library function against the chart's HTML element.

        See the `plotly.js function reference <https://plotly.com/javascript/plotlyjs-function-reference/>`_ for a list of methods.
        The chart's HTML element is passed as the first argument automatically.

        If the function is awaited, the result of the method call is returned
        (unless it resolves to the chart's HTML element, in which case ``None`` is returned).
        Otherwise, the method is executed without waiting for a response.

        *Added in version 3.13.0*

        :param name: name of the plotly.js function (without the ``Plotly.`` prefix)
        :param args: arguments to pass after the chart element
        :param timeout: timeout in seconds (default: 1 second)

        :return: AwaitableResponse that can be awaited to get the result of the method call
        """
        return self.run_method('run_plot_method', name, *args, timeout=timeout)

    def update(self) -> None:
        with self._props.suspend_updates():
            self._props['options'] = self._get_figure_json()
            if not self._props.get('full'):  # NOTE: never switch back, the client has loaded the full bundle already
                self._props['full'] = self._needs_full_bundle()
        super().update()

    def _needs_full_bundle(self) -> bool:
        options = self._props['options']
        try:
            traces = [*(options.get('data') or []),
                      *(trace for frame in options.get('frames') or [] for trace in frame.get('data') or [])]
        except (AttributeError, TypeError):
            return True  # an unexpected figure shape is not worth guessing about
        for trace in traces:
            try:
                trace_type = trace['type'] or 'scatter'
            except (KeyError, TypeError):
                trace_type = 'scatter'
            if trace_type not in LIGHT_TRACE_TYPES:
                return True
        return False

    def _get_figure_json(self) -> dict:
        if optional_features.has('plotly') and isinstance(self.figure, go.Figure):
            # convert go.Figure to dict object which is directly JSON serializable
            # orjson supports NumPy array serialization
            return self.figure.to_plotly_json()

        if isinstance(self.figure, dict):
            # already a dict object with keys: data, layout, config (optional)
            return self.figure

        raise ValueError(f'Plotly figure is of unknown type "{self.figure.__class__.__name__}".')
