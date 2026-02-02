import * as esbuild from 'esbuild';
import * as fs from 'fs';

const isWatch = process.argv.includes('--watch');

const config = {
  entryPoints: ['./src/index.js'],
  bundle: true,
  outfile: './nicegui.js',
  format: 'iife',
  globalName: 'NiceGUI',
  external: ['vue', 'quasar', 'socket.io'],
  // Map external modules to their global variables
  banner: {
    js: `/* NiceGUI Client Bundle - Built with esbuild */`,
  },
  footer: {
    js: `
// Flatten exports to window for backwards compatibility
if (typeof window !== "undefined") {
  const exports = NiceGUI;
  window.True = exports.True;
  window.False = exports.False;
  window.None = exports.None;
  window.getElement = exports.getElement;
  window.getHtmlElement = exports.getHtmlElement;
  window.runMethod = exports.runMethod;
  window.getComputedProp = exports.getComputedProp;
  window.emitEvent = exports.emitEvent;
  window.logAndEmit = exports.logAndEmit;
  window.runJavascript = exports.runJavascript;
  window.download = exports.download;
  window.ack = exports.ack;
  window.parseElements = exports.parseElements;
  window.createApp = exports.createApp;
  window.applyColors = exports.applyColors;
  window.TAB_ID = exports.TAB_ID;
  window.OLD_TAB_ID = exports.OLD_TAB_ID;

  // Expose app and mounted_app via getters
  Object.defineProperty(window, "mounted_app", {
    get: exports.getMountedApp,
    enumerable: true,
    configurable: true
  });

  Object.defineProperty(window, "app", {
    get: exports.getApp,
    enumerable: true,
    configurable: true
  });
}
`,
  },
  minify: false,
  keepNames: true,
  sourcemap: false,
};

if (isWatch) {
  const context = await esbuild.context(config);
  await context.watch();
  console.log('Watching for changes...');
} else {
  await esbuild.build(config);
  // Add trailing newline for pre-commit hook
  const content = fs.readFileSync('./nicegui.js', 'utf8');
  if (!content.endsWith('\n')) {
    fs.appendFileSync('./nicegui.js', '\n');
  }
  console.log('Build complete!');
}
