// Custom partial bundle: plotly core + every SVG-based trace.
// Excluded: gl3d (scatter3d/surface/mesh3d/...), gl2d (scattergl/splom/parcoords),
// geo (scattergeo/choropleth) and map/mapbox traces -- all WebGL and/or heavy deps.
import Plotly from "plotly.js/lib/core";

import bar from "plotly.js/lib/bar";
import box from "plotly.js/lib/box";
import heatmap from "plotly.js/lib/heatmap";
import histogram from "plotly.js/lib/histogram";
import histogram2d from "plotly.js/lib/histogram2d";
import histogram2dcontour from "plotly.js/lib/histogram2dcontour";
import contour from "plotly.js/lib/contour";
import scatterternary from "plotly.js/lib/scatterternary";
import violin from "plotly.js/lib/violin";
import funnel from "plotly.js/lib/funnel";
import waterfall from "plotly.js/lib/waterfall";
import image from "plotly.js/lib/image";
import pie from "plotly.js/lib/pie";
import sunburst from "plotly.js/lib/sunburst";
import treemap from "plotly.js/lib/treemap";
import icicle from "plotly.js/lib/icicle";
import funnelarea from "plotly.js/lib/funnelarea";
import sankey from "plotly.js/lib/sankey";
import indicator from "plotly.js/lib/indicator";
import table from "plotly.js/lib/table";
import carpet from "plotly.js/lib/carpet";
import scattercarpet from "plotly.js/lib/scattercarpet";
import contourcarpet from "plotly.js/lib/contourcarpet";
import ohlc from "plotly.js/lib/ohlc";
import candlestick from "plotly.js/lib/candlestick";
import scatterpolar from "plotly.js/lib/scatterpolar";
import barpolar from "plotly.js/lib/barpolar";
import scattersmith from "plotly.js/lib/scattersmith";
import parcats from "plotly.js/lib/parcats";
import calendars from "plotly.js/lib/calendars";

Plotly.register([
  bar, box, heatmap, histogram, histogram2d, histogram2dcontour, contour,
  scatterternary, violin, funnel, waterfall, image, pie, sunburst, treemap,
  icicle, funnelarea, sankey, indicator, table, carpet, scattercarpet,
  contourcarpet, ohlc, candlestick, scatterpolar, barpolar, scattersmith,
  parcats, calendars,
]);

export { Plotly };
