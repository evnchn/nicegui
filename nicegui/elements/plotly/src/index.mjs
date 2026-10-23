// Light bundle: scatter (always included in core) plus the trace types most NiceGUI charts use.
// Keep in sync with LIGHT_TRACE_TYPES in plotly.py -- tests/test_plotly.py asserts the two match.
import Plotly from "plotly.js/lib/core";
import bar from "plotly.js/lib/bar";
import box from "plotly.js/lib/box";
import contour from "plotly.js/lib/contour";
import heatmap from "plotly.js/lib/heatmap";
import histogram from "plotly.js/lib/histogram";
import histogram2d from "plotly.js/lib/histogram2d";
import histogram2dcontour from "plotly.js/lib/histogram2dcontour";
import image from "plotly.js/lib/image";
import indicator from "plotly.js/lib/indicator";
import pie from "plotly.js/lib/pie";
import table from "plotly.js/lib/table";
import violin from "plotly.js/lib/violin";
import calendars from "plotly.js/lib/calendars";

Plotly.register([
  bar,
  box,
  contour,
  heatmap,
  histogram,
  histogram2d,
  histogram2dcontour,
  image,
  indicator,
  pie,
  table,
  violin,
  calendars,
]);

export { Plotly };
