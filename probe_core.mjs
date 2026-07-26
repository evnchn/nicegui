import * as esbuild from 'esbuild';
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
const QSRC = path.resolve('node_modules/quasar/src');
const D = {
  __QUASAR_VERSION__: '"2.18.5"', __QUASAR_SSR__: 'false', __QUASAR_SSR_SERVER__: 'false',
  __QUASAR_SSR_CLIENT__: 'false', __QUASAR_SSR_PWA__: 'false', __Q_META__: 'false',
};
async function size(code, label) {
  const r = await esbuild.build({
    stdin: { contents: code, resolveDir: QSRC, sourcefile: 'x.js' },
    bundle: true, format: 'esm', write: false, minify: true, external: ['vue'], define: D, legalComments: 'none',
    metafile: true,
  });
  const out = r.outputFiles[0].contents;
  // top inputs
  const ins = Object.entries(r.metafile.outputs)[0][1].inputs;
  const top = Object.entries(ins).sort((a, b) => b[1].bytesInOutput - a[1].bytesInOutput).slice(0, 6)
    .map(([k, v]) => `${k.replace('node_modules/quasar/src/', '')}:${v.bytesInOutput}`);
  console.log(label.padEnd(34), 'raw=' + out.length, 'br=' + zlib.brotliCompressSync(Buffer.from(out)).length);
  if (process.env.TOP) console.log('   ', top.join(' '));
  return out.length;
}
await size(`import i from './install-quasar.js'; window.x=i`, 'install-quasar only');
await size(`import * as d from './directives.js'; window.x=d`, 'directives');
await size(`import * as u from './utils.js'; window.x=u`, 'utils');
await size(`import * as c from './composables.js'; window.x=c`, 'composables');
await size(`import * as p from './plugins.js'; window.x=p`, 'plugins (all)');
const pl = fs.readFileSync(path.join(QSRC, 'plugins.js'), 'utf8');
for (const m of pl.matchAll(/from '(.+?)'/g)) {
  await size(`import * as p from '${m[1]}'; window.x=p`, '  plugin ' + m[1].split('/')[2]);
}
await size(`import * as u from './utils.js'; import * as c from './composables.js'; import * as d from './directives.js'; import i from './install-quasar.js'; window.x=[u,c,d,i]`, 'core w/o plugins');
