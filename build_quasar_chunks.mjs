#!/usr/bin/env node
// Build per-component Quasar chunks from quasar/src (NOT the pre-bundled dist).
//
// Output layout (nicegui/static/quasar/):
//   core.js        - installQuasar + directives + plugins + utils + composables, sets window.Quasar
//   c/QBtn.js      - one entry per Quasar component, default-exports it
//   p/Notify.js    - one entry per lazily-loaded Quasar plugin
//   s/<hash>.js    - shared chunks (esbuild code splitting)
//   manifest.json  - transitive output-file list per component tag / plugin
import * as esbuild from 'esbuild';
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';

const ROOT = path.resolve('.');
const Q = path.join(ROOT, 'node_modules', 'quasar');
const QSRC = path.join(Q, 'src');
const VERSION = JSON.parse(fs.readFileSync(path.join(Q, 'package.json'))).version;
const OUT = path.join(ROOT, 'nicegui', 'static', 'quasar');
const TMP = path.join(ROOT, '.quasar-entries');

// Plugins kept out of the always-loaded core because they drag whole components in.
const LAZY_PLUGINS = process.env.FAT_CORE ? [] : ['Dialog', 'BottomSheet', 'Loading', 'LoadingBar'];

const kebab = (n) => n.replace(/([a-z0-9])([A-Z])/g, '$1-$2').replace(/([A-Z])([A-Z][a-z])/g, '$1-$2').toLowerCase();

// ---- discover component name -> source file -----------------------------
const comps = {};
for (const dir of fs.readdirSync(path.join(QSRC, 'components'))) {
  const idx = path.join(QSRC, 'components', dir, 'index.js');
  if (!fs.existsSync(idx)) continue;
  const src = fs.readFileSync(idx, 'utf8');
  const imported = {};
  for (const m of src.matchAll(/^import\s+(\w+)\s+from\s+'(.+?)'/gm)) {
    imported[m[1]] = path.resolve(path.join(QSRC, 'components', dir), m[2]);
  }
  const em = src.match(/export\s*\{([\s\S]*?)\}/);
  for (const name of (em ? em[1].split(',').map((s) => s.trim()).filter(Boolean) : [])) {
    if (imported[name]) comps[name] = imported[name];
  }
}

// ---- discover plugin name -> source file --------------------------------
const pluginsSrc = fs.readFileSync(path.join(QSRC, 'plugins.js'), 'utf8');
const pluginFile = {};
for (const m of pluginsSrc.matchAll(/^import\s+(\w+)\s+from\s+'(.+?)'/gm)) {
  pluginFile[m[1]] = path.resolve(QSRC, m[2]);
}

// ---- write entry stubs ---------------------------------------------------
fs.rmSync(TMP, { recursive: true, force: true });
fs.mkdirSync(TMP, { recursive: true });
const entryPoints = {};
for (const [name, file] of Object.entries(comps)) {
  const p = path.join(TMP, `${name}.js`);
  fs.writeFileSync(p, `export { default } from ${JSON.stringify(file)}\n`);
  entryPoints[`c/${name}`] = p;
}
for (const name of LAZY_PLUGINS) {
  const p = path.join(TMP, `plugin_${name}.js`);
  fs.writeFileSync(p, `export { default } from ${JSON.stringify(pluginFile[name])}\n`);
  entryPoints[`p/${name}`] = p;
}
const eagerPlugins = Object.keys(pluginFile).filter((n) => !LAZY_PLUGINS.includes(n));
const coreEntry = path.join(TMP, '__core.js');
fs.writeFileSync(coreEntry, `
import installQuasar from ${JSON.stringify(path.join(QSRC, 'install-quasar.js'))}
import * as directives from ${JSON.stringify(path.join(QSRC, 'directives.js'))}
import * as utils from ${JSON.stringify(path.join(QSRC, 'utils.js'))}
import * as composables from ${JSON.stringify(path.join(QSRC, 'composables.js'))}
${eagerPlugins.map((n) => `import ${n} from ${JSON.stringify(pluginFile[n])}`).join('\n')}

const plugins = { ${eagerPlugins.join(', ')} }
const Quasar = {
  version: ${JSON.stringify(VERSION)},
  install (app, opts) { installQuasar(app, { directives, plugins, ...opts }) },
  lang: Lang,
  iconSet: IconSet,
  ...directives,
  ...plugins,
  ...composables,
  ...utils
}
window.Quasar = Quasar
export default Quasar
`);
entryPoints.core = coreEntry;

const result = await esbuild.build({
  entryPoints,
  bundle: true,
  splitting: true,
  format: 'esm',
  outdir: OUT,
  chunkNames: 's/[hash]',
  entryNames: '[dir]/[name]',
  minify: true,
  external: ['vue'],
  metafile: true,
  legalComments: 'none',
  define: {
    __QUASAR_VERSION__: JSON.stringify(VERSION),
    __QUASAR_SSR__: 'false',
    __QUASAR_SSR_SERVER__: 'false',
    __QUASAR_SSR_CLIENT__: 'false',
    __QUASAR_SSR_PWA__: 'false',
    __Q_META__: 'false',
  },
});
fs.rmSync(TMP, { recursive: true, force: true });

// ---- manifest ------------------------------------------------------------
const meta = result.metafile;
const entryOf = {};
for (const [file, o] of Object.entries(meta.outputs)) {
  if (o.entryPoint) entryOf[path.relative(OUT, path.resolve(file)).replace(/\.js$/, '')] = path.resolve(file);
}
function closure(file, seen = new Set()) {
  const rel = path.relative(ROOT, file);
  if (seen.has(file) || !meta.outputs[rel]) return seen;
  seen.add(file);
  for (const i of meta.outputs[rel].imports) {
    if (i.kind === 'import-statement') closure(path.resolve(i.path), seen);
  }
  return seen;
}
const files = (key) => [...closure(entryOf[key])].map((f) => path.relative(OUT, f));
const manifest = { core: files('core'), components: {}, plugins: {} };
for (const name of Object.keys(comps)) manifest.components[kebab(name)] = { entry: `c/${name}.js`, files: files(`c/${name}`) };
for (const name of LAZY_PLUGINS) manifest.plugins[name] = { entry: `p/${name}.js`, files: files(`p/${name}`) };
fs.writeFileSync(path.join(OUT, 'manifest.json'), JSON.stringify(manifest));

// ---- report --------------------------------------------------------------
const abs = (rel) => path.join(OUT, rel);
const cost = (tags, plugins = []) => {
  const s = new Set(manifest.core);
  for (const t of tags) for (const f of manifest.components[t].files) s.add(f);
  for (const p of plugins) for (const f of manifest.plugins[p].files) s.add(f);
  const fl = [...s];
  const raw = fl.reduce((a, f) => a + fs.statSync(abs(f)).size, 0);
  const sep = fl.reduce((a, f) => a + zlib.brotliCompressSync(fs.readFileSync(abs(f))).length, 0);
  const cat = zlib.brotliCompressSync(Buffer.concat(fl.map((f) => fs.readFileSync(abs(f))))).length;
  return `files=${String(fl.length).padStart(3)} raw=${String(raw).padStart(7)} sep-br=${String(sep).padStart(6)} cat-br=${String(cat).padStart(6)}`;
};
console.log('components:', Object.keys(comps).length, ' lazy plugins:', LAZY_PLUGINS.join(',') || '(none)');
console.log('core only               ', cost([]));
console.log('hello world (q-btn)     ', cost(['q-btn']));
const realistic = ['q-btn', 'q-icon', 'q-input', 'q-select', 'q-table', 'q-th', 'q-tr', 'q-td', 'q-card',
  'q-card-section', 'q-dialog', 'q-checkbox', 'q-toggle', 'q-slider', 'q-tabs', 'q-tab', 'q-tab-panels',
  'q-tab-panel', 'q-menu', 'q-list', 'q-item', 'q-item-section', 'q-separator', 'q-spinner', 'q-tooltip',
  'q-badge', 'q-avatar', 'q-drawer', 'q-header', 'q-toolbar', 'q-layout', 'q-page', 'q-page-container'];
console.log('realistic (33 comps)    ', cost(realistic, ['Dialog']));
console.log('EVERYTHING              ', cost(Object.keys(manifest.components), LAZY_PLUGINS));
const umd = path.join(ROOT, 'nicegui', 'static', 'quasar.umd.prod.js');
console.log('baseline quasar.umd.prod.js raw=' + fs.statSync(umd).size,
  'br=' + zlib.brotliCompressSync(fs.readFileSync(umd)).length);
