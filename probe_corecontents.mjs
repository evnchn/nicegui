import * as esbuild from 'esbuild';
import fs from 'node:fs';
import path from 'node:path';
const QSRC = path.resolve('node_modules/quasar/src');
const D = {
  __QUASAR_VERSION__: '"2.18.5"', __QUASAR_SSR__: 'false', __QUASAR_SSR_SERVER__: 'false',
  __QUASAR_SSR_CLIENT__: 'false', __QUASAR_SSR_PWA__: 'false', __Q_META__: 'false',
};
const pluginsSrc = fs.readFileSync(path.join(QSRC, 'plugins.js'), 'utf8');
const pluginFile = {};
for (const m of pluginsSrc.matchAll(/^import\s+(\w+)\s+from\s+'(.+?)'/gm)) pluginFile[m[1]] = path.resolve(QSRC, m[2]);
const LAZY = (process.env.LAZY || 'Dialog,BottomSheet,Loading,LoadingBar').split(',').filter(Boolean);
const eager = Object.keys(pluginFile).filter((n) => !LAZY.includes(n));
const parts = [];
if (!process.env.NO_UTILS) parts.push(`import * as utils from '${QSRC}/utils.js'; window.a=utils`);
if (!process.env.NO_COMPOSABLES) parts.push(`import * as c from '${QSRC}/composables.js'; window.b=c`);
parts.push(`import * as d from '${QSRC}/directives.js'; window.c=d`);
parts.push(`import i from '${QSRC}/install-quasar.js'; window.d=i`);
parts.push(...eager.map((n, k) => `import P${k} from '${pluginFile[n]}'; window.p${k}=P${k}`));
const r = await esbuild.build({
  stdin: { contents: parts.join('\n'), resolveDir: QSRC, sourcefile: 'core.js' },
  bundle: true, format: 'esm', write: false, minify: true, external: ['vue'], define: D,
  legalComments: 'none', metafile: true,
});
const out = Object.values(r.metafile.outputs)[0];
const by = {};
for (const [k, v] of Object.entries(out.inputs)) {
  const rel = k.replace('node_modules/quasar/src/', '');
  const group = rel.startsWith('components/') ? 'COMPONENT:' + rel.split('/')[1]
    : rel.startsWith('utils/') ? 'utils/' + rel.split('/')[1]
      : rel.split('/').slice(0, 2).join('/');
  by[group] = (by[group] || 0) + v.bytesInOutput;
}
console.log('LAZY=' + LAZY.join(',') + ' total raw=' + out.bytes);
for (const [k, v] of Object.entries(by).sort((a, b) => b[1] - a[1]).slice(0, 22)) {
  console.log('  ' + String(v).padStart(7), k);
}
