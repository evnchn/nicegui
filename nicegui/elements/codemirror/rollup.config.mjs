import nodeResolve from "@rollup/plugin-node-resolve";
import terser from "@rollup/plugin-terser";

const main = {
  input: "./src/index.mjs",
  output: {
    dir: "./dist/",
    format: "es",
    sourcemap: true,
  },
  plugins: [
    nodeResolve(),
    terser({
      mangle: true,
    }),
  ],
};

// Separate pass for the CRDT binding so it doesn't perturb the main bundle's chunking.
export default [main, { ...main, input: "./src/yjs-binding.mjs", external: ["yjs"] }];
