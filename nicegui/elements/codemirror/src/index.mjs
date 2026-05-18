export * from "codemirror";
export * from "@codemirror/view";
export * from "@codemirror/state";
export * from "@codemirror/commands";
export * from "@codemirror/language";
export * from "@codemirror/language-data";
export * from "@codemirror/theme-one-dark";
export * as themes from "@uiw/codemirror-themes-all";

// CRDT layer — opt-in via `ui.codemirror(...).with_crdt(doc_id)`.
// Re-exported under explicit names so the Vue wrapper doesn't have to guess at
// internal y-codemirror.next module layout.
export { yCollab } from "y-codemirror.next";
export { Doc as YjsDoc, applyUpdate as applyYjsUpdate } from "yjs";
export {
  Awareness as YAwareness,
  applyAwarenessUpdate,
  encodeAwarenessUpdate,
  removeAwarenessStates,
} from "y-protocols/awareness";
