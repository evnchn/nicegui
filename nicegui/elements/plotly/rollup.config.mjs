import nodeResolve from "@rollup/plugin-node-resolve";
import commonjs from "@rollup/plugin-commonjs";
import json from "@rollup/plugin-json";
import replace from "@rollup/plugin-replace";
import terser from "@rollup/plugin-terser";
import css from "rollup-plugin-import-css";
import glslPkg from "rollup-plugin-glsl";
import polyfillNode from "rollup-plugin-polyfill-node";

const glsl = glslPkg.glsl ?? glslPkg;

export default [
  {
    // light bundle, built from plotly.js sources so that its trace list can be chosen freely;
    // those sources are CommonJS and import CSS, GLSL, JSON and Node built-ins,
    // see plotly.js/esbuild-config.js for the plugin set plotly.js itself uses for the same job
    input: "./src/index.mjs",
    output: { file: "./dist/index.js", format: "es", sourcemap: true },
    plugins: [
      replace({ preventAssignment: true, values: { "process.env.NODE_DEBUG": "false" } }),
      css({ inject: true }),
      glsl({ include: "**/*.glsl" }),
      json(),
      nodeResolve({ browser: true, preferBuiltins: false }),
      commonjs({ transformMixedEsModules: true }),
      polyfillNode(), // NOTE: after commonjs, otherwise its injected imports make CommonJS modules look like ES modules
      terser({ mangle: true }),
    ],
  },
  {
    // full bundle, re-packaged from the distribution plotly.js builds and optimizes itself;
    // building it from sources instead costs about 190 kB gzipped
    input: "./src/full.mjs",
    output: { file: "./dist/full.js", format: "es", sourcemap: true },
    plugins: [nodeResolve(), commonjs(), terser({ mangle: true })],
  },
];
