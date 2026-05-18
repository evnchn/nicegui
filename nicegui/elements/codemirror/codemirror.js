import * as CM from "nicegui-codemirror";
import { yCollab } from "nicegui-codemirror/yjs-binding.js";
import * as Y from "yjs";
import { Awareness, applyAwarenessUpdate, encodeAwarenessUpdate } from "y-protocols/awareness";

// Origin tag for Yjs updates applied locally from a remote source; used to suppress
// the echo back to the server which would otherwise cause an infinite update storm.
const YJS_REMOTE = "yjs-remote";

export default {
  template: `
    <div></div>
  `,
  props: {
    value: String,
    language: String,
    theme: String,
    lineWrapping: Boolean,
    disable: Boolean,
    indent: String,
    highlightWhitespace: Boolean,
    crdtDocId: { type: String, default: null },
    id: String,
  },
  watch: {
    language(newLanguage) {
      this.setLanguage(newLanguage);
    },
    theme(newTheme) {
      this.setTheme(newTheme);
    },
    disable(newDisable) {
      this.setDisabled(newDisable);
    },
    lineWrapping(newLineWrapping) {
      this.setLineWrapping(newLineWrapping);
    },
  },
  data() {
    return {
      // To let other methods wait for the editor to be created because
      // they might be called by the server before the editor is created.
      editorPromise: new Promise((resolve) => {
        this.resolveEditor = resolve;
      }),
    };
  },
  beforeUnmount() {
    if (this.crdtDocId) {
      this._teardownCrdt();
      return;
    }
    if (this.editor) {
      const element = mounted_app.elements[this.$props.id.slice(1)];
      if (element) element.props.value = this.editor.state.doc.toString();
    }
  },
  methods: {
    // Find the language's extension by its name. Case insensitive.
    findLanguage(name) {
      for (const language of this.languages)
        for (const alias of [language.name, ...language.alias])
          if (name.toLowerCase() === alias.toLowerCase()) return language;

      console.error(`Language not found: ${name}`);
      console.info("Supported language names:", this.languages.map((lang) => lang.name).join(", "));
      return null;
    },
    // Get the names of all supported languages
    async getLanguages() {
      if (!this.editor) await this.editorPromise;
      // Over 100 supported languages: https://github.com/codemirror/language-data/blob/main/src/language-data.ts
      return this.languages.map((lang) => lang.name).sort(Intl.Collator("en").compare);
    },
    setLanguage(language) {
      if (!language) {
        this.editor.dispatch({
          effects: this.languageConfig.reconfigure([]),
        });
        return;
      }

      const lang_description = this.findLanguage(language);
      if (!lang_description) {
        return;
      }

      lang_description.load().then((extension) => {
        this.editor.dispatch({
          effects: this.languageConfig.reconfigure([extension]),
        });
      });
    },
    async getThemes() {
      if (!this.editor) await this.editorPromise;
      // `this.themes` also contains some non-theme objects
      // The real themes are Arrays
      return Object.keys(this.themes)
        .filter((key) => Array.isArray(this.themes[key]))
        .sort(Intl.Collator("en").compare);
    },
    setTheme(theme) {
      const new_theme = this.themes[theme];
      if (new_theme === undefined) {
        console.error("Theme not found:", theme);
        return;
      }
      this.editor.dispatch({
        effects: this.themeConfig.reconfigure([new_theme]),
      });
    },
    setEditorValueFromProps() {
      // When collaboration is on, Yjs owns the document state; the `value` prop is no
      // longer the source of truth.
      if (this.crdtDocId) return;
      this.setEditorValue(this.value);
    },
    setEditorValue(value) {
      if (!this.editor) return;
      const old = this.editor.state.doc.toString();
      if (old === value) return;

      // Find the changed region so we only replace what differs.
      // This preserves cursor positions and selections outside the change.
      let start = 0;
      while (start < old.length && start < value.length && old[start] === value[start]) start++;
      let oldEnd = old.length;
      let newEnd = value.length;
      while (oldEnd > start && newEnd > start && old[oldEnd - 1] === value[newEnd - 1]) {
        oldEnd--;
        newEnd--;
      }

      this.emitting = false;
      this.editor.dispatch({ changes: { from: start, to: oldEnd, insert: value.slice(start, newEnd) } });
      this.emitting = true;
    },
    setDisabled(disabled) {
      this.editor.dispatch({
        effects: this.editableConfig.reconfigure(this.editableStates[!disabled]),
      });
    },
    setLineWrapping(wrap) {
      this.editor.dispatch({
        effects: this.lineWrappingConfig.reconfigure(wrap ? [CM.EditorView.lineWrapping] : []),
      });
    },
    setupExtensions() {
      const self = this;

      // Sends a ChangeSet https://codemirror.net/docs/ref/#state.ChangeSet
      // containing only the changes made to the document.
      // This could potentially be optimized further by sending updates
      // periodically instead of on every change and accumulating changesets
      // with ChangeSet.compose.
      const changeSender = CM.ViewPlugin.fromClass(
        class {
          update(update) {
            if (!update.docChanged) return;
            if (!self.emitting) return;
            self.$emit("update:value", update.changes);
          }
        },
      );

      const extensions = [
        CM.basicSetup,
        // In CRDT mode yjs owns the doc and emits via its own update channel; skip changeSender.
        ...(this.crdtDocId ? [yCollab(this.ytext, this.awareness)] : [changeSender]),
        // Enables the Tab key to indent the current lines https://codemirror.net/examples/tab/
        CM.keymap.of([CM.indentWithTab]),
        // Sets indentation https://codemirror.net/docs/ref/#language.indentUnit
        CM.indentUnit.of(this.indent),
        // We will set these Compartments later and dynamically through props
        this.themeConfig.of([]),
        this.languageConfig.of([]),
        this.editableConfig.of([]),
        this.lineWrappingConfig.of([]),
        CM.EditorView.theme({
          "&": { height: "100%" },
          ".cm-scroller": { overflow: "auto" },
        }),
      ];

      if (this.highlightWhitespace) extensions.push([CM.highlightWhitespace()]);

      return extensions;
    },
    _setupCrdt() {
      this.ydoc = new Y.Doc();
      this.ytext = this.ydoc.getText("codemirror");
      this.awareness = new Awareness(this.ydoc);

      const docId = this.crdtDocId;

      this._onYjsInit = (data) => {
        if (data.doc_id !== docId) return;
        const update = new Uint8Array(data.update);
        if (update.length === 0) return;
        Y.applyUpdate(this.ydoc, update, YJS_REMOTE);
      };
      this._onYjsUpdate = (data) => {
        if (data.doc_id !== docId) return;
        Y.applyUpdate(this.ydoc, new Uint8Array(data.update), YJS_REMOTE);
      };
      this._onYjsAwareness = (data) => {
        if (data.doc_id !== docId) return;
        applyAwarenessUpdate(this.awareness, new Uint8Array(data.update), YJS_REMOTE);
      };

      window.socket.on("yjs_init", this._onYjsInit);
      window.socket.on("yjs_update", this._onYjsUpdate);
      window.socket.on("yjs_awareness", this._onYjsAwareness);

      this._ydocUpdateHandler = (update, origin) => {
        if (origin === YJS_REMOTE) return;
        window.socket.emit("yjs_update", { doc_id: docId, update });
      };
      this.ydoc.on("update", this._ydocUpdateHandler);

      this._awarenessUpdateHandler = ({ added, updated, removed }, origin) => {
        if (origin === YJS_REMOTE) return;
        const update = encodeAwarenessUpdate(this.awareness, added.concat(updated, removed));
        window.socket.emit("yjs_awareness", { doc_id: docId, update });
      };
      this.awareness.on("update", this._awarenessUpdateHandler);

      window.socket.emit("yjs_join", { doc_id: docId });
    },
    _teardownCrdt() {
      if (!this.ydoc) return;
      window.socket.emit("yjs_leave", { doc_id: this.crdtDocId });
      window.socket.off("yjs_init", this._onYjsInit);
      window.socket.off("yjs_update", this._onYjsUpdate);
      window.socket.off("yjs_awareness", this._onYjsAwareness);
      this.ydoc.off("update", this._ydocUpdateHandler);
      this.awareness.off("update", this._awarenessUpdateHandler);
      this.awareness.destroy();
      this.ydoc.destroy();
    },
  },
  async mounted() {
    // This is used to prevent emitting the value we just received from the server.
    this.emitting = true;

    // The Compartments are used to change the properties of the editor ("extensions") dynamically
    this.themes = { ...CM.themes, oneDark: CM.oneDark };
    this.themeConfig = new CM.Compartment();
    this.languages = CM.languages;
    this.languageConfig = new CM.Compartment();
    this.editableConfig = new CM.Compartment();
    this.editableStates = { true: CM.EditorView.editable.of(true), false: CM.EditorView.editable.of(false) };
    this.lineWrappingConfig = new CM.Compartment();

    if (this.crdtDocId) this._setupCrdt();

    const extensions = this.setupExtensions();

    this.editor = new CM.EditorView({
      // In CRDT mode the y-codemirror binding seeds the editor from ytext on its own.
      doc: this.crdtDocId ? this.ytext.toString() : this.value,
      extensions: extensions,
      parent: this.$el,
    });

    this.resolveEditor(this.editor);

    this.setLanguage(this.language);
    this.setTheme(this.theme);
    this.setDisabled(this.disable);
    this.setLineWrapping(this.lineWrapping);
  },
};
