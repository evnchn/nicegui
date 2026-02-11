import { renderSlot as _renderSlot, openBlock as _openBlock, createElementBlock as _createElementBlock } from "vue"

const _hoisted_1 = ["href", "target"]

export default {
  render(_ctx, _cache) {
  return (_openBlock(), _createElementBlock("a", {
    href: _ctx.computed_href,
    target: _ctx.target
  }, [
    _renderSlot(_ctx.$slots, "default")
  ], 8 /* PROPS */, _hoisted_1))
},
  mounted() {
    setTimeout(this.compute_href, 0); // NOTE: wait for window.path_prefix to be set in app.mounted()
  },
  updated() {
    this.compute_href();
  },
  methods: {
    compute_href() {
      this.computed_href = (this.href.startsWith("/") ? window.path_prefix : "") + this.href;
    },
  },
  props: {
    href: String,
    target: String,
  },
  data: function () {
    return {
      computed_href: this.href,
    };
  },
};
