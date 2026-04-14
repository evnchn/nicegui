// AUTO-GENERATED from image.js — DO NOT EDIT
import { normalizeProps as _normalizeProps, guardReactiveProps as _guardReactiveProps, renderSlot as _renderSlot, resolveComponent as _resolveComponent, withCtx as _withCtx, renderList as _renderList, createSlots as _createSlots, openBlock as _openBlock, createBlock as _createBlock } from "vue"

export default {
  render(_ctx, _cache) {
  const _component_q_img = _resolveComponent("q-img")

  return (_openBlock(), _createBlock(_component_q_img, {
    ref: "qRef",
    src: _ctx.computed_src
  }, _createSlots({ _: 2 /* DYNAMIC */ }, [
    _renderList(_ctx.$slots, (_, slot) => {
      return {
        name: slot,
        fn: _withCtx((slotProps) => [
          _renderSlot(_ctx.$slots, slot, _normalizeProps(_guardReactiveProps(slotProps || {})))
        ])
      }
    })
  ]), 1032 /* PROPS, DYNAMIC_SLOTS */, ["src"]))
},
  props: {
    src: String,
    t: String,
  },
  data: function () {
    return {
      computed_src: undefined,
    };
  },
  mounted() {
    setTimeout(() => this.compute_src(), 0); // NOTE: wait for window.path_prefix to be set in app.mounted()
  },
  updated() {
    this.compute_src();
  },
  methods: {
    compute_src() {
      const suffix = this.t ? (this.src.includes("?") ? "&" : "?") + "_nicegui_t=" + this.t : "";
      this.computed_src = (this.src.startsWith("/") ? window.path_prefix : "") + this.src + suffix;
    },
  },
};
