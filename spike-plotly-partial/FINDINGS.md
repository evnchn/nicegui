# Spike: partial plotly.js dist for NiceGUI

All numbers below came from commands actually run in this worktree (plotly.js 3.1.1,
node v22.20.0, rollup 4.x, headless chromium via playwright).

## Sizes (measured, `gzip -9`)

| bundle                         | raw       | gzip      | trace types |
| ------------------------------ | --------- | --------- | ----------- |
| current (`plotly.min.js`)      | 4,581,324 | 1,349,680 | 49          |
| `plotly-cartesian.min.js`      | 1,350,414 | 438,491   | 12          |
| custom SVG-only (lib/core+reg) | 1,806,859 | 589,292   | 30 (BROKEN) |

Cartesian saves 911,189 B gzipped (-67.5%). Reproduce: point
`nicegui/elements/plotly/src/index.mjs` at `plotly.js/dist/plotly-cartesian.min.js`
and `npm run build`.

## The blocker: silent, invisible, WRONG rendering

`Plotly.newPlot` with an unregistered trace type does NOT throw and does NOT log
anything at the default config (`logging: 1`). The trace `type` is silently
coerced to `scatter`:

- `scatter3d` -> `_fullData[0].type === "scatter"`, no error, no console output,
  and the x/y are drawn as a **flat 2D scatter**. The user gets a plausible-looking
  but wrong chart, not a blank one.
- `surface`, `scattermapbox`, `choropleth` -> coerced to `scatter`, 0 trace nodes,
  blank plot area, console completely empty.
- Only at `Plotly.setPlotConfig({logging: 2})` does it emit
  `LOG: Unrecognized trace type scatter3d.`

## Cartesian drops far more than "3D and maps"

Registered in the cartesian bundle (12): bar, box, contour, heatmap, histogram,
histogram2d, histogram2dcontour, image, pie, scatter, scatterternary, violin.

Dropped (37) include ordinary dashboard traces, not exotica:
**indicator, table, sunburst, treemap, icicle, sankey, funnel, waterfall,
candlestick, ohlc, scatterpolar, barpolar, parcoords, splom, scattergl, carpet.**

## Detection is possible

`Plotly.validate(data, layout)` returns structured errors against the *registered*
schema, e.g. `In data trace 0, key type is set to an invalid value (scatter3d)`.
`Object.keys(Plotly.PlotSchema.get().traces)` yields the registry. So plotly.js
could warn in `plotly.js`'s `update()` before `newPlot`.

## Why the custom "everything except WebGL" bundle failed

Building from `plotly.js/lib/*` (rather than a prebuilt dist) needs build config
NiceGUI does not have:

1. `lib/core` imports `maplibre-gl/dist/maplibre-gl.css` -> rollup has no CSS plugin.
2. Even with a CSS shim, the output keeps bare Node builtin imports
   (`stream`, `assert`, `buffer/`) -> browser fails with
   `Failed to resolve module specifier "events"`. Needs a node-polyfill plugin.
   `nodeResolve({browser: true, preferBuiltins: false})` was not sufficient.
