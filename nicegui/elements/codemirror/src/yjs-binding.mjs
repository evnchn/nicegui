// Separate entry so the main `index.mjs` stays byte-identical to upstream, which
// keeps codemirror's dist chunks (and their content-hash filenames) untouched.
// Loaded only when an `ui.codemirror(...).with_crdt(...)` instance mounts. Inlines
// y-protocols/awareness here (~6 KB) so the browser doesn't need a second bare-name
// resolution for it; yjs core stays external and resolves via the shared bundle.
export { yCollab } from "y-codemirror.next";
export {
  Awareness,
  applyAwarenessUpdate,
  encodeAwarenessUpdate,
} from "y-protocols/awareness";
