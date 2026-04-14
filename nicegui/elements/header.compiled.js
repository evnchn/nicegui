// AUTO-GENERATED from header.js — DO NOT EDIT
import { renderSlot as _renderSlot, resolveComponent as _resolveComponent, withCtx as _withCtx, openBlock as _openBlock, createBlock as _createBlock } from "vue"

export default {
  render(_ctx, _cache) {
  const _component_q_header = _resolveComponent("q-header")

  return (_openBlock(), _createBlock(_component_q_header, { ref: "qRef" }, {
    default: _withCtx(() => [
      _renderSlot(_ctx.$slots, "default")
    ]),
    _: 3 /* FORWARDED */
  }, 512 /* NEED_PATCH */))
},
  mounted() {
    if (this.addScrollPadding) {
      this.resizeObserver = new ResizeObserver(() => {
        document.documentElement.style.scrollPaddingTop = `${this.$el.offsetHeight}px`;
      });
      this.resizeObserver.observe(this.$el);
    }
  },
  unmounted() {
    this.resizeObserver?.disconnect();
  },
  props: {
    addScrollPadding: Boolean,
  },
};
