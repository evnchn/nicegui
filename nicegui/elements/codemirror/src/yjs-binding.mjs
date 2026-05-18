// Separate entry so the main `index.mjs` stays byte-identical to upstream, which
// keeps codemirror's dist chunks (and their content-hash filenames) untouched.
// Loaded only when an `ui.codemirror(...).with_crdt(...)` instance mounts.
export { yCollab } from "y-codemirror.next";
