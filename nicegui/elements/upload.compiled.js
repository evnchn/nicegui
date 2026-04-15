// AUTO-GENERATED from upload.js — DO NOT EDIT
import { normalizeProps as _normalizeProps, guardReactiveProps as _guardReactiveProps, renderSlot as _renderSlot, resolveComponent as _resolveComponent, withCtx as _withCtx, renderList as _renderList, createSlots as _createSlots, openBlock as _openBlock, createBlock as _createBlock } from "vue"

export default {
  render(_ctx, _cache) {
  const _component_q_uploader = _resolveComponent("q-uploader")

  return (_openBlock(), _createBlock(_component_q_uploader, {
    ref: "qRef",
    url: _ctx.computed_url
  }, _createSlots({ _: 2 /* DYNAMIC */ }, [
    _renderList(_ctx.$slots, (_, slot) => {
      return {
        name: slot,
        fn: _withCtx((slotProps) => [
          _renderSlot(_ctx.$slots, slot, _normalizeProps(_guardReactiveProps(slotProps || {})))
        ])
      }
    })
  ]), 1032 /* PROPS, DYNAMIC_SLOTS */, ["url"]))
},
  mounted() {
    setTimeout(() => this.compute_url(), 0); // NOTE: wait for window.path_prefix to be set in app.mounted()
  },
  updated() {
    this.compute_url();
  },
  methods: {
    compute_url() {
      this.computed_url = (this.url.startsWith("/") ? window.path_prefix : "") + this.url;
    },
  },
  props: {
    url: String,
  },
  data: function () {
    return {
      computed_url: this.url,
    };
  },
};
