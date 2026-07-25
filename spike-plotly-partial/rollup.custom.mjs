import nodeResolve from "@rollup/plugin-node-resolve";
import commonjs from "@rollup/plugin-commonjs";
import terser from "@rollup/plugin-terser";
import fs from "fs";

// minimal CSS handler: inline the stylesheet as an injected <style> (plotly's
// own build does the same via a browserify transform)
const css = () => ({
  name: "css",
  transform(code, id) {
    if (!id.endsWith(".css")) return null;
    const src = fs.readFileSync(id, "utf8");
    return {
      code: `const s=document.createElement("style");s.textContent=${JSON.stringify(src)};document.head.appendChild(s);export default undefined;`,
      map: { mappings: "" },
    };
  },
});

export default {
  input: "./src/index-custom.mjs",
  output: { file: "/tmp/custom-bundle.js", format: "es", sourcemap: false },
  plugins: [css(), nodeResolve({ browser: true, preferBuiltins: false }), commonjs(), terser({ mangle: true })],
};
