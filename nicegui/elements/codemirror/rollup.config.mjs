import nodeResolve from "@rollup/plugin-node-resolve";
import terser from "@rollup/plugin-terser";

const common = {
  output: { dir: "./dist/", format: "es", sourcemap: true },
  plugins: [nodeResolve(), terser({ mangle: true })],
};

// Two independent build passes share the same dist/ directory but rollup never sees them
// together — keeping `src/index.mjs`'s output byte-identical to upstream (no shared-chunk
// re-shuffling) and confining the CRDT bundle to its own files. yjs core and y-protocols
// are external; the browser resolves them via NiceGUI's shared yjs ESM bundle.
export default [
  { ...common, input: "./src/index.mjs" },
  {
    ...common,
    input: "./src/yjs-binding.mjs",
    external: ["yjs", "y-protocols/awareness"],
  },
];
