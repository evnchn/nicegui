import nodeResolve from "@rollup/plugin-node-resolve";
import terser from "@rollup/plugin-terser";

export default {
  input: "./src/index.js",
  output: {
    file: "./nicegui.js",
    format: "iife",
    name: "NiceGUI",
    sourcemap: false,
    globals: {
      "vue": "Vue",
      "quasar": "Quasar",
      "socket.io": "io"
    }
  },
  external: ["vue", "quasar", "socket.io"],
  plugins: [
    nodeResolve(),
    terser({
      mangle: false,
      compress: {
        defaults: false,
        unused: true,
      },
      format: {
        comments: "some",
        beautify: true,
        indent_level: 2,
      }
    }),
  ],
};
