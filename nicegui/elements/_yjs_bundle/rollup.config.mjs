import nodeResolve from "@rollup/plugin-node-resolve";
import terser from "@rollup/plugin-terser";

// Two independent bundles: yjs core and y-protocols/awareness. Each gets its own
// dist subdirectory so register_esm() can register them at distinct paths
// (register_esm is keyed by path, so a single dist can't carry two ESM aliases).
const common = {
  plugins: [nodeResolve(), terser({ mangle: true })],
  output: { format: "es", sourcemap: true },
};

// `register_esm` expects index.js at the root of the registered path; rename the
// rollup output accordingly so the import-map URL `.../esm/<key>/index.js` resolves.
export default [
  {
    ...common,
    input: "./src/yjs.mjs",
    output: { ...common.output, dir: "./dist/yjs/", entryFileNames: "index.js" },
  },
  {
    ...common,
    input: "./src/y-protocols-awareness.mjs",
    output: { ...common.output, dir: "./dist/y-protocols-awareness/", entryFileNames: "index.js" },
    external: ["yjs"],
  },
];
