// AUTO-GENERATED from html.js — DO NOT EDIT
import { resolveDynamicComponent as _resolveDynamicComponent, openBlock as _openBlock, createBlock as _createBlock } from "vue"

export default {
  render(_ctx, _cache) {
  return (_openBlock(), _createBlock(_resolveDynamicComponent(_ctx.tag)))
},
  data() {
    return { previousInnerHTML: null };
  },
  mounted() {
    this.renderContent();
  },
  updated() {
    this.renderContent();
  },
  methods: {
    renderContent() {
      if (this.innerHTML === this.previousInnerHTML) return;
      if (this.sanitize) {
        this.$el.setHTML(this.innerHTML);
      } else {
        this.$el.innerHTML = this.innerHTML;
      }
      this.previousInnerHTML = this.innerHTML;
    },
  },
  props: {
    innerHTML: String,
    sanitize: Boolean,
    tag: String,
  },
};
